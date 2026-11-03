import json
import base64
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from critic_agent.sandbox import DockerRunner, SandboxError, parse_junit
from critic_agent.process import bounded_run, OutputLimitError
import sys
from test_foundation import temporary_directory


PASS_XML = b'<testsuites><testsuite tests="2" failures="0" errors="0"><testcase name="test_index" classname="ProductsContractTest"/><testcase name="test_store" classname="ProductsContractTest"/></testsuite></testsuites>'
IMAGE_ID = b'sha256:'+b'a'*64


def envelope(xml):
    return b'CRITIC_JUNIT_B64:'+base64.b64encode(xml)+b'\n'


class ReportTests(unittest.TestCase):
    def test_pass_report_counts_testcases_not_nested_suite_totals(self):
        result = parse_junit(PASS_XML)
        self.assertEqual(result['passed'], 2)
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['status'], 'PASSED')

    def test_failure_error_and_skipped_never_pass(self):
        for tag in ['failure', 'error', 'skipped']:
            xml = f'<testsuite><testcase name="test_show"><{tag} message="detail">evidence</{tag}></testcase></testsuite>'.encode()
            result = parse_junit(xml)
            self.assertNotEqual(result['status'], 'PASSED')
            self.assertEqual(result['passed'], 0)
            self.assertIn('evidence', result['cases'][0]['evidence'])

    def test_empty_malformed_and_doctype_rejected(self):
        for xml in [b'<testsuites/>', b'not xml', b'<!DOCTYPE x><testsuite/>', b'<unexpected><testcase name="x"/></unexpected>']:
            with self.subTest(xml=xml), self.assertRaises(SandboxError):
                parse_junit(xml)

    def test_duplicate_case_identity_rejected(self):
        with self.assertRaises(SandboxError):
            parse_junit(b'<testsuite><testcase name="x" classname="C"/><testcase name="x" classname="C"/></testsuite>')

    def test_suite_counters_must_agree_with_cases(self):
        with self.assertRaises(SandboxError):
            parse_junit(b'<testsuite tests="1" errors="1"><testcase name="x"/></testsuite>')


class RunnerTests(unittest.TestCase):
    def test_process_output_is_bounded(self):
        with self.assertRaises(OutputLimitError) as error:
            bounded_run([sys.executable, '-c', 'print("x" * 100000)'], timeout=5, output_limit=256)
        self.assertLessEqual(len(error.exception.output)+len(error.exception.stderr), 256)

    def test_candidate_command_is_restricted_and_only_mounts_input_and_reports(self):
        with temporary_directory() as temp:
            code = Path(temp)/'candidate.php'
            code.write_text('<?php')
            reports = Path(temp)/'reports'
            reports.mkdir()
            command = DockerRunner().command('critic-test', reports, code)
            text = ' '.join(command)
            for flag in ['--network=none', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges',
                         '--user=10001:10001', '--memory=768m', '--pids-limit=128', '--pull=never']:
                self.assertIn(flag, command)
            self.assertIn('dst=/input/controller.php,readonly', text)
            self.assertNotIn('docker.sock', text)
            self.assertNotIn('--privileged', text)
            self.assertEqual(command.count('--mount'), 1)
            self.assertNotIn('dst=/reports', text)

    def test_missing_docker_is_environment_error(self):
        with patch('critic_agent.sandbox.shutil.which', return_value=None):
            with self.assertRaises(SandboxError):
                DockerRunner().check_reference()

    def test_timeout_is_recorded_and_cleanup_attempted(self):
        calls = []
        def execute(args, **kwargs):
            calls.append(args)
            if 'run' in args:
                raise subprocess.TimeoutExpired(args, 1, output=b'test started')
            return subprocess.CompletedProcess(args, 0, IMAGE_ID, b'')
        with temporary_directory() as temp, patch('critic_agent.sandbox.shutil.which', return_value='docker'):
            result = DockerRunner(output_root=Path(temp), execute=execute).check_reference()
            self.assertEqual(result['status'], 'ERROR')
            self.assertEqual(result['reason'], 'timeout')
            self.assertTrue(any('rm' in c and '--force' in c for c in calls))
            self.assertTrue((Path(result['run_directory'])/'result.json').exists())

    def test_missing_junit_is_error_even_if_process_exits_zero(self):
        def execute(args, **kwargs):
            return subprocess.CompletedProcess(args, 0, IMAGE_ID, b'')
        with temporary_directory() as temp, patch('critic_agent.sandbox.shutil.which', return_value='docker'):
            result = DockerRunner(output_root=Path(temp), execute=execute).check_reference()
            self.assertEqual(result['status'], 'ERROR')
            self.assertEqual(result['reason'], 'missing_report')

    def test_nonzero_exit_cannot_pass_even_with_passing_junit(self):
        def execute(args, **kwargs):
            if 'run' in args:
                return subprocess.CompletedProcess(args, 2, envelope(PASS_XML), b'failed')
            return subprocess.CompletedProcess(args, 0, IMAGE_ID, b'')
        with temporary_directory() as temp, patch('critic_agent.sandbox.shutil.which', return_value='docker'):
            result = DockerRunner(output_root=Path(temp), execute=execute).check_reference()
            self.assertNotEqual(result['status'], 'READY')

    def test_candidate_is_not_run_if_reference_readiness_fails(self):
        with temporary_directory() as temp:
            path = Path(temp)/'code.php'
            path.write_text('<?php')
            runner = DockerRunner(output_root=Path(temp))
            with patch.object(runner, 'check_reference', return_value={'status': 'ERROR', 'reason': 'offline'}), \
                 patch.object(runner, '_run') as run:
                result = runner.check_candidate(path)
                self.assertEqual(result['status'], 'ERROR')
                run.assert_not_called()

    def test_success_uses_immutable_image_and_cleanup_failure_cannot_be_ready(self):
        calls = []
        def execute(args, **kwargs):
            calls.append(args)
            if 'run' in args:
                cases = ''.join(f'<testcase name="t{i}"/>' for i in range(21))
                return subprocess.CompletedProcess(args, 0, envelope(('<testsuite>'+cases+'</testsuite>').encode()), b'')
            if 'rm' in args:
                return subprocess.CompletedProcess(args, 1, b'', b'cannot remove')
            return subprocess.CompletedProcess(args, 0, IMAGE_ID, b'')
        with temporary_directory() as temp, patch('critic_agent.sandbox.shutil.which', return_value='docker'):
            result = DockerRunner(output_root=Path(temp), execute=execute).check_reference()
            self.assertEqual(result['status'], 'ERROR')
            self.assertEqual(result['reason'], 'cleanup_failed')
            run = next(c for c in calls if 'run' in c)
            self.assertEqual(run[-2], IMAGE_ID.decode())

    def test_output_limit_is_recorded_and_container_cleanup_attempted(self):
        calls = []
        def execute(args, **kwargs):
            calls.append(args)
            if 'run' in args:
                raise OutputLimitError(b'overflow', b'')
            return subprocess.CompletedProcess(args, 0, IMAGE_ID, b'')
        with temporary_directory() as temp, patch('critic_agent.sandbox.shutil.which', return_value='docker'):
            result = DockerRunner(output_root=Path(temp), execute=execute).check_reference()
            self.assertEqual(result['reason'], 'output_limit')
            self.assertTrue(any('rm' in c for c in calls))


if __name__ == '__main__':
    unittest.main()
