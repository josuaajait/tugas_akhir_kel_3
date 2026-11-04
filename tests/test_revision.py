import copy
import json
from pathlib import Path
import unittest

from critic_agent.feedback import build_feedback, revision_prompt
from critic_agent.orchestrator import run_products
from critic_agent.generation import generate
from critic_agent.ollama import OllamaClient, ModelError
from critic_agent.spec import SpecError
from test_foundation import SPEC, temporary_directory


CODE = '<?php\nnamespace App\\Http\\Controllers;\nclass ProductController {}\n'
CHANGED = CODE+'// revision\n'
IMAGE = 'sha256:'+'a'*64
FAILED = {'status': 'FAILED_INTERNAL', 'image_id': IMAGE, 'summary': {
    'total': 14, 'passed': 13, 'failure': 1, 'error': 0, 'skipped': 0,
    'cases': [{'name': 'test_destroy_removes_only_target_and_returns_empty_body', 'outcome': 'failure',
               'evidence': 'Expected response status code [204] but received 500.\nBadMethodCallException: Method Illuminate\\Routing\\ResponseFactory::setContent does not exist.\nStack trace:\n#0 secret trace'}]}}
PASSED = {'status': 'PASSED_INTERNAL', 'image_id': IMAGE, 'summary': {
    'total': 14, 'passed': 14, 'failure': 0, 'error': 0, 'skipped': 0, 'cases': []}}


def static_ok(code, spec):
    return {'status': 'AWAITING_DYNAMIC_TESTS', 'findings': []}


class FakeRunner:
    image = 'critic-laravel:dev'
    def __init__(self, results):
        self.results = iter(results)
        self.calls = 0
    def check_candidate(self, path):
        self.calls += 1
        return copy.deepcopy(next(self.results))


def client_for(responses):
    responses = iter(responses)
    def transport(request, timeout):
        value = next(responses)
        if isinstance(value, Exception):
            raise value
        return {'response': value, 'done': True}
    return OllamaClient(transport=transport)


class FeedbackTests(unittest.TestCase):
    def test_destroy_feedback_compact_and_proven(self):
        feedback = build_feedback([], FAILED, 0)
        self.assertEqual(feedback['findings'][0]['location'], {'method': 'destroy'})
        evidence = feedback['findings'][0]['evidence']
        self.assertIn('204', evidence)
        self.assertIn('setContent', evidence)
        self.assertNotIn('secret trace', evidence)
        self.assertIn('destroy', revision_prompt(SPEC, CODE, feedback))

    def test_static_first_and_at_most_five(self):
        findings = [{'source': 'static', 'check': 'method', 'location': {'method': 'show'},
                     'explanation': 'missing', 'evidence': 'not found'} for _ in range(7)]
        feedback = build_feedback(findings, FAILED, 2)
        self.assertLessEqual(len(feedback['findings']), 5)
        self.assertEqual(feedback['findings'][0]['source'], 'static')


