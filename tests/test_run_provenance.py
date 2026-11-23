import json
from pathlib import Path
import unittest
from urllib.error import URLError

from critic_agent.generation import generate
from critic_agent.ollama import OllamaClient
from critic_agent.orchestrator import run_products
from test_foundation import CODE, SPEC, temporary_directory
from test_revision import CHANGED, FAILED, IMAGE, PASSED, FakeRunner, client_for, static_ok


class ProvenanceTests(unittest.TestCase):
    def test_loop_archives_effective_seed_and_transport_per_revision(self):
        client = client_for([CODE, URLError('temporary outage'), CHANGED])
        with temporary_directory() as tmp:
            folder = run_products(SPEC, Path(tmp), client, FakeRunner([FAILED, PASSED]),
                                  static_analyzer=static_ok)
            manifest = json.loads((folder / 'run_manifest.json').read_bytes())
            attempts = json.loads((folder / 'history.json').read_bytes())['attempts']
            self.assertEqual(manifest['status'], 'LOLOS')
            self.assertEqual(manifest['image_id'], IMAGE)
            self.assertEqual(len(manifest['provenance']['tests']['local_products_suite_sha256']), 64)
            self.assertEqual([entry['model_request']['options']['seed'] for entry in attempts], [42, 42])
            self.assertEqual([len(entry['model_request']['transport_attempts']) for entry in attempts], [1, 2])

    def test_generation_archives_model_snapshot_and_retry_without_changing_response(self):
        response = {'response': CODE, 'done': True}
        requests = []

        def generate_request(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                raise URLError('temporary outage')
            return response

        def metadata_request(request, timeout):
            if request.full_url.endswith('/api/version'):
                return {'version': '0.test'}
            return {'models': [{'name': 'qwen2.5:7b-instruct', 'digest': 'd'*64,
                                'details': {'quantization_level': 'Q4_K_M'}}]}

        client = OllamaClient(transport=generate_request, metadata_transport=metadata_request, seed=43)
        with temporary_directory() as tmp:
            folder = generate(SPEC, Path(tmp), client)
            manifest = json.loads((folder / 'run_manifest.json').read_bytes())
            self.assertEqual(json.loads((folder / 'response.json').read_bytes()), response)
            self.assertEqual(manifest['provenance']['model_identity']['digest'], 'd'*64)
            self.assertEqual(manifest['provenance']['model_identity']['quantization'], 'Q4_K_M')
            self.assertEqual(manifest['provenance']['model_identity']['ollama_version'], '0.test')
            self.assertEqual(len(manifest['provenance']['prototype_source_sha256']), 64)
            self.assertEqual(manifest['model_request']['options']['seed'], 43)
            self.assertEqual([attempt['outcome'] for attempt in manifest['model_request']['transport_attempts']],
                             ['retryable_error', 'ok'])

    def test_transport_exhaustion_still_archives_both_attempts(self):
        def broken(request, timeout):
            raise URLError('offline')

        client = OllamaClient(transport=broken)
        with temporary_directory() as tmp:
            folder = generate(SPEC, Path(tmp), client)
            manifest = json.loads((folder / 'run_manifest.json').read_bytes())
            self.assertEqual(manifest['status'], 'ERROR')
            self.assertEqual(manifest['provenance']['model_identity']['status'], 'unavailable')
            self.assertEqual(len(manifest['model_request']['transport_attempts']), 2)
