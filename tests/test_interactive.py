import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from test_foundation import temporary_directory


def answers():
    return ['books', 'Book', 'BookController', '2',
            'title', 'string', '', '80', 'y',
            'pages', 'integer', '1', '', 'n']


class InteractiveTests(unittest.TestCase):
    def collect(self, values):
        from critic_agent.interactive import collect_spec
        messages = []
        supplied = iter(values)
        return collect_spec(read=lambda prompt: next(supplied), write=messages.append), messages

    def test_collects_user_fields_into_reusable_contract(self):
        spec, _ = self.collect(answers())
        self.assertEqual(spec['resource'], 'books')
        self.assertEqual(spec['model'], 'Book')
        self.assertEqual(spec['controller'], 'BookController')
        self.assertEqual(spec['fields'], [
            {'name': 'title', 'type': 'string',
             'rules': ['required', 'string', 'max:80', 'unique:books,title']},
            {'name': 'pages', 'type': 'integer', 'rules': ['required', 'integer', 'min:1']},
        ])
        self.assertEqual(spec['operations']['destroy'], {'success_status': 204, 'not_found_status': 404})

    def test_reprompts_invalid_names_types_bounds_and_duplicates(self):
        values = ['../bad', 'migrations', 'books', 'class', 'Book', 'Controller',
                  'BookController', '0', '2', 'id', 'title', 'float', 'string',
                  'oops', '', '300', '80', 'maybe', 'n',
                  'title', 'pages', 'integer', '10', '2', 'n', '1', '20', 'n']
        spec, messages = self.collect(values)
        self.assertEqual([f['name'] for f in spec['fields']], ['title', 'pages'])
        self.assertEqual(spec['fields'][1]['rules'], ['required', 'integer', 'min:1', 'max:20'])
        self.assertTrue(messages)

    def test_decline_confirmation_has_no_files_or_model_calls(self):
        from critic_agent.interactive import start_interactive
        with temporary_directory() as tmp, patch('builtins.input', side_effect=answers()+['n']):
            result = start_interactive(Path(tmp)/'sessions', write=lambda text: None)
            self.assertEqual(result['status'], 'CANCELLED')
            self.assertFalse((Path(tmp)/'sessions').exists())

    def test_eof_and_interrupt_cancel_without_traceback(self):
        from critic_agent.cli import main
        for error in (EOFError, KeyboardInterrupt):
            with self.subTest(error=error), temporary_directory() as tmp:
                with patch('builtins.input', side_effect=error), contextlib.redirect_stderr(io.StringIO()), \
                        contextlib.redirect_stdout(io.StringIO()) as output:
                    code = main(['start', '--output', str(Path(tmp)/'sessions')])
                self.assertEqual(code, 130)
                self.assertEqual(json.loads(output.getvalue())['status'], 'CANCELLED')
                self.assertFalse((Path(tmp)/'sessions').exists())

    def test_narrow_unique_integer_domain_is_reprompted(self):
        spec, _ = self.collect(['items', 'Item', 'ItemController', '1',
                                'code', 'integer', '1', '3', 'y', '1', '5', 'y'])
        self.assertEqual(spec['fields'][0]['rules'],
                         ['required', 'integer', 'min:1', 'max:5', 'unique:items,code'])

    def test_real_terminal_input_can_cancel_without_a_spec_file(self):
        with temporary_directory() as tmp:
            result = subprocess.run([sys.executable, '-m', 'critic_agent', 'start', '--output', tmp],
                                    input='\n'.join(answers()+['n'])+'\n', capture_output=True,
                                    text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 130, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'CANCELLED')
            self.assertIn('BookController', result.stderr)
            self.assertFalse(list(Path(tmp).iterdir()))

    def test_start_help_and_invalid_configuration_before_input(self):
        result = subprocess.run([sys.executable, '-m', 'critic_agent', 'start', '--help'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        from critic_agent.cli import main
        with patch('builtins.input', side_effect=AssertionError('must not prompt')), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['start', '--temperature', 'nan']), 2)


