import copy
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from critic_agent.resources import (resource_contract, render_resource, validate_resource_spec,
                                    ResourceDockerRunner, build_resource)
from critic_agent.orchestrator import run_resource
from critic_agent.spec import SpecError, OPERATIONS
from critic_agent.cli import main
from critic_agent.feedback import build_feedback
from test_foundation import temporary_directory
from test_revision import client_for, static_ok


BOOKS = {'spec_id': 'books_basic', 'spec_version': '1.0', 'resource': 'books', 'model': 'Book',
         'controller': 'BookController', 'fields': [
             {'name': 'title', 'type': 'string', 'rules': ['required', 'string', 'max:80']},
             {'name': 'pages', 'type': 'integer', 'rules': ['required', 'integer', 'min:1', 'max:5000']}],
         'operations': copy.deepcopy(OPERATIONS)}


class ResourceTemplateTests(unittest.TestCase):
    def test_deterministic_scaffold_and_counts(self):
        contract = resource_contract(BOOKS)
        self.assertEqual(contract['internal_tests'], 12)
        self.assertEqual(resource_contract(BOOKS), contract)
        files = render_resource(BOOKS)
        self.assertEqual(files, render_resource(BOOKS))
        self.assertIn('app/Models/Book.php', files)
        self.assertIn("protected $table = 'books'", files['app/Models/Book.php'])
        self.assertIn('BookController', files['routes/api.php'])
        self.assertIn('app/Http/Controllers/BookController.php', files['runtime.php'])
        self.assertNotIn('ProductController.php', files['runtime.php'])
        self.assertNotIn('ReferenceEvaluation', files['phpunit.xml'])
        self.assertNotIn('evaluation/', '\n'.join(files))

    def test_unique_fixture_values_obey_narrow_bounds(self):
        spec = copy.deepcopy(BOOKS)
        spec['fields'][0]['rules'] = ['required', 'string', 'min:1', 'max:1', 'unique:books,title']
        spec['fields'][1]['rules'] = ['required', 'integer', 'min:-9', 'max:-5', 'unique:books,pages']
        fixtures = resource_contract(spec)['fixtures']
        for field in ('title', 'pages'):
            self.assertEqual(len({body[field] for body in fixtures.values()}), 5)
        self.assertTrue(all(len(body['title']) == 1 and -9 <= body['pages'] <= -5 for body in fixtures.values()))

    def test_unique_integer_one_sided_domains_are_not_artificially_bounded(self):
        for rule in ('min:1000000', 'max:-1000000'):
            spec = copy.deepcopy(BOOKS)
            spec['fields'][1]['rules'] = ['required', 'integer', rule, 'unique:books,pages']
            values = [body['pages'] for body in resource_contract(spec)['fixtures'].values()]
            self.assertEqual(len(set(values)), 5)
            self.assertTrue(all(value >= 1000000 if rule.startswith('min') else value <= -1000000 for value in values))

    def test_unsupported_fixture_domains_rejected(self):
        for rules, index in [(['required', 'string', 'max:0'], 0),
                             (['required', 'string', 'min:257'], 0),
                             (['required', 'integer', 'min:0', 'max:1', 'unique:books,pages'], 1)]:
            spec = copy.deepcopy(BOOKS)
            spec['fields'][index]['rules'] = rules
            with self.assertRaises(SpecError):
                validate_resource_spec(spec)

    def test_reserved_scaffold_names_rejected(self):
        for key, value in [('model', 'Class'), ('controller', 'Controller'), ('resource', 'migrations'),
                           ('resource', 'sqlite_sequence')]:
            with self.assertRaises(SpecError):
                validate_resource_spec(dict(BOOKS, **{key: value}))

    def test_spec_and_template_changes_change_fingerprint(self):
        spec = copy.deepcopy(BOOKS)
        spec['fields'][0]['rules'][-1] = 'max:81'
        self.assertNotEqual(resource_contract(spec)['contract_sha256'], resource_contract(BOOKS)['contract_sha256'])

    @unittest.skipUnless(shutil.which('php'), 'PHP needed for trusted provider enumeration')
    def test_trusted_provider_counts_match_contract(self):
        root = Path(__file__).resolve().parents[1]
        if not (root/'harness/laravel/vendor/autoload.php').exists():
            self.skipTest('Locked harness dependencies not installed')
        for name in ('books', 'inventory_items'):
            spec = json.loads((root/'examples'/(name+'.json')).read_text())
            with temporary_directory() as tmp:
                context = Path(tmp).resolve()
                for filename, source in render_resource(spec).items():
                    path = context/filename
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(source.encode())
                # Only trusted test declarations and pure data providers are loaded.
                script = r'''<?php
require $argv[1];
require $argv[2].'/tests/Support/ResourceFixtures.php';
require $argv[2].'/tests/Feature/ResourceContractTest.php';
require $argv[2].'/tests/Feature/ResourceReadinessTest.php';
$counts = [];
foreach ([Tests\Feature\ResourceContractTest::class, Tests\Feature\ResourceReadinessTest::class] as $name) {
    $class = new ReflectionClass($name); $count = 0;
    foreach ($class->getMethods(ReflectionMethod::IS_PUBLIC) as $method) {
        if (!str_starts_with($method->getName(), 'test_')) continue;
        $providers = $method->getAttributes(PHPUnit\Framework\Attributes\DataProvider::class);
        $count += $providers ? count($class->getMethod($providers[0]->getArguments()[0])->invoke(null)) : 1;
    }
    $counts[] = $count;
}
echo json_encode($counts);
'''
                (context/'enumerate.php').write_text(script)
                result = subprocess.run(['php', str(context/'enumerate.php'), str(root/'harness/laravel/vendor/autoload.php'), str(context)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                contract = resource_contract(spec)
                self.assertEqual(json.loads(result.stdout), [contract['internal_tests'], contract['readiness_tests']])

    @unittest.skipUnless(shutil.which('php'), 'PHP needed to lint generated trusted files')
    def test_every_rendered_php_file_lints_for_two_and_four_fields(self):
        specs = [BOOKS, copy.deepcopy(BOOKS)]
        specs[1]['fields'] += [{'name': 'code', 'type': 'string', 'rules': ['required', 'string', 'unique:books,code']},
                              {'name': 'quantity', 'type': 'integer', 'rules': ['required', 'integer', 'min:0']}]
        self.assertEqual(resource_contract(specs[1])['internal_tests'], 16)
        for spec in specs:
            for name, source in render_resource(spec).items():
                if name.endswith('.php'):
                    with self.subTest(path=name):
                        checked = subprocess.run(['php', '-n', '-l'], input=source.encode(), capture_output=True)
                        self.assertEqual(checked.returncode, 0, checked.stdout+checked.stderr)

    def test_build_archives_context_and_keeps_base_separate(self):
        with temporary_directory() as tmp:
            calls = []
            def execute(args, **kwargs):
                calls.append(args)
                if 'inspect' in args:
                    data = {'Id': 'sha256:'+'a'*64, 'Config': {'Entrypoint': ['php', '/opt/critic-entrypoint.php'], 'Labels': {}}}
                    return subprocess.CompletedProcess(args, 0, json.dumps(data).encode(), b'')
                return subprocess.CompletedProcess(args, 0)
            folder = build_resource(BOOKS, Path(tmp), execute=execute)
            result = json.loads((folder/'build_result.json').read_text())
            self.assertEqual(result['status'], 'BUILT')
            self.assertTrue((folder/'context'/'runtime.php').exists())
            command = next(args for args in calls if 'build' in args)
            self.assertIn('CONTRACT_SHA256='+resource_contract(BOOKS)['contract_sha256'], command)
            self.assertNotIn('HARNESS_IMAGE=critic-laravel:dev', command)
            tag = next(args for args in calls if 'tag' in args)
            self.assertEqual(tag[-2], 'sha256:'+'a'*64)
            self.assertIn('HARNESS_IMAGE='+tag[-1], command)
            self.assertIn(['docker', 'image', 'rm', tag[-1]], calls)
            with self.assertRaises(ValueError):
                build_resource(BOOKS, Path(tmp), image='critic-laravel:dev')

    def test_evaluation_base_alias_is_rejected_before_build(self):
        with temporary_directory() as tmp:
            calls = []
            def execute(args, **kwargs):
                calls.append(args)
                data = {'Id': 'sha256:'+'a'*64, 'Config': {'Entrypoint': ['php', '/opt/critic-evaluation-entrypoint.php'],
                        'Labels': {'org.critic.reference-suite-sha256': 'x'*64}}}
                return subprocess.CompletedProcess(args, 0, json.dumps(data).encode(), b'')
            folder = build_resource(BOOKS, Path(tmp), base_image='alias:dev', execute=execute)
            result = json.loads((folder/'build_result.json').read_text())
            self.assertEqual(result['status'], 'ERROR')
            self.assertFalse(any('build' in args for args in calls))

    def test_build_timeout_applies_to_docker_preparation_and_cleanup(self):
        with temporary_directory() as tmp:
            calls = []
            def execute(args, **kwargs):
                calls.append((args, kwargs['timeout']))
                if 'inspect' in args:
                    data = {'Id': 'sha256:'+'a'*64, 'Config': {'Entrypoint': ['php', '/opt/critic-entrypoint.php'], 'Labels': {}}}
                    return subprocess.CompletedProcess(args, 0, json.dumps(data).encode(), b'')
                if 'tag' in args and kwargs['timeout'] < 20:
                    raise subprocess.TimeoutExpired(args, kwargs['timeout'])
                return subprocess.CompletedProcess(args, 0, b'', b'')
            folder = build_resource(BOOKS, Path(tmp), timeout=45, execute=execute)
            result = json.loads((folder/'build_result.json').read_text())
            self.assertEqual(result['status'], 'BUILT')
            self.assertEqual(result['timeout_seconds'], 45)
            self.assertTrue(all(timeout == 45 for _, timeout in calls))

    def test_tag_timeout_still_cleans_owned_tag_and_preserves_original_failure(self):
        with temporary_directory() as tmp:
            calls = []
            def execute(args, **kwargs):
                calls.append(args)
                if 'inspect' in args:
                    data = {'Id': 'sha256:'+'a'*64, 'Config': {'Entrypoint': ['php', '/opt/critic-entrypoint.php'], 'Labels': {}}}
                    return subprocess.CompletedProcess(args, 0, json.dumps(data).encode(), b'')
                if 'tag' in args:
                    raise subprocess.TimeoutExpired(args, kwargs['timeout'])
                if 'rm' in args:
                    return subprocess.CompletedProcess(args, 1, b'', b'No such image')
                self.fail('Build must not start after tag timeout')
            folder = build_resource(BOOKS, Path(tmp), timeout=45, execute=execute)
            result = json.loads((folder/'build_result.json').read_text())
            self.assertEqual(result['status'], 'ERROR')
            self.assertEqual(result['failed_stage'], 'pin_base')
            self.assertEqual(result['reason'], 'timeout')
            self.assertIn('timed out', result['detail'])
            pin = next(args for args in calls if 'tag' in args)
            self.assertIn(['docker', 'image', 'rm', pin[-1]], calls)
            self.assertEqual(result['base_cleanup_exit_code'], 1)
            self.assertIn('No such image', result['base_cleanup_detail'])

    def test_protected_target_docker_hub_aliases_are_rejected(self):
        for image in ('docker.io/library/critic-laravel:dev', 'library/critic-laravel:dev',
                      'index.docker.io/library/critic-laravel-evaluation:dev'):
            with temporary_directory() as tmp, self.assertRaises(ValueError):
                build_resource(BOOKS, Path(tmp), image=image)


class ResourceRunnerTests(unittest.TestCase):
    def test_bound_spec_counts_modes_and_restricted_mount(self):
        runner = ResourceDockerRunner(BOOKS)
        self.assertEqual(runner.candidate_tests, 12)
        command = runner.command('test', Path('unused'), Path('code.php'))
        self.assertEqual(command[-1], 'resource-candidate')
        self.assertEqual(command.count('--mount'), 1)
        self.assertIn('--network=none', command)
        self.assertEqual(runner.command('test', Path('unused'))[-1], 'resource-reference')

    def test_wrong_image_fingerprint_cannot_be_ready(self):
        with temporary_directory() as tmp:
            raw = {'status': 'READY', 'image_id': 'sha256:'+'a'*64, 'run_directory': tmp}
            execute = lambda *a, **kw: subprocess.CompletedProcess([], 0, b'wrong', b'')
            with patch('critic_agent.sandbox.DockerRunner.check_reference', return_value=raw):
                result = ResourceDockerRunner(BOOKS, execute=execute).check_reference()
            self.assertEqual(result['status'], 'ERROR')
            self.assertEqual(result['reason'], 'contract_mismatch')


class ResourceLoopTests(unittest.TestCase):
    def test_generic_count_and_provenance(self):
        class Runner:
            spec = BOOKS
            candidate_tests = 12
            contract_sha256 = resource_contract(BOOKS)['contract_sha256']
            def check_candidate(self, path):
                return {'status': 'PASSED_INTERNAL', 'image_id': 'sha256:'+'a'*64,
                        'summary': {'total': 12, 'passed': 12, 'failure': 0, 'error': 0, 'skipped': 0}}
        with temporary_directory() as tmp:
            folder = run_resource(BOOKS, Path(tmp), client_for(['<?php\n// trusted test transport\n']), Runner(),
                                  static_analyzer=static_ok)
            result = json.loads((folder/'run_manifest.json').read_text())
            self.assertEqual(result['status'], 'LOLOS')
            self.assertEqual(result['expected_internal_tests'], 12)
            self.assertEqual(result['resource_contract_sha256'], Runner.contract_sha256)

    def test_wrong_runner_spec_rejected_before_model(self):
        with temporary_directory() as tmp, self.assertRaises(ValueError):
            run_resource(BOOKS, Path(tmp), client_for([]), object())

    def test_required_field_feedback_locates_arbitrary_field(self):
        dynamic = {'summary': {'cases': [{'name': 'test_required_field_rejection_preserves_data with data set "store_title"',
                                         'outcome': 'failure', 'evidence': '422 expected'}]}}
        self.assertEqual(build_feedback([], dynamic, 0)['findings'][0]['location'], {'method': 'store'})

    def test_wrong_count_cannot_lolos(self):
        class Runner:
            spec = BOOKS
            contract_sha256 = resource_contract(BOOKS)['contract_sha256']
            candidate_tests = 12
            def check_candidate(self, path):
                return {'status': 'PASSED_INTERNAL', 'image_id': 'sha256:'+'a'*64,
                        'summary': {'total': 14, 'passed': 14, 'failure': 0, 'error': 0, 'skipped': 0}}
        with temporary_directory() as tmp:
            folder = run_resource(BOOKS, Path(tmp), client_for(['<?php\n// fixture\n']), Runner(), static_analyzer=static_ok)
            self.assertEqual(json.loads((folder/'history.json').read_text())['status'], 'ERROR')


class ResourceCliTests(unittest.TestCase):
    def test_resource_commands_help(self):
        for command in ('resource-build', 'resource-check', 'run-resource'):
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as error:
                main([command, '--help'])
            self.assertEqual(error.exception.code, 0)

    def test_resource_readiness_cli_never_calls_model(self):
        with temporary_directory() as tmp:
            path = Path(tmp)/'books.json'
            path.write_text(json.dumps(BOOKS))
            with patch('critic_agent.cli.ResourceDockerRunner') as runner, \
                    patch('critic_agent.cli.OllamaClient') as model, redirect_stdout(io.StringIO()) as output:
                runner.return_value.check_reference.return_value = {'status': 'READY'}
                self.assertEqual(main(['resource-check', str(path)]), 0)
                model.assert_not_called()
                self.assertEqual(json.loads(output.getvalue())['status'], 'READY')
