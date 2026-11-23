import json
from pathlib import Path
import unittest
from urllib.error import URLError

from test_foundation import SPEC, temporary_directory
from test_revision import CODE, CHANGED, FAILED, PASSED, IMAGE, FakeRunner, static_ok
from critic_agent.ollama import OllamaClient
from critic_agent.reference import reference_suite_hash


class Reference:
    image = IMAGE

    def __init__(self):
        self.calls = []

    def check_reference(self):
        return {'status': 'READY', 'image_id': self.image, 'suite_sha256': reference_suite_hash()}

    def check_candidate(self, path):
        data = path.read_bytes()
        self.calls.append(data)
        failed = b'// revision' not in data
        return {'status': 'FAILED_REFERENCE' if failed else 'PASSED_REFERENCE',
                'image_id': self.image, 'cleanup_exit_code': 0, 'exit_code': 1 if failed else 0,
                'summary': {'total': 33, 'passed': 32 if failed else 33,
                            'failure': int(failed), 'error': 0, 'skipped': 0}}


class AblationTests(unittest.TestCase):
    def test_environment_error_excludes_pair_and_preserves_other_branch_and_reference(self):
        from critic_agent.ab import run_ab

        responses = iter([CODE, URLError('offline'), URLError('offline'), CHANGED])

        def transport(request, timeout):
            response = next(responses)
            if isinstance(response, Exception):
                raise response
            return {'response': response, 'done': True}

        runner = FakeRunner([FAILED, FAILED, PASSED])
        runner.check_reference = lambda: {'status': 'READY', 'image_id': IMAGE}
        with temporary_directory() as temp:
            folder = run_ab(SPEC, Path(temp), OllamaClient(transport=transport), runner, Reference(),
                            kind='products', order_seed=7, revision_seeds=[43], static_analyzer=static_ok)
            report = json.loads((folder/'pair.json').read_bytes())
            first, second = (report['branches'][key] for key in report['order'])
            self.assertEqual(first['status'], 'ERROR')
            self.assertEqual(first['cost']['http_retries_observed'], 1)
            self.assertEqual(second['evaluation']['status'], 'EVALUATED')
            self.assertEqual(report['n_ab'], 0)
            self.assertIsNone(report['delta_final_pp'])

    def test_format_failure_is_shared_and_evaluator_scores_no_code_as_zero(self):
        from critic_agent.ab import run_ab

        responses = iter(['description without a controller', CHANGED, CHANGED])

        def transport(request, timeout):
            return {'response': next(responses), 'done': True}

        runner = FakeRunner([PASSED, PASSED])
        runner.check_reference = lambda: {'status': 'READY', 'image_id': IMAGE}
        reference = Reference()
        with temporary_directory() as temp:
            folder = run_ab(SPEC, Path(temp), OllamaClient(transport=transport), runner, reference,
                            kind='products', order_seed=7, revision_seeds=[43], static_analyzer=static_ok)
            report = json.loads((folder/'pair.json').read_bytes())
            self.assertEqual(report['n_ab'], 1)
            self.assertIsNone(report['initial_code_sha256'])
            self.assertEqual(len(reference.calls), 2)
            for branch in report['branches'].values():
                self.assertEqual(branch['evaluation']['initial_pass_rate'], 0)

    def test_one_initial_seed_schedule_feedback_isolation_and_shared_evaluation(self):
        from critic_agent.ab import run_ab

        calls = []

        def transport(request, timeout):
            calls.append(json.loads(request.data))
            return {'response': CODE if len(calls) == 1 else CHANGED, 'done': True,
                    'prompt_eval_count': 10, 'eval_count': 5}

        runner = FakeRunner([FAILED, PASSED, FAILED, PASSED])
        runner.check_reference = lambda: {'status': 'READY', 'image_id': IMAGE}
        reference = Reference()
        with temporary_directory() as temp:
            folder = run_ab(SPEC, Path(temp), OllamaClient(transport=transport), runner, reference,
                            kind='products', order_seed=7, revision_seeds=[93], static_analyzer=static_ok)
            report = json.loads((folder/'pair.json').read_bytes())
            self.assertEqual(report['status'], 'EVALUATED')
            self.assertEqual(report['delta_final_pp'], 0)
            self.assertEqual([call['options']['seed'] for call in calls], [42, 93, 93])
            self.assertEqual(len(reference.calls), 3)
            self.assertEqual(reference.calls.count(CODE.encode()), 1)
            for index, condition in enumerate(report['order'], 1):
                feedback = json.loads(calls[index]['prompt'].split('FEEDBACK_JSON:\n', 1)[1])
                self.assertEqual('findings' in feedback, condition == 'A')
                if condition == 'B':
                    self.assertNotIn('setContent', calls[index]['prompt'])
                    self.assertEqual(set(feedback), {'message'})
                branch = Path(report['branches'][condition]['run_directory'])
                self.assertEqual((branch/'initial_controller.php').read_bytes(), CODE.encode())
                manifest = json.loads((branch/'run_manifest.json').read_bytes())
                self.assertEqual(manifest['ab']['pair_id'], report['pair_id'])
                self.assertEqual(report['branches'][condition]['cost']['output_tokens_observed'], 5)
                self.assertEqual(report['branches'][condition]['cost']['model_calls'], 1)