class LoopTests(unittest.TestCase):
    def run_loop(self, responses, results, **kwargs):
        temp = temporary_directory()
        self.addCleanup(temp.cleanup)
        runner = FakeRunner(results)
        root = run_products(SPEC, Path(temp.name), client_for(responses), runner,
                            static_analyzer=kwargs.pop('static_analyzer', static_ok), **kwargs)
        return root, json.loads((root/'history.json').read_text()), runner

    def test_failure_revised_to_success(self):
        root, result, runner = self.run_loop([CODE, CHANGED], [FAILED, PASSED])
        self.assertEqual(result['status'], 'LOLOS')
        self.assertEqual(result['revision_count'], 1)
        self.assertEqual(runner.calls, 2)
        self.assertEqual((root/'initial_controller.php').read_bytes(), CODE.encode())
        self.assertEqual((root/'final_controller.php').read_bytes(), CHANGED.encode())
        self.assertIn('setContent', (root/'attempts/1/prompt.txt').read_text())

    def test_initial_success_no_revision(self):
        _, result, runner = self.run_loop([CODE], [PASSED])
        self.assertEqual(result['status'], 'LOLOS')
        self.assertEqual(result['revision_count'], 0)

    def test_all_findings_archived_only_five_sent_to_model(self):
        failed = copy.deepcopy(FAILED)
        failed['summary']['passed'] = 8
        failed['summary']['failure'] = 6
        failed['summary']['cases'] = [
            {'name': f'test_destroy_case_{i}', 'outcome': 'failure', 'evidence': f'failure {i}'}
            for i in range(6)]
        root, result, _ = self.run_loop([CODE, CODE], [failed])
        self.assertEqual(len(result['attempts'][0]['findings']), 6)
        feedback = json.loads((root/'attempts/0/feedback.json').read_text())
        self.assertEqual(len(feedback['findings']), 5)

    def test_identical_stops_without_dynamic_recheck(self):
        _, result, runner = self.run_loop([CODE, CODE], [FAILED])
        self.assertEqual(result['stop_reason'], 'identical_code')
        self.assertEqual(result['status'], 'BELUM LOLOS')
        self.assertEqual(result['revision_count'], 1)
        self.assertEqual(runner.calls, 1)
        self.assertEqual(result['attempts'][-1]['reused_from'], 0)

    def test_max_three_revisions_and_last_code_retained(self):
        codes = [CODE+'//'+str(i) for i in range(4)]
        root, result, runner = self.run_loop(codes, [FAILED]*4)
        self.assertEqual(result['stop_reason'], 'max_revisions')
        self.assertEqual(result['revision_count'], 3)
        self.assertEqual(runner.calls, 4)
        self.assertEqual((root/'final_controller.php').read_bytes(), codes[-1].encode())

    def test_format_failure_consumes_revision_without_stale_final_code(self):
        root, result, runner = self.run_loop([CODE, 'not php'], [FAILED], max_revisions=1)
        self.assertEqual(result['status'], 'BELUM LOLOS')
        self.assertEqual(result['revision_count'], 1)
        self.assertFalse((root/'final_controller.php').exists())
        self.assertEqual(result['attempts'][-1]['findings'][0]['source'], 'format')

    def test_static_failure_skips_dynamic(self):
        finding = {'source': 'static', 'check': 'syntax', 'location': {'line': 2}, 'explanation': 'syntax', 'evidence': 'parse error'}
        def broken(code, spec):
            return {'findings': [finding]}
        _, result, runner = self.run_loop([CODE], [], max_revisions=0, static_analyzer=broken)
        self.assertEqual(runner.calls, 0)
        self.assertEqual(result['attempts'][0]['dynamic_status'], 'skipped')

    def test_environment_error_is_not_feedback_for_revision(self):
        _, result, runner = self.run_loop([CODE], [{'status': 'ERROR', 'reason': 'reference_not_ready'}])
        self.assertEqual(result['status'], 'ERROR')
        self.assertEqual(result['stop_reason'], 'environment_error')
        self.assertEqual(result['revision_count'], 0)

    def test_model_error_after_initial_keeps_last_completed_candidate(self):
        root, result, _ = self.run_loop([CODE, ModelError('offline')], [FAILED])
        self.assertEqual(result['status'], 'ERROR')
        self.assertEqual(result['revision_count'], 0)
        self.assertEqual((root/'final_controller.php').read_bytes(), CODE.encode())

    def test_incomplete_dynamic_success_cannot_lolos(self):
        incomplete = copy.deepcopy(PASSED)
        incomplete['summary']['passed'] = 13
        _, result, _ = self.run_loop([CODE], [incomplete])
        self.assertEqual(result['status'], 'ERROR')

    def test_resume_existing_generation_preserves_original(self):
        with temporary_directory() as temp:
            source = generate(SPEC, Path(temp)/'generation', client_for([CODE]))
            runner = FakeRunner([FAILED, PASSED])
            root = run_products(SPEC, Path(temp)/'loops', client_for([CHANGED]), runner,
                                initial_run=source, static_analyzer=static_ok)
            result = json.loads((root/'history.json').read_text())
            self.assertEqual(result['status'], 'LOLOS')
            self.assertEqual((source/'initial_controller.php').read_bytes(), CODE.encode())
            (source/'initial_controller.php').write_text('tampered')
            with self.assertRaises(ValueError):
                run_products(SPEC, Path(temp)/'other', client_for([]), runner, initial_run=source)

    def test_unsupported_contract_rejected_before_model(self):
        with temporary_directory() as temp, self.assertRaises(SpecError):
            run_products(dict(SPEC, model='Other'), Path(temp), client_for([]), FakeRunner([]))
