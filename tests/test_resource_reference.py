import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch
from critic_agent import __version__

from critic_agent.resource_reference import (resource_reference_manifest, render_resource_reference,
                                             ResourceReferenceRunner, build_resource_reference,
                                             evaluate_resource)
from critic_agent.reference import reference_suite_hash
from critic_agent.resources import resource_contract
from critic_agent.cli import main
from test_evaluation import archive, INITIAL, FINAL, IMAGE
from test_foundation import temporary_directory

ROOT = Path(__file__).resolve().parents[1]


def spec(name):
    return json.loads((ROOT/'examples'/(name+'.json')).read_text())


def source_archive(root, name, *, identical=False):
    source = archive(root)
    (source/'spec.json').write_text(json.dumps(spec(name)))
    if identical:
        (source/'final_controller.php').write_bytes(INITIAL)
        history = json.loads((source/'history.json').read_text())
        history['attempts'][-1]['code_sha256'] = history['attempts'][0]['code_sha256']
        (source/'history.json').write_text(json.dumps(history))
    return source


class FakeRunner:
    def __init__(self, source_spec, results):
        self.spec = copy.deepcopy(source_spec)
        meta = resource_reference_manifest(source_spec)
        self.candidate_tests = meta['expected_tests']
        self.expected_suite_sha256 = meta['suite_sha256']
        self.image = 'test-image'
        self.results = iter(results)
        self.seen = []
    def check_reference(self):
        return {'status': 'READY', 'image_id': IMAGE, 'suite_sha256': self.expected_suite_sha256}
    def check_candidate(self, path):
        self.seen.append(Path(path).read_bytes())
        return next(self.results)


def evaluated(total, passed):
    return {'status': 'PASSED_REFERENCE' if passed == total else 'FAILED_REFERENCE',
            'image_id': IMAGE, 'summary': {'total': total, 'passed': passed, 'failure': total-passed,
                                         'error': 0, 'skipped': 0}}


class ResourceReferenceProfileTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('php'), 'PHP needed for trusted assertion probe')
    def test_collection_assertion_rejects_swapped_ids_missing_fields_and_duplicates(self):
        if not (ROOT/'harness/laravel/vendor/autoload.php').exists():
            self.skipTest('Harness vendor not installed')
        with temporary_directory() as tmp:
            folder = Path(tmp).resolve()
            script = r'''<?php
require $argv[1];
require $argv[2];
// Configure PHPUnit assertion formatting only; no application/test runner boot.
(new PHPUnit\TextUI\Configuration\Builder)->build(['assertion-probe', '--no-configuration']);
$class = new ReflectionClass(Evaluation\ResourceReferenceTest::class);
$instance = $class->newInstanceWithoutConstructor();
$method = $class->getMethod('assertCollectionRecords');
$expected = [11 => ['title' => 'First', 'pages' => 40], 12 => ['title' => 'Second', 'pages' => 80]];
$good = [['id' => 11, 'title' => 'First', 'pages' => 40], ['id' => 12, 'title' => 'Second', 'pages' => 80]];
$method->invoke($instance, $good, $expected);
$method->invoke($instance, array_reverse($good), $expected);
$badCases = [
    [['id' => 12, 'title' => 'First', 'pages' => 40], ['id' => 11, 'title' => 'Second', 'pages' => 80]],
    [['id' => 11, 'title' => 'First'], $good[1]],
    [$good[0], $good[0]],
];
foreach ($badCases as $records) {
    try { $method->invoke($instance, $records, $expected); exit(2); }
    catch (PHPUnit\Framework\AssertionFailedError $e) { /* intended rejection */ }
}
echo 'accepted valid; rejected three invalid collections';
'''
            (folder/'probe.php').write_text(script)
            result = subprocess.run(['php', str(folder/'probe.php'), str(ROOT/'harness/laravel/vendor/autoload.php'),
                                     str(ROOT/'evaluation/resource-reference/ResourceReferenceTest.php')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('rejected three', result.stdout)

    def test_authored_profiles_counts_and_separate_fixtures(self):
        for name, total in [('books', 35), ('inventory_items', 57)]:
            data = spec(name)
            meta = resource_reference_manifest(data)
            self.assertEqual(meta['expected_tests'], total)
            self.assertEqual(meta['prototype_version'], __version__)
            self.assertEqual(meta, resource_reference_manifest(data))
            files = render_resource_reference(data)
            profile = json.loads(files['profile.json'])
            self.assertNotEqual(profile['fixtures'], resource_contract(data)['fixtures'])
            self.assertIn('ResourceReferenceTest.php', files)
            self.assertNotIn('ResourceContractTest', files['ResourceReferenceTest.php'])
            self.assertNotIn('ResourceReadinessTest', files['ResourceReferenceTest.php'])
            self.assertNotIn('ResourceFixtures', files['ResourceReferenceTest.php'])
            self.assertNotIn('critic/contract.json', files['ResourceReferenceTest.php'])

    def test_changed_contract_or_unknown_resource_rejected(self):
        data = spec('books')
        data['fields'][0]['rules'][-1] = 'max:79'
        with self.assertRaises(ValueError):
            resource_reference_manifest(data)
        data = spec('products')
        with self.assertRaises(ValueError):
            resource_reference_manifest(data)

    @unittest.skipUnless(shutil.which('php'), 'PHP needed for trusted lint/providers')
    def test_trusted_suite_lint_and_provider_counts(self):
        if not (ROOT/'harness/laravel/vendor/autoload.php').exists():
            self.skipTest('Harness vendor not installed')
        for name in ('books', 'inventory_items'):
            data = spec(name)
            with temporary_directory() as tmp:
                folder = Path(tmp).resolve()
                (folder/'reference').mkdir()
                files = render_resource_reference(data)
                for filename, content in files.items():
                    if filename.endswith('.php'):
                        lint = subprocess.run(['php', '-n', '-l'], input=content.encode(), capture_output=True)
                        self.assertEqual(lint.returncode, 0, lint.stdout+lint.stderr)
                (folder/'reference-profile.json').write_text(files['profile.json'])
                (folder/'reference/ResourceReferenceTest.php').write_text(files['ResourceReferenceTest.php'])
                script = r'''<?php
require $argv[1];
require $argv[2].'/reference/ResourceReferenceTest.php';
$class = new ReflectionClass(Evaluation\ResourceReferenceTest::class);
$count = 0;
foreach ($class->getMethods(ReflectionMethod::IS_PUBLIC) as $method) {
    if (!str_starts_with($method->getName(), 'test_')) continue;
    $providers = $method->getAttributes(PHPUnit\Framework\Attributes\DataProvider::class);
    $count += $providers ? count($class->getMethod($providers[0]->getArguments()[0])->invoke(null)) : 1;
}
echo $count;
'''
                (folder/'count.php').write_text(script)
                result = subprocess.run(['php', str(folder/'count.php'), str(ROOT/'harness/laravel/vendor/autoload.php'), str(folder)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                self.assertEqual(int(result.stdout), resource_reference_manifest(data)['expected_tests'])


class ResourceReferencePairTests(unittest.TestCase):
    def test_35_case_same_code_pair_executes_both_and_has_no_repair_denominator(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            source = source_archive(root, 'books', identical=True)
            runner = FakeRunner(spec('books'), [evaluated(35, 35), evaluated(35, 35)])
            folder = evaluate_resource(source, root/'reports', runner)
            result = json.loads((folder/'evaluation_result.json').read_text())
            self.assertEqual(result['status'], 'EVALUATED')
            self.assertEqual(result['expected_tests'], 35)
            self.assertEqual(result['initial']['total'], 35)
            self.assertEqual(result['uplift_pp'], 0)
            self.assertIsNone(result['repair']['percent'])
            self.assertEqual(runner.seen, [INITIAL, INITIAL])

    def test_57_case_partial_improvement_and_raw_counts(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            source = source_archive(root, 'inventory_items')
            runner = FakeRunner(spec('inventory_items'), [evaluated(57, 40), evaluated(57, 44)])
            folder = evaluate_resource(source, root/'reports', runner)
            result = json.loads((folder/'evaluation_result.json').read_text())
            self.assertEqual(result['status'], 'EVALUATED')
            self.assertAlmostEqual(result['uplift_pp'], 4/57*100)
            self.assertEqual(result['repair'], {'numerator': 0, 'denominator': 1, 'percent': 0})
            self.assertEqual((source/'final_controller.php').read_bytes(), FINAL)

    def test_wrong_spec_runner_and_incomplete_result_rejected(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            source = source_archive(root, 'books')
            with self.assertRaises(ValueError):
                evaluate_resource(source, root/'reports', FakeRunner(spec('inventory_items'), []))
            runner = FakeRunner(spec('books'), [evaluated(33, 33)])
            folder = evaluate_resource(source, root/'reports', runner)
            result = json.loads((folder/'evaluation_result.json').read_text())
            self.assertEqual(result['status'], 'ERROR')
            self.assertIsNone(result['uplift_pp'])

    def test_source_tampering_rejected_before_candidate_execution(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            source = source_archive(root, 'books')
            (source/'final_controller.php').write_bytes(b'changed')
            runner = FakeRunner(spec('books'), [])
            with self.assertRaises(ValueError):
                evaluate_resource(source, root/'reports', runner)
            self.assertEqual(runner.seen, [])

    def test_absent_final_and_syntax_error_keep_resource_denominators(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            source = source_archive(root, 'inventory_items')
            manifest = json.loads((source/'run_manifest.json').read_text())
            manifest.update(status='BELUM LOLOS', final_code_available=False)
            (source/'run_manifest.json').write_text(json.dumps(manifest))
            history = json.loads((source/'history.json').read_text())
            history['status'] = 'BELUM LOLOS'
            del history['attempts'][-1]['code_sha256']
            (source/'history.json').write_text(json.dumps(history))
            (source/'final_controller.php').unlink()
            runner = FakeRunner(spec('inventory_items'), [evaluated(57, 40)])
            result = json.loads((evaluate_resource(source, root/'reports', runner)/'evaluation_result.json').read_text())
            self.assertEqual(result['status'], 'EVALUATED')
            self.assertEqual(result['final']['passed'], 0)
            self.assertEqual(result['final']['total'], 57)
            self.assertFalse(result['final']['runner_result']['executed'])
        with temporary_directory() as tmp:
            root = Path(tmp)
            raw = {'status': 'UNLOADABLE_CODE', 'reason': 'invalid_syntax', 'image_id': IMAGE, 'executed': False}
            runner = FakeRunner(spec('books'), [raw, evaluated(35, 35)])
            result = json.loads((evaluate_resource(source_archive(root, 'books'), root/'reports', runner)/'evaluation_result.json').read_text())
            self.assertEqual(result['initial']['total'], 35)
            self.assertEqual(result['initial']['passed'], 0)
            self.assertEqual(result['repair']['percent'], 100)

    def test_environment_wrong_image_or_suite_has_no_metrics(self):
        for bad in ({'status': 'ERROR', 'reason': 'timeout'}, dict(evaluated(35, 35), image_id='sha256:'+'c'*64)):
            with temporary_directory() as tmp:
                root = Path(tmp)
                runner = FakeRunner(spec('books'), [evaluated(35, 30), bad])
                result = json.loads((evaluate_resource(source_archive(root, 'books'), root/'reports', runner)/'evaluation_result.json').read_text())
                self.assertEqual(result['status'], 'ERROR')
                self.assertIsNone(result['uplift_pp'])
                self.assertIsNone(result['repair'])
        with temporary_directory() as tmp:
            root = Path(tmp)
            runner = FakeRunner(spec('books'), [])
            runner.check_reference = lambda: {'status': 'READY', 'image_id': IMAGE, 'suite_sha256': 'wrong'}
            result = json.loads((evaluate_resource(source_archive(root, 'books'), root/'reports', runner)/'evaluation_result.json').read_text())
            self.assertEqual(result['status'], 'ERROR')
            self.assertEqual(runner.seen, [])


class ResourceReferenceRunnerBuildTests(unittest.TestCase):
    def test_runner_checks_its_own_profile_hash(self):
        for correct in (True, False):
            with temporary_directory() as tmp:
                def execute(args, **kwargs):
                    expected = (resource_contract(spec('books'))['contract_sha256']
                                if 'org.critic.resource-contract-sha256' in ' '.join(args)
                                else resource_reference_manifest(spec('books'))['suite_sha256'])
                    return subprocess.CompletedProcess(args, 0, (expected if correct else 'wrong').encode(), b'')
                runner = ResourceReferenceRunner(spec('books'), execute=execute)
                raw = {'status': 'READY', 'image_id': IMAGE, 'run_directory': tmp}
                with patch('critic_agent.sandbox.DockerRunner.check_reference', return_value=raw):
                    result = runner.check_reference()
                self.assertEqual(result['status'], 'READY' if correct else 'ERROR')

    def test_valid_suite_label_with_wrong_resource_label_is_not_ready(self):
        with temporary_directory() as tmp:
            def execute(args, **kwargs):
                value = ('wrong-resource' if 'org.critic.resource-contract-sha256' in ' '.join(args)
                         else resource_reference_manifest(spec('books'))['suite_sha256'])
                return subprocess.CompletedProcess(args, 0, value.encode(), b'')
            runner = ResourceReferenceRunner(spec('books'), execute=execute)
            raw = {'status': 'READY', 'image_id': IMAGE, 'run_directory': tmp}
            with patch('critic_agent.sandbox.DockerRunner.check_reference', return_value=raw):
                result = runner.check_reference()
            self.assertEqual(result['status'], 'ERROR')
            self.assertEqual(result['reason'], 'base_contract_mismatch')

    def test_runner_modes_and_counts(self):
        runner = ResourceReferenceRunner(spec('inventory_items'))
        self.assertEqual(runner.candidate_tests, 57)
        self.assertEqual(runner.reference_tests, 57)
        self.assertEqual(runner.command('x', Path('unused'))[-1], 'evaluation-reference')
        self.assertEqual(runner.command('x', Path('unused'), Path('code.php'))[-1], 'evaluation-candidate')

    def test_build_pins_matching_base_and_rejects_wrong_resource(self):
        for match in (True, False):
            with temporary_directory() as tmp:
                calls = []
                data = spec('books')
                def execute(args, **kwargs):
                    calls.append(args)
                    self.assertEqual(kwargs['timeout'], 45)
                    if 'inspect' in args:
                        base = {'Id': IMAGE, 'Config': {'Entrypoint': ['php', '/opt/critic-resource-entrypoint.php'],
                                'Labels': {'org.critic.resource-contract-sha256': resource_contract(data)['contract_sha256'] if match else 'wrong'}}}
                        return subprocess.CompletedProcess(args, 0, json.dumps(base).encode(), b'')
                    return subprocess.CompletedProcess(args, 0, b'', b'')
                folder = build_resource_reference(data, Path(tmp), execute=execute, timeout=45)
                result = json.loads((folder/'build_result.json').read_text())
                self.assertEqual(result['status'], 'BUILT' if match else 'ERROR')
                if match:
                    pin = next(args for args in calls if 'tag' in args)
                    command = next(args for args in calls if 'build' in args)
                    self.assertEqual(pin[-2], IMAGE)
                    self.assertIn('RESOURCE_IMAGE='+pin[-1], command)
                    self.assertIn(['docker', 'image', 'rm', pin[-1]], calls)
                else:
                    self.assertFalse(any('build' in args for args in calls))

    def test_protected_target_aliases_rejected(self):
        for image in ('docker.io/library/critic-resource-books:dev', 'critic-resource-inventory_items:dev', 'critic-laravel-evaluation:dev'):
            with temporary_directory() as tmp, self.assertRaises(ValueError):
                build_resource_reference(spec('books'), Path(tmp), image=image)

    def test_base_tag_timeout_keeps_error_and_attempts_cleanup(self):
        with temporary_directory() as tmp:
            calls = []
            data = spec('books')
            def execute(args, **kwargs):
                calls.append(args)
                if 'inspect' in args:
                    base = {'Id': IMAGE, 'Config': {'Entrypoint': ['php', '/opt/critic-resource-entrypoint.php'],
                            'Labels': {'org.critic.resource-contract-sha256': resource_contract(data)['contract_sha256']}}}
                    return subprocess.CompletedProcess(args, 0, json.dumps(base).encode(), b'')
                if 'tag' in args:
                    raise subprocess.TimeoutExpired(args, kwargs['timeout'])
                if 'rm' in args:
                    return subprocess.CompletedProcess(args, 1, b'', b'No such image')
                self.fail('Build must not start after tag timeout')
            folder = build_resource_reference(data, Path(tmp), timeout=45, execute=execute)
            result = json.loads((folder/'build_result.json').read_text())
            self.assertEqual(result['reason'], 'timeout')
            self.assertEqual(result['failed_stage'], 'pin_base')
            self.assertIn('timed out', result['detail'])
            pin = next(args for args in calls if 'tag' in args)
            self.assertIn(['docker', 'image', 'rm', pin[-1]], calls)
            self.assertEqual(result['base_cleanup_exit_code'], 1)


class ResourceReferenceCliTests(unittest.TestCase):
    def test_new_command_help(self):
        for command in ('resource-evaluation-build', 'evaluate-resource'):
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as error:
                main([command, '--help'])
            self.assertEqual(error.exception.code, 0)

    def test_evaluate_cli_never_calls_ollama(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            source = source_archive(root, 'books')
            runner = FakeRunner(spec('books'), [evaluated(35, 30), evaluated(35, 35)])
            with patch('critic_agent.cli.ResourceReferenceRunner', return_value=runner), \
                    patch('critic_agent.cli.OllamaClient') as model, redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(['evaluate-resource', str(source), '--output', str(root/'reports')]), 0)
                self.assertEqual(json.loads(output.getvalue())['status'], 'EVALUATED')
                model.assert_not_called()
