import hashlib
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from critic_agent.reference import (ReferenceDockerRunner, evaluate_products, reference_suite_hash,
                                    REFERENCE_TESTS)
from critic_agent.sandbox import SandboxError
from critic_agent.cli import main
from test_foundation import SPEC, temporary_directory


INITIAL = b'<?php\n// initial\n'
FINAL = b'<?php\n// final\n'
IMAGE = 'sha256:'+'b'*64


def archive(root, *, final_available=True, status='LOLOS'):
    source = root/'source'
    source.mkdir()
    (source/'spec.json').write_text(json.dumps(SPEC))
    (source/'initial_controller.php').write_bytes(INITIAL)
    if final_available:
        (source/'final_controller.php').write_bytes(FINAL)
    attempts = [{'iteration': 0, 'code_sha256': hashlib.sha256(INITIAL).hexdigest()},
                {'iteration': 1, 'code_sha256': hashlib.sha256(FINAL).hexdigest()} if final_available
                else {'iteration': 1, 'findings': [{'source': 'format'}]}]
    (source/'history.json').write_text(json.dumps({'status': status, 'attempts': attempts}))
    (source/'run_manifest.json').write_text(json.dumps({'run_id': 'source-run', 'status': status,
                                                     'final_code_available': final_available}))
    return source


def evaluated(passed):
    return {'status': 'PASSED_REFERENCE' if passed == REFERENCE_TESTS else 'FAILED_REFERENCE',
            'image_id': IMAGE, 'summary': {'total': REFERENCE_TESTS, 'passed': passed,
                                         'failure': REFERENCE_TESTS-passed, 'error': 0, 'skipped': 0}}


class FakeReferenceRunner:
    image = 'critic-laravel-evaluation:dev'
    def __init__(self, results):
        self.results = iter(results)
        self.seen = []
    def check_reference(self):
        return {'status': 'READY', 'image_id': IMAGE, 'suite_sha256': reference_suite_hash()}
    def check_candidate(self, path):
        self.seen.append(Path(path).read_bytes())
        return next(self.results)