class StartExecutionTests(unittest.TestCase):
    def ready(self):
        return {'ready': True, 'checks': {
            'python': {'ok': True}, 'php': {'ok': True}, 'docker': {'ok': True},
            'ollama': {'ok': True, 'detail': ['qwen2.5:7b-instruct']}, 'qwen': {'ok': True},
        }}

    def test_environment_failure_preserves_spec_and_stops_before_build(self):
        from critic_agent.interactive import start_interactive
        with temporary_directory() as tmp, patch('builtins.input', side_effect=answers()+['y']), \
                patch('critic_agent.interactive.doctor', return_value={'ready': False, 'checks': {
                    'docker': {'ok': False, 'detail': 'endpoint unavailable'}}}):
            result = start_interactive(Path(tmp), write=lambda text: None)
            self.assertEqual(result['status'], 'ERROR')
            self.assertEqual(result['stage'], 'prerequisites')
            folder = Path(result['session_directory'])
            self.assertEqual(json.loads((folder/'spec.json').read_text())['resource'], 'books')
            self.assertEqual(json.loads((folder/'session.json').read_text())['status'], 'ERROR')
            self.assertFalse((folder/'runs').exists())

    def test_build_failure_is_archived_without_model_generation(self):
        from critic_agent.interactive import start_interactive
        with temporary_directory() as tmp:
            build = Path(tmp)/'failed-build'
            build.mkdir()
            (build/'build_result.json').write_text(json.dumps({'status': 'ERROR', 'detail': 'build failed'}))
            with patch('builtins.input', side_effect=answers()+['y']), \
                    patch('critic_agent.interactive.doctor', return_value=self.ready()), \
                    patch('critic_agent.interactive.prepare_base', return_value='critic-laravel:dev'), \
                    patch('critic_agent.interactive.build_resource', return_value=build):
                result = start_interactive(Path(tmp)/'sessions', write=lambda text: None)
            self.assertEqual(result['status'], 'ERROR')
            self.assertEqual(result['stage'], 'build_resource')
            self.assertEqual(result['build_directory'], str(build.resolve()))
            self.assertFalse((Path(result['session_directory'])/'runs').exists())

    def test_readiness_failure_stops_before_loop(self):
        self.execute(readiness={'status': 'ERROR', 'reason': 'reference_not_ready'}, expected='ERROR')

    def test_ready_runs_real_loop_and_retains_terminal_status(self):
        self.execute(readiness={'status': 'READY', 'image_id': 'sha256:'+'a'*64}, expected='BELUM LOLOS')

    def test_success_requires_actual_dynamic_pass_and_exposes_final_code(self):
        self.execute(readiness={'status': 'READY', 'image_id': 'sha256:'+'a'*64}, expected='LOLOS')

    def test_interrupt_during_model_call_records_terminal_loop_and_location(self):
        from critic_agent.cli import main
        from critic_agent.resources import ResourceDockerRunner
        with temporary_directory() as tmp:
            folder = Path(tmp)
            build = folder/'built'
            build.mkdir()
            (build/'build_result.json').write_text(json.dumps({'status': 'BUILT'}))
            with patch('builtins.input', side_effect=answers()+['y']), \
                    patch('critic_agent.interactive.doctor', return_value=self.ready()), \
                    patch('critic_agent.interactive.prepare_base', return_value='critic-laravel:dev'), \
                    patch('critic_agent.interactive.build_resource', return_value=build), \
                    patch.object(ResourceDockerRunner, 'check_reference', return_value={
                        'status': 'READY', 'image_id': 'sha256:'+'a'*64}), \
                    patch('critic_agent.ollama.OllamaClient.generate', side_effect=KeyboardInterrupt), \
                    contextlib.redirect_stdout(io.StringIO()) as output, \
                    contextlib.redirect_stderr(io.StringIO()):
                code = main(['start', '--output', str(folder/'sessions')])
            self.assertEqual(code, 130)
            result = json.loads(output.getvalue())
            self.assertEqual(result['status'], 'CANCELLED')
            run = Path(result['run_directory'])
            for name in ('history.json', 'run_manifest.json'):
                saved = json.loads((run/name).read_text())
                self.assertEqual(saved['status'], 'ERROR')
                self.assertEqual(saved['stop_reason'], 'user_cancelled')
            self.assertTrue((run/'attempts/0/prompt.txt').is_file())
            self.assertIn('dibatalkan', json.loads((run/'attempts/0/result.json').read_text())['error'])

    def execute(self, *, readiness, expected):
        from critic_agent.interactive import start_interactive
        from critic_agent.resources import ResourceDockerRunner
        from test_static import GOOD
        response = GOOD.replace('ProductController', 'BookController') if expected == 'LOLOS' else 'No PHP code was produced.'
        # External Docker and model are controlled; real orchestrator creates immutable attempt archives.
        with temporary_directory() as tmp:
            folder = Path(tmp)
            build = folder/'built'
            build.mkdir()
            (build/'build_result.json').write_text(json.dumps({'status': 'BUILT'}))
            with patch('builtins.input', side_effect=answers()+['y']), \
                    patch('critic_agent.interactive.doctor', return_value=self.ready()), \
                    patch('critic_agent.interactive.prepare_base', return_value='critic-laravel:dev'), \
                    patch('critic_agent.interactive.build_resource', return_value=build), \
                    patch.object(ResourceDockerRunner, 'check_reference', return_value=readiness), \
                    patch.object(ResourceDockerRunner, 'check_candidate', return_value={
                        'status': 'PASSED_INTERNAL', 'image_id': 'sha256:'+'a'*64,
                        'summary': {'total': 12, 'passed': 12, 'failure': 0, 'error': 0, 'skipped': 0}}), \
                    patch('critic_agent.ollama.OllamaClient.generate', return_value={
                        'done': True, 'response': response}):
                if expected == 'LOLOS':
                    from critic_agent.cli import main
                    with contextlib.redirect_stdout(io.StringIO()) as output, \
                            contextlib.redirect_stderr(io.StringIO()):
                        exit_code = main(['start', '--output', str(folder/'sessions'), '--max-revisions', '0'])
                    self.assertEqual(exit_code, 0)
                    result = json.loads(output.getvalue())
                    self.assertEqual(result['history'][0]['passed'], 12)
                    self.assertTrue(Path(result['final_controller']).is_file())
                else:
                    result = start_interactive(folder/'sessions', write=lambda text: None, max_revisions=0)
            self.assertEqual(result['status'], expected)
            saved = json.loads((Path(result['session_directory'])/'session.json').read_text())
            self.assertEqual(saved['status'], expected)
            self.assertTrue(saved['image'].startswith('critic-interactive-'))
            if expected != 'ERROR':
                run = Path(result['run_directory'])
                self.assertEqual(json.loads((run/'spec.json').read_text())['fields'][0]['name'], 'title')
                self.assertTrue((run/'attempts/0/response.json').is_file())
                self.assertEqual(result['stop_reason'], 'all_checks_passed' if expected == 'LOLOS' else 'max_revisions')
                if expected == 'LOLOS':
                    self.assertTrue((run/'final_controller.php').is_file())


