"""Presentation contracts: shell pipelines remain machine-readable."""
import contextlib
import io
import json
import os
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

from critic_agent.cli import main


class Terminal(io.StringIO):
    def isatty(self):
        return True


class PresentationCliTests(unittest.TestCase):
    def invoke(self, args, *, terminal=False):
        output = Terminal() if terminal else io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = main(args)
        return code, output.getvalue(), errors.getvalue()

    def test_pipe_defaults_to_original_json(self):
        code, output, errors = self.invoke(['validate', 'examples/products.json'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output), {'valid': True, 'spec_id': 'products_basic', 'contract': 'v1-basic'})
        self.assertEqual(errors, '')

    def test_terminal_defaults_to_readable_output(self):
        code, output, _ = self.invoke(['validate', 'examples/products.json'], terminal=True)
        self.assertEqual(code, 0)
        self.assertIn('CRITIC AGENT', output)
        self.assertIn('products_basic', output)
        self.assertNotIn('"valid":', output)

    def test_pretty_and_json_flags_work_on_both_sides_of_command(self):
        for flag in ('--pretty', '--json'):
            for args in ([flag, 'validate', 'examples/products.json'],
                         ['validate', 'examples/products.json', flag]):
                with self.subTest(args=args):
                    code, output, _ = self.invoke(args)
                    self.assertEqual(code, 0)
                    if flag == '--json':
                        self.assertTrue(json.loads(output)['valid'])
                    else:
                        self.assertIn('CRITIC AGENT', output)

    def test_explicit_json_overrides_terminal_and_does_not_leak_to_next_call(self):
        code, output, _ = self.invoke(['validate', 'examples/products.json', '--json'], terminal=True)
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output)['valid'])
        self.assertIn('CRITIC AGENT', self.invoke(['validate', 'examples/products.json'], terminal=True)[1])

    def test_pretty_prompt_is_still_the_exact_raw_prompt(self):
        raw = self.invoke(['prompt', 'examples/products.json'])[1]
        code, pretty, _ = self.invoke(['prompt', 'examples/products.json', '--pretty'])
        self.assertEqual(code, 0)
        self.assertEqual(pretty, raw)

    def test_pretty_input_error_preserves_exit_code_and_diagnostic(self):
        code, _, errors = self.invoke(['validate', 'missing-spec.json', '--pretty'])
        self.assertEqual(code, 2)
        self.assertIn('ERROR', errors)
        self.assertIn('missing-spec.json', errors)
        self.assertNotIn('Traceback', errors)

    def test_pretty_doctor_renders_failed_checks_without_success_claim(self):
        with patch('critic_agent.cli.doctor', return_value={
                'ready': False, 'checks': {'docker': {'ok': False, 'detail': 'endpoint unavailable'}}}):
            code, output, _ = self.invoke(['doctor', '--pretty', '--no-color'])
        self.assertEqual(code, 3)
        self.assertIn('endpoint unavailable', output)
        self.assertIn('docker', output)
        self.assertNotIn('LOLOS', output)
        self.assertNotIn('\x1b', output)

    def test_subprocess_pretty_does_not_require_a_terminal(self):
        result = subprocess.run([sys.executable, '-m', 'critic_agent', 'validate',
                                 'examples/products.json', '--pretty'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('CRITIC AGENT', result.stdout)
        self.assertNotIn('\x1b', result.stdout)

    def test_build_logs_go_to_stderr_and_stdout_is_one_json_result(self):
        def build(command, **kwargs):
            print('Docker build output', file=kwargs.get('stdout') or sys.stdout)
            return subprocess.CompletedProcess(command, 0)

        with patch('critic_agent.cli.shutil.which', return_value='docker'), \
                patch('critic_agent.cli.subprocess.run', side_effect=build):
            code, output, errors = self.invoke(['harness-build', '--json'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)['status'], 'BUILT')
        self.assertIn('Docker build output', errors)

    def test_help_honors_explicit_machine_mode_before_parsing_exits(self):
        output = Terminal()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as exited:
            main(['--json', '--help'])
        self.assertEqual(exited.exception.code, 0)
        self.assertIn('usage:', output.getvalue())
        self.assertNotIn('CRITIC AGENT', output.getvalue())


class RendererTests(unittest.TestCase):
    def render(self, value, *, columns='88', environment=None):
        from critic_agent.console import Console
        output = Terminal()
        with patch.dict(os.environ, {'COLUMNS': columns, 'TERM': 'xterm', **(environment or {})}, clear=True), \
                contextlib.redirect_stdout(output):
            with Console(mode='pretty') as console:
                console.result(value)
        return output.getvalue()

    def test_zero_false_null_and_unknown_status_remain_distinct(self):
        text = self.render({'status': 'provisional_unreviewed', 'reviewed': False,
                            'count': 0, 'metric': None, 'history': [
                                {'attempt': 0, 'passed': 0, 'total': 14, 'error': None}]},
                           environment={'NO_COLOR': ''})
        for expected in ('provisional_unreviewed', 'tidak', '0', '14', 'N/A'):
            self.assertIn(expected, text)
        self.assertNotIn('LOLOS', text)
        self.assertNotIn('\x1b', text)

    def test_terminal_color_can_be_disabled_by_environment(self):
        self.assertIn('\x1b[', self.render({'status': 'LOLOS'}))
        for environment in ({'NO_COLOR': '1'}, {'TERM': 'dumb'}):
            with self.subTest(environment=environment):
                self.assertNotIn('\x1b', self.render({'status': 'LOLOS'}, environment=environment))

    def test_long_paths_and_many_columns_wrap_in_narrow_terminal(self):
        text = self.render({'path': 'C:/very-long-project-name/very-long-archive-name/controller.php',
                            'history': [{'attempt': 0, 'passed': 0, 'total': 14,
                                         'findings': 1, 'error': 'unavailable'}]},
                           columns='36', environment={'NO_COLOR': '1'})
        self.assertTrue(all(len(line) <= 35 for line in text.splitlines()), text)
        self.assertIn('controller.php', text.replace('\n', '').replace(' ', '').replace('|', ''))
        self.assertIn('unavailable', text)

    def test_terminal_control_sequences_do_not_reach_pretty_output(self):
        text = self.render({'detail': '\x1b[2Jinjected\x1b]0;bad-title\x07\rtext'},
                           environment={'NO_COLOR': '1'})
        self.assertNotIn('\x1b', text)
        self.assertNotIn('\x07', text)
        self.assertNotIn('\r', text)
        self.assertNotIn('bad-title', text)
        self.assertIn('injected', text)

    def test_spinner_stops_before_input_and_on_exception(self):
        from critic_agent.console import Console
        with contextlib.redirect_stdout(Terminal()), contextlib.redirect_stderr(Terminal()), \
                patch.dict(os.environ, {'TERM': 'xterm'}):
            with self.assertRaises(RuntimeError):
                with Console(mode='pretty') as console:
                    console.progress('Generating controller')
                    with patch('builtins.input', return_value='n'):
                        self.assertEqual(console.read('Continue? '), 'n')
                    self.assertFalse(any(t.name == 'critic-console' for t in threading.enumerate()))
                    console.progress('Checking controller')
                    raise RuntimeError('cancelled')
        self.assertFalse(any(t.name == 'critic-console' for t in threading.enumerate()))


class LoopProgressTests(unittest.TestCase):
    def test_actual_stages_are_visible_before_work_and_archives_keep_their_results(self):
        from pathlib import Path
        from critic_agent.cli import emit, loop_summary
        from critic_agent.console import Console
        from critic_agent.orchestrator import run_products
        from test_foundation import SPEC, temporary_directory
        from test_revision import CODE, CHANGED, FAILED, PASSED, FakeRunner, client_for, static_ok

        for identical in (False, True):
            with self.subTest(identical=identical), temporary_directory() as tmp:
                errors, output = io.StringIO(), io.StringIO()
                client = client_for([CODE, CODE if identical else CHANGED])
                generate = client.generate

                def observe_generation(prompt):
                    self.assertIn('Qwen', errors.getvalue())
                    return generate(prompt)

                client.generate = observe_generation
                test = self

                class ObservedRunner(FakeRunner):
                    def check_candidate(self, path):
                        test.assertIn('14 test internal', errors.getvalue())
                        return super().check_candidate(path)

                runner = ObservedRunner([FAILED] if identical else [FAILED, PASSED])
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    with Console(mode='pretty', no_color=True):
                        folder = run_products(SPEC, Path(tmp), client, runner, static_analyzer=static_ok)
                        emit(loop_summary(folder))
                saved = json.loads((folder/'history.json').read_text())
                self.assertEqual(saved['status'], 'BELUM LOLOS' if identical else 'LOLOS')
                self.assertEqual(saved['stop_reason'], 'identical_code' if identical else 'all_checks_passed')
                self.assertEqual(saved['revision_count'], 1)
                self.assertEqual((folder/'initial_controller.php').read_bytes(), CODE.encode())
                self.assertIn('13/14', errors.getvalue())
                self.assertIn('Revisi 1', errors.getvalue())
                if identical:
                    self.assertIn('identik', errors.getvalue())
                    self.assertNotIn('[ LOLOS ]', output.getvalue())
                else:
                    self.assertIn('14/14', errors.getvalue())
                    self.assertIn('[ LOLOS ]', output.getvalue())


if __name__ == '__main__':
    unittest.main()