class EvaluationTests(unittest.TestCase):
    def test_pair_rates_and_repair_preserve_source(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            source = archive(root)
            runner = FakeReferenceRunner([evaluated(30), evaluated(33)])
            folder = evaluate_products(source, root/'reports', runner)
            result = json.loads((folder/'evaluation_result.json').read_text())
            self.assertEqual(result['status'], 'EVALUATED')
            self.assertEqual(result['initial']['passed'], 30)
            self.assertEqual(result['final']['passed'], 33)
            self.assertAlmostEqual(result['uplift_pp'], 100-30/33*100)
            self.assertEqual(result['repair'], {'numerator': 1, 'denominator': 1, 'percent': 100.0})
            self.assertEqual(result['regression']['percent'], None)
            self.assertEqual(runner.seen, [INITIAL, FINAL])
            self.assertEqual((source/'final_controller.php').read_bytes(), FINAL)

    def test_regression_and_nothing_to_repair(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            folder = evaluate_products(archive(root), root/'reports', FakeReferenceRunner([evaluated(33), evaluated(32)]))
            result = json.loads((folder/'evaluation_result.json').read_text())
            self.assertEqual(result['regression']['numerator'], 1)
            self.assertIsNone(result['repair']['percent'])
            self.assertLess(result['uplift_pp'], 0)

    def test_tampered_code_or_missing_claimed_artifact_rejected(self):
        for action in ('tamper', 'delete'):
            with temporary_directory() as tmp:
                root = Path(tmp)
                source = archive(root)
                if action == 'tamper':
                    (source/'initial_controller.php').write_bytes(b'changed')
                else:
                    (source/'final_controller.php').unlink()
                with self.assertRaises(ValueError):
                    evaluate_products(source, root/'reports', FakeReferenceRunner([]))

    def test_declared_missing_final_code_is_zero_not_environment_error(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            source = archive(root, final_available=False, status='BELUM LOLOS')
            runner = FakeReferenceRunner([evaluated(30)])
            folder = evaluate_products(source, root/'reports', runner)
            result = json.loads((folder/'evaluation_result.json').read_text())
            self.assertEqual(result['status'], 'EVALUATED')
            self.assertEqual(result['final']['passed'], 0)
            self.assertEqual(result['final']['status'], 'UNAVAILABLE_CODE')
            self.assertEqual(len(runner.seen), 1)

    def test_source_error_is_excluded(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                evaluate_products(archive(root, status='ERROR'), root/'reports', FakeReferenceRunner([]))

    def test_environment_failure_keeps_metrics_unavailable(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            runner = FakeReferenceRunner([evaluated(30), {'status': 'ERROR', 'reason': 'timeout'}])
            folder = evaluate_products(archive(root), root/'reports', runner)
            result = json.loads((folder/'evaluation_result.json').read_text())
            self.assertEqual(result['status'], 'ERROR')
            self.assertIsNone(result['uplift_pp'])
            self.assertIsNone(result['repair'])

    def test_unloadable_syntax_counts_zero_without_fabricated_test_execution(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            raw = {'status': 'UNLOADABLE_CODE', 'reason': 'invalid_syntax', 'image_id': IMAGE, 'executed': False}
            runner = FakeReferenceRunner([raw, evaluated(33)])
            folder = evaluate_products(archive(root), root/'reports', runner)
            result = json.loads((folder/'evaluation_result.json').read_text())
            self.assertEqual(result['status'], 'EVALUATED')
            self.assertEqual(result['initial']['passed'], 0)
            self.assertFalse(result['initial']['runner_result']['executed'])
            self.assertEqual(result['uplift_pp'], 100.0)

    def test_changed_image_or_partial_suite_never_evaluated(self):
        for bad in [dict(evaluated(33), image_id='sha256:'+'c'*64),
                    dict(evaluated(33), summary={'total': 1, 'passed': 1})]:
            with temporary_directory() as tmp:
                root = Path(tmp)
                folder = evaluate_products(archive(root), root/'reports', FakeReferenceRunner([evaluated(30), bad]))
                result = json.loads((folder/'evaluation_result.json').read_text())
                self.assertEqual(result['status'], 'ERROR')
                self.assertIsNone(result['uplift_pp'])

    def test_reference_readiness_error_does_not_evaluate_candidates(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            runner = FakeReferenceRunner([])
            runner.check_reference = lambda: {'status': 'ERROR', 'reason': 'image_unavailable'}
            folder = evaluate_products(archive(root), root/'reports', runner)
            self.assertEqual(runner.seen, [])
            result = json.loads((folder/'evaluation_result.json').read_text())
            self.assertEqual(result['status'], 'ERROR')


class ReferenceRunnerTests(unittest.TestCase):
    def test_full_runner_uses_33_cases_and_evaluator_statuses(self):
        import base64
        calls = []
        def execute(args, **kwargs):
            calls.append(args)
            if 'run' in args:
                failures = args[-1] == 'evaluation-candidate'
                cases = ''.join(f'<testcase name="t{i}">'+('<failure message="wrong"/>' if failures and i == 0 else '')+'</testcase>' for i in range(33))
                xml = ('<testsuite>'+cases+'</testsuite>').encode()
                return subprocess.CompletedProcess(args, int(failures), b'CRITIC_JUNIT_B64:'+base64.b64encode(xml)+b'\n', b'')
            if '--format' in args:
                data = IMAGE if '{{.Id}}' in args else reference_suite_hash()
                return subprocess.CompletedProcess(args, 0, data.encode(), b'')
            return subprocess.CompletedProcess(args, 0, b'', b'')
        with temporary_directory() as tmp, patch('critic_agent.sandbox.shutil.which', return_value='docker'):
            path = Path(tmp)/'controller.php'
            path.write_bytes(INITIAL)
            runner = ReferenceDockerRunner(output_root=Path(tmp)/'harness', execute=execute)
            result = runner.check_candidate(path)
            self.assertEqual(result['status'], 'FAILED_REFERENCE')
            self.assertEqual(result['summary']['passed'], 32)
            self.assertTrue(all(c[-2] == IMAGE for c in calls if 'run' in c))

    def test_distinct_modes_and_suite_size(self):
        runner = ReferenceDockerRunner()
        self.assertEqual(runner.command('x', Path('unused'))[-1], 'evaluation-reference')
        self.assertEqual(runner.command('x', Path('unused'), Path('candidate.php'))[-1], 'evaluation-candidate')
        self.assertEqual(runner.candidate_tests, 33)

    def test_mismatched_image_suite_is_not_ready(self):
        with temporary_directory() as tmp:
            result = {'status': 'READY', 'image_id': IMAGE, 'run_directory': tmp}
            execute = lambda *args, **kw: subprocess.CompletedProcess(args, 0, b'wrong hash', b'')
            runner = ReferenceDockerRunner(execute=execute)
            with patch('critic_agent.sandbox.DockerRunner.check_reference', return_value=result):
                checked = runner.check_reference()
            self.assertEqual(checked['status'], 'ERROR')
            self.assertEqual(checked['reason'], 'suite_mismatch')

    def test_syntax_preflight_marker_requires_reserved_exit_and_successful_cleanup(self):
        import base64
        diagnostic = base64.b64encode(b'Parse error\nErrors parsing /input/controller.php\n')
        for cleanup in (0, 1):
            with temporary_directory() as tmp:
                folder = Path(tmp)
                (folder/'stdout.log').write_bytes(b'CRITIC_INVALID_SYNTAX:'+diagnostic+b'\n')
                raw = {'status': 'ERROR', 'reason': 'missing_report', 'image_id': IMAGE,
                       'run_directory': str(folder), 'exit_code': 65, 'cleanup_exit_code': cleanup}
                runner = ReferenceDockerRunner()
                with patch('critic_agent.sandbox.DockerRunner._run', return_value=raw):
                    result = runner._run(folder/'candidate.php')
                self.assertEqual(result['status'], 'UNLOADABLE_CODE' if cleanup == 0 else 'ERROR')

    def test_failed_candidate_with_cleanup_failure_is_environment_error(self):
        with temporary_directory() as tmp:
            raw = dict(evaluated(32), cleanup_exit_code=1, run_directory=tmp)
            with patch('critic_agent.sandbox.DockerRunner._run', return_value=raw):
                result = ReferenceDockerRunner()._run(Path(tmp)/'candidate.php')
            self.assertEqual(result['status'], 'ERROR')
            self.assertEqual(result['reason'], 'cleanup_failed')


class EvaluationCliTests(unittest.TestCase):
    def test_build_separate_context_with_suite_fingerprint(self):
        def inspect_context(command, **kwargs):
            context = Path(command[-1])
            expected = Path(__file__).resolve().parents[1]/'harness'/'runtime.php'
            self.assertEqual((context/'runtime.php').read_bytes(), expected.read_bytes())
            return subprocess.CompletedProcess(command, 0)
        with patch('critic_agent.cli.shutil.which', return_value='docker'), \
                patch('critic_agent.cli.subprocess.run', side_effect=inspect_context) as run:
            self.assertEqual(main(['evaluation-build']), 0)
        command = run.call_args.args[0]
        self.assertEqual(Path(command[-1]).name, 'evaluation')
        self.assertIn('SUITE_SHA256='+reference_suite_hash(), command)

    def test_evaluate_cli_does_not_call_model(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            runner = FakeReferenceRunner([evaluated(30), evaluated(33)])
            with patch('critic_agent.cli.ReferenceDockerRunner', return_value=runner), \
                    patch('critic_agent.cli.OllamaClient') as model, redirect_stdout(io.StringIO()) as output:
                code = main(['evaluate-products', str(archive(root)), '--output', str(root/'reports')])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.getvalue())['status'], 'EVALUATED')
            model.assert_not_called()


if __name__ == '__main__':
    unittest.main()