class BasePreparationTests(unittest.TestCase):
    def test_existing_base_is_reused_and_missing_base_gets_owned_tag(self):
        from critic_agent.interactive import prepare_base
        for exists in (True, False):
            with self.subTest(exists=exists), temporary_directory() as tmp:
                commands = []

                def execute(command, **kwargs):
                    commands.append(command)
                    status = 0 if exists or command[1] == 'build' else 1
                    return subprocess.CompletedProcess(command, status, b'output', b'detail')

                with patch('critic_agent.interactive.bounded_run', side_effect=execute):
                    image = prepare_base(Path(tmp), timeout=600, write=lambda text: None)
                records = [json.loads(path.read_text()) for path in Path(tmp).glob('*.json')]
                self.assertEqual(records[0]['timeout_seconds'], 600)
                if exists:
                    self.assertEqual(image, 'critic-laravel:dev')
                    self.assertEqual(len(commands), 1)
                else:
                    self.assertTrue(image.startswith('critic-interactive-base-'))
                    self.assertEqual(commands[-1][1:4], ['build', '--tag', image])
                    self.assertTrue((Path(tmp)/'base-build.stdout.log').is_file())

    def test_failed_and_timed_out_base_builds_preserve_command_output(self):
        from critic_agent.interactive import prepare_base
        from critic_agent.sandbox import SandboxError
        for timeout in (False, True):
            with self.subTest(timeout=timeout), temporary_directory() as tmp:
                def execute(command, **kwargs):
                    if command[1] == 'build' and timeout:
                        raise subprocess.TimeoutExpired(command, 600, output=b'partial', stderr=b'timeout detail')
                    return subprocess.CompletedProcess(command, 1, b'partial', b'failed')

                with patch('critic_agent.interactive.bounded_run', side_effect=execute):
                    with self.assertRaises((SandboxError, subprocess.TimeoutExpired)):
                        prepare_base(Path(tmp), timeout=600, write=lambda text: None)
                self.assertEqual((Path(tmp)/'base-build.stdout.log').read_bytes(), b'partial')
                record = json.loads((Path(tmp)/'base-build.json').read_text())
                self.assertTrue('error' in record or record['exit_code'] == 1)


if __name__ == '__main__':
    unittest.main()
