"""Post-loop products evaluation. Never generates revisions or model feedback."""
from datetime import datetime, timezone
import base64
import binascii
import hashlib
import json
from pathlib import Path
import re
import subprocess
from uuid import uuid4

from .sandbox import DockerRunner, SandboxError, validate_products_contract
from .spec import load_spec

REFERENCE_TESTS = 33
SUITE_LABEL = 'org.critic.reference-suite-sha256'
ROOT = Path(__file__).resolve().parents[1]


def reference_suite_hash() -> str:
    paths = [ROOT/'evaluation'/name for name in
             ('Dockerfile', 'entrypoint.php', 'phpunit-evaluation.xml', 'suite.json')]
    paths += sorted((ROOT/'evaluation'/'reference-tests').glob('*.php'))
    paths.append(ROOT/'harness'/'runtime.php')
    digest = hashlib.sha256()
    for path in sorted(paths):
        # Normalize authored text so Windows checkout newlines do not change the fingerprint.
        content = path.read_text(encoding='utf-8').replace('\r\n', '\n').encode('utf-8')
        digest.update(path.relative_to(ROOT).as_posix().encode('utf-8')+b'\0')
        digest.update(str(len(content)).encode('ascii')+b'\0'+content)
    return digest.hexdigest()


class ReferenceDockerRunner(DockerRunner):
    reference_mode = 'evaluation-reference'
    candidate_mode = 'evaluation-candidate'
    reference_tests = candidate_tests = REFERENCE_TESTS
    candidate_pass_status = 'PASSED_REFERENCE'
    candidate_fail_status = 'FAILED_REFERENCE'

    def __init__(self, *, image='critic-laravel-evaluation:dev', **kwargs):
        super().__init__(image=image, **kwargs)

    def suite_hash(self):
        return reference_suite_hash()

    def _run(self, candidate, image=None):
        result = super()._run(candidate, image=image)
        if result.get('status') == self.candidate_fail_status and result.get('cleanup_exit_code') != 0:
            result.update(status='ERROR', reason='cleanup_failed')
            self._write_result(Path(result['run_directory']), result)
        if (candidate is not None and result.get('status') == 'ERROR'
                and result.get('reason') == 'missing_report' and result.get('exit_code') == 65
                and result.get('cleanup_exit_code') == 0):
            stdout = (Path(result['run_directory'])/'stdout.log').read_bytes()
            markers = [line.removeprefix(b'CRITIC_INVALID_SYNTAX:') for line in stdout.splitlines()
                       if line.startswith(b'CRITIC_INVALID_SYNTAX:')]
            if len(markers) == 1 and len(markers[0]) <= 21848:
                try:
                    diagnostic = base64.b64decode(markers[0], validate=True)
                except binascii.Error:
                    diagnostic = b''
                if b'Errors parsing /input/controller.php' in diagnostic:
                    result.update(status='UNLOADABLE_CODE', reason='invalid_syntax', executed=False,
                                  diagnostic=diagnostic.decode('utf-8', errors='replace'))
                    self._write_result(Path(result['run_directory']), result)
        return result

    def check_reference(self):
        result = super().check_reference()
        if result['status'] != 'READY':
            return result
        try:
            label = self.execute(['docker', 'image', 'inspect', '--format',
                                  '{{ index .Config.Labels "'+SUITE_LABEL+'" }}', result['image_id']],
                                 capture_output=True, timeout=10, shell=False)
            actual = label.stdout.decode('utf-8', errors='replace').strip()
            expected = self.suite_hash()
            result.update(suite_sha256=actual, expected_suite_sha256=expected)
            if label.returncode or actual != expected:
                result.update(status='ERROR', reason='suite_mismatch')
        except (OSError, subprocess.TimeoutExpired, SandboxError) as exc:
            result.update(status='ERROR', reason='suite_inspection_error', detail=str(exc))
        self._write_result(Path(result['run_directory']), result)
        return result


def _json(path):
    if path.stat().st_size > 8_000_000:
        raise ValueError(f'Arsip terlalu besar: {path.name}')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError(f'Arsip harus berupa object JSON: {path.name}')
    return value


def _write(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))


def _code(source, name, expected_hash):
    path = source/name
    if expected_hash is None:
        if path.exists():
            raise ValueError(f'{name} tersedia tetapi hash percobaan tidak ada.')
        return None
    if not isinstance(expected_hash, str) or not re.fullmatch('[a-f0-9]{64}', expected_hash):
        raise ValueError(f'Hash {name} tidak valid.')
    if not path.is_file() or path.stat().st_size > 1_000_000:
        raise ValueError(f'Arsip menyatakan {name} tersedia, tetapi file hilang/terlalu besar.')
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise ValueError(f'Hash {name} berbeda dengan riwayat loop.')
    return data


def _proportion(numerator, denominator):
    return {'numerator': numerator, 'denominator': denominator,
            'percent': numerator/denominator*100 if denominator else None}


