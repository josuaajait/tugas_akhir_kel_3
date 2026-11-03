import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import URLError

from critic_agent.spec import validate_spec, SpecError
from critic_agent.prompts import build_prompt
from critic_agent.ollama import OllamaClient, ModelError
from critic_agent.generation import extract_php, ExtractionError, generate


SPEC = {'spec_id': 'products_basic', 'spec_version': '1.0', 'resource': 'products',
        'model': 'Product', 'controller': 'ProductController',
        'fields': [{'name': 'name', 'type': 'string', 'rules': ['required', 'string', 'max:100']},
                   {'name': 'price', 'type': 'integer', 'rules': ['required', 'integer', 'min:0']},
                   {'name': 'sku', 'type': 'string', 'rules': ['required', 'string', 'unique:products,sku']}],
        'operations': {'index': {'success_status': 200},
                       'store': {'success_status': 201, 'validation_error_status': 422},
                       'show': {'success_status': 200, 'not_found_status': 404},
                       'update': {'success_status': 200, 'validation_error_status': 422, 'not_found_status': 404},
                       'destroy': {'success_status': 204, 'not_found_status': 404}}}
CODE = '<?php\nnamespace App\\Http\\Controllers;\nclass ProductController {}\n'


def temporary_directory():
    base = Path(__file__).resolve().parents[1]/'work'
    base.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=base)


class ContractTests(unittest.TestCase):
    def test_product_contract(self):
        self.assertEqual(validate_spec(SPEC), SPEC)

    def test_unsafe_and_unsupported_spec_rejected(self):
        changes = [('controller', '../escape'), ('model', 'Product;exit'),
                   ('resource', 'products/../../'), ('extra', 'ignored')]
        for key, value in changes:
            with self.subTest(key=key), self.assertRaises(SpecError):
                validate_spec({**SPEC, key: value})
        for value in [True, '201', 999, 202]:
            bad = copy.deepcopy(SPEC)
            bad['operations']['store']['success_status'] = value
            with self.subTest(value=value), self.assertRaises(SpecError):
                validate_spec(bad)
        for rule in ['exists:users,id', 'unique:users,email', 'min:no', 'max:-1']:
            bad = copy.deepcopy(SPEC)
            bad['fields'][0]['rules'].append(rule)
            with self.subTest(rule=rule), self.assertRaises(SpecError):
                validate_spec(bad)

    def test_duplicate_field_and_unknown_type(self):
        bad = copy.deepcopy(SPEC)
        bad['fields'].append(bad['fields'][0])
        with self.assertRaises(SpecError):
            validate_spec(bad)
        bad = copy.deepcopy(SPEC)
        bad['fields'][0]['type'] = 'array'
        with self.assertRaises(SpecError):
            validate_spec(bad)

    def test_prompt_has_contract_and_no_reference_tests(self):
        prompt = build_prompt(SPEC)
        for text in ['show($id)', 'update(Request $request, $id)', 'Accept: application/json',
                     'ProductController', 'unique:products,sku', 'data', '204']:
            self.assertIn(text, prompt)
        self.assertNotIn('reference_results', prompt)


class GenerationTests(unittest.TestCase):
    def test_extract_raw_and_fenced(self):
        self.assertEqual(extract_php(CODE), CODE)
        self.assertEqual(extract_php('Controller:\n```php\n'+CODE+'```\nSelesai.'), CODE)
        crlf = CODE.replace('\n', '\r\n')
        self.assertEqual(extract_php('```php\r\n'+crlf+'```\r\n'), crlf)

    def test_bad_or_ambiguous_output_rejected(self):
        for raw in ['hello', '', '```php\n'+CODE+'```\n```php\n'+CODE+'```',
                    '```php\n'+CODE, CODE+'?>extra']:
            with self.subTest(raw=raw[:20]), self.assertRaises(ExtractionError):
                extract_php(raw)

    def test_raw_candidate_outside_fence_is_ambiguous(self):
        with self.assertRaises(ExtractionError):
            extract_php(CODE+'\n```php\n<?php\nclass Other {}\n```\n')

    def test_client_payload(self):
        calls = []
        def transport(request, timeout):
            calls.append((json.loads(request.data), timeout))
            return {'response': CODE, 'done': True, 'model': 'qwen2.5:7b-instruct'}
        client = OllamaClient(transport=transport, temperature=0.2, seed=7, timeout=3)
        self.assertEqual(client.generate('prompt')['response'], CODE)
        data, timeout = calls[0]
        self.assertFalse(data['stream'])
        self.assertEqual(data['options']['seed'], 7)
        self.assertEqual(timeout, 3)

    def test_client_retries_transport_once(self):
        calls = []
        def broken(request, timeout):
            calls.append(1)
            raise URLError('offline')
        with self.assertRaises(ModelError):
            OllamaClient(transport=broken).generate('test')
        self.assertEqual(len(calls), 2)

    def test_incomplete_or_malformed_service_response_is_error(self):
        for result in [{'response': CODE, 'done': False}, [], {'done': True},
                       {'response': CODE, 'done': True, 'done_reason': 'length'}]:
            with self.subTest(result=result), self.assertRaises(ModelError):
                OllamaClient(transport=lambda req, timeout: result).generate('x')

    def test_archive_preserves_raw_and_never_claims_lolos(self):
        with temporary_directory() as temp:
            client = OllamaClient(transport=lambda req, timeout: {'response': CODE, 'done': True})
            folder = generate(SPEC, Path(temp), client)
            other = generate(SPEC, Path(temp), client)
            self.assertNotEqual(folder, other)
            self.assertEqual((folder/'initial_controller.php').read_text(), CODE)
            manifest = json.loads((folder/'run_manifest.json').read_text())
            self.assertEqual(manifest['status'], 'AWAITING_DYNAMIC_TESTS')
            self.assertEqual(manifest['options']['seed'], 42)
            self.assertEqual(manifest['prompt_sha256'], hashlib.sha256((folder/'prompt.txt').read_bytes()).hexdigest())
            self.assertTrue((folder/'response.json').exists())

    def test_format_failure_is_archived(self):
        with temporary_directory() as temp:
            client = OllamaClient(transport=lambda req, timeout: {'response': 'not code', 'done': True})
            folder = generate(SPEC, Path(temp), client)
            result = json.loads((folder/'run_manifest.json').read_text())
            self.assertEqual(result['status'], 'FORMAT_FAIL')
            self.assertFalse((folder/'initial_controller.php').exists())

    def test_model_error_is_archived(self):
        with temporary_directory() as temp:
            def broken(req, timeout):
                raise URLError('offline')
            folder = generate(SPEC, Path(temp), OllamaClient(transport=broken))
            data = json.loads((folder/'run_manifest.json').read_text())
            self.assertEqual(data['status'], 'ERROR')
            self.assertEqual(data['stop_reason'], 'model_error')

    def test_truncated_model_response_is_preserved(self):
        with temporary_directory() as temp:
            result = {'response': CODE, 'done': True, 'done_reason': 'length'}
            client = OllamaClient(transport=lambda req, timeout: result)
            folder = generate(SPEC, Path(temp), client)
            self.assertEqual(json.loads((folder/'response.json').read_text()), result)
            self.assertEqual(json.loads((folder/'run_manifest.json').read_text())['status'], 'ERROR')


if __name__ == '__main__':
    unittest.main()