def _valid_result(raw, image_id, expected_tests=REFERENCE_TESTS):
    summary = raw.get('summary', {})
    counters = [summary.get(key) for key in ('passed', 'failure', 'error', 'skipped')]
    if (raw.get('image_id') != image_id or summary.get('total') != expected_tests
            or any(type(n) is not int or n < 0 for n in counters)
            or sum(counters) != expected_tests or summary['skipped'] != 0):
        return False
    expected = 'PASSED_REFERENCE' if summary['passed'] == expected_tests else 'FAILED_REFERENCE'
    return raw.get('status') == expected


def evaluate_products(loop_directory: Path, output_root: Path, runner) -> Path:
    return _evaluate_pair(loop_directory, output_root, runner, expected_tests=REFERENCE_TESTS,
                          suite_sha256=reference_suite_hash(), validate_contract=validate_products_contract)


def _evaluate_pair(loop_directory, output_root, runner, *, expected_tests, suite_sha256, validate_contract):
    source = Path(loop_directory).resolve(strict=True)
    manifest = _json(source/'run_manifest.json')
    history = _json(source/'history.json')
    status = manifest.get('status')
    if status not in ('LOLOS', 'BELUM LOLOS') or history.get('status') != status:
        raise ValueError('Hanya arsip loop selesai LOLOS/BELUM LOLOS yang dapat dievaluasi; ERROR dikecualikan.')
    spec = load_spec(source/'spec.json')
    validate_contract(spec)
    if manifest.get('spec_sha256') is not None:
        if hashlib.sha256((source/'spec.json').read_bytes()).hexdigest() != manifest['spec_sha256']:
            raise ValueError('Hash spesifikasi arsip berubah.')
    attempts = history.get('attempts')
    if (not isinstance(attempts, list) or not attempts
            or any(not isinstance(item, dict) or item.get('iteration') != i for i, item in enumerate(attempts))):
        raise ValueError('Riwayat percobaan tidak lengkap/berurutan.')
    final_hash = attempts[-1].get('code_sha256')
    if type(manifest.get('final_code_available')) is not bool or manifest['final_code_available'] != (final_hash is not None):
        raise ValueError('Ketersediaan kode akhir tidak cocok dengan riwayat.')
    if status == 'LOLOS' and final_hash is None:
        raise ValueError('Status LOLOS tanpa kode akhir tidak valid.')
    versions = {'initial': _code(source, 'initial_controller.php', attempts[0].get('code_sha256')),
                'final': _code(source, 'final_controller.php', final_hash)}
    folder = Path(output_root)/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_evaluation_'+uuid4().hex)
    folder.mkdir(parents=True, exist_ok=False)
    _write(folder/'spec.json', spec)
    _write(folder/'source_manifest.json', manifest)
    _write(folder/'source_history.json', history)
    for position, content in versions.items():
        if content is not None:
            (folder/(position+'_controller.php')).write_bytes(content)
    result = {'status': 'ERROR', 'reason': 'incomplete_evaluation', 'source_directory': str(source),
              'source_run_id': manifest.get('run_id'), 'source_status': status,
              'created_at': datetime.now(timezone.utc).isoformat(),
              'suite_sha256': suite_sha256, 'suite_stage': 'development',
              'expected_tests': expected_tests, 'initial': None, 'final': None,
              'uplift_pp': None, 'repair': None, 'regression': None}
    try:
        readiness = runner.check_reference()
        result['readiness'] = readiness
        if (readiness.get('status') != 'READY' or readiness.get('suite_sha256') != result['suite_sha256']
                or not re.fullmatch(r'sha256:[a-f0-9]{64}', readiness.get('image_id', ''))):
            result['reason'] = 'reference_not_ready'
            return folder
        result['image_id'] = runner.image = readiness['image_id']
        for position, content in versions.items():
            if content is None:
                raw = {'status': 'UNAVAILABLE_CODE', 'reason': 'source_declares_no_code', 'executed': False}
                passed = 0
            else:
                raw = runner.check_candidate(folder/(position+'_controller.php'))
                unloadable = (raw.get('status') == 'UNLOADABLE_CODE' and raw.get('reason') == 'invalid_syntax'
                              and raw.get('executed') is False and raw.get('image_id') == result['image_id'])
                if not unloadable and not _valid_result(raw, result['image_id'], expected_tests):
                    result[position] = {'status': 'ERROR', 'runner_result': raw}
                    result['reason'] = 'invalid_or_failed_evaluation_run'
                    return folder
                passed = 0 if unloadable else raw['summary']['passed']
            result[position] = {'status': raw['status'], 'passed': passed, 'total': expected_tests,
                                'pass_rate': passed/expected_tests*100, 'runner_result': raw,
                                'code_sha256': hashlib.sha256(content).hexdigest() if content is not None else None}
        before, after = result['initial']['passed'], result['final']['passed']
        result.update(status='EVALUATED', reason='pair_evaluated',
                      uplift_pp=result['final']['pass_rate']-result['initial']['pass_rate'],
                      repair=_proportion(int(before < expected_tests and after == expected_tests), int(before < expected_tests)),
                      regression=_proportion(int(before == expected_tests and after < expected_tests), int(before == expected_tests)))
    except (SandboxError, OSError, subprocess.TimeoutExpired) as exc:
        result.update(reason='environment_error', detail=str(exc))
    finally:
        _write(folder/'evaluation_result.json', result)
    return folder
