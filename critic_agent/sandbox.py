"""Docker-only candidate execution for the fixed products harness.

JUnit and stdout are observations from the candidate's process, not cryptographic
proof against a controller deliberately tampering with its own test process.
"""
from datetime import datetime, timezone
import base64
import binascii
import hashlib
import json
import math
from pathlib import Path
import shutil
import re
import subprocess
from uuid import uuid4
import xml.etree.ElementTree as ET
from .process import bounded_run, OutputLimitError
from .spec import load_spec, validate_spec, SpecError


class SandboxError(RuntimeError):
    pass


def validate_products_contract(spec):
    validate_spec(spec)
    supported = load_spec(Path(__file__).resolve().parents[1]/'harness'/'products-contract.json')
    if any(spec[key] != supported[key] for key in ('resource', 'model', 'controller', 'fields', 'operations')):
        raise SpecError('Harness contoh ini hanya mendukung kontrak products yang disediakan; variasi lain belum tersedia.')


def parse_junit(content: bytes) -> dict:
    if len(content) > 4_000_000 or b'<!DOCTYPE' in content.upper() or b'<!ENTITY' in content.upper():
        raise SandboxError('Laporan XML terlalu besar atau mengandung deklarasi yang tidak didukung.')
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise SandboxError(f'Laporan JUnit tidak valid: {exc}') from exc
    if root.tag not in ('testsuites', 'testsuite'):
        raise SandboxError('Root laporan bukan testsuite/testsuites.')
    cases, identities = [], set()
    for node in root.iter('testcase'):
        name, cls = node.get('name'), node.get('classname', node.get('class', ''))
        if not name or (cls, name) in identities:
            raise SandboxError('Nama testcase kosong atau duplikat.')
        identities.add((cls, name))
        outcome, evidence = 'passed', ''
        for tag in ('error', 'failure', 'skipped'):
            child = node.find(tag)
            if child is not None:
                outcome = tag
                evidence = child.get('message', '')+'\n'+''.join(child.itertext())
                break
        cases.append({'name': name, 'class': cls, 'outcome': outcome, 'evidence': evidence[:12000]})
    if not cases:
        raise SandboxError('Laporan tidak berisi testcase; tidak boleh dinyatakan lulus.')
    for suite in root.iter():
        if suite.tag not in ('testsuite', 'testsuites'):
            continue
        descendants = list(suite.iter('testcase'))
        expected = {'tests': len(descendants)}
        for attr, tag in [('failures', 'failure'), ('errors', 'error'), ('skipped', 'skipped')]:
            expected[attr] = sum(n.find(tag) is not None for n in descendants)
        for attr, number in expected.items():
            if attr in suite.attrib and suite.get(attr) != str(number):
                raise SandboxError(f'Counter JUnit {attr} tidak sesuai testcase.')
    counts = {label: sum(c['outcome'] == label for c in cases) for label in ('passed', 'failure', 'error', 'skipped')}
    return {'status': 'PASSED' if counts['passed'] == len(cases) else 'FAILED',
            'total': len(cases), **counts, 'cases': cases}


class DockerRunner:
    reference_mode = 'reference'
    candidate_mode = 'candidate'
    reference_tests = 21
    candidate_tests = 14
    candidate_pass_status = 'PASSED_INTERNAL'
    candidate_fail_status = 'FAILED_INTERNAL'

    def __init__(self, *, image='critic-laravel:dev', output_root=Path('runs/harness'), timeout=120,
                 execute=bounded_run):
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('Timeout harus positif.')
        if not image or image.startswith('-') or any(c.isspace() for c in image):
            raise ValueError('Nama image Docker tidak valid.')
        self.image, self.output_root, self.timeout, self.execute = image, Path(output_root), timeout, execute

    def command(self, name: str, reports: Path, candidate: Path | None = None) -> list[str]:
        command = ['docker', 'run', '--name', name, '--pull=never', '--network=none', '--read-only',
                   '--log-driver=none',
                   '--cap-drop=ALL', '--security-opt=no-new-privileges', '--user=10001:10001',
                   '--memory=768m', '--cpus=1', '--pids-limit=128',
                   '--tmpfs', '/work:rw,nosuid,nodev,size=512m,mode=1777',
                   '--tmpfs', '/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777']
        if candidate is not None:
            command += ['--mount', f'type=bind,src={candidate.resolve()},dst=/input/controller.php,readonly']
        command += [self.image, self.candidate_mode if candidate is not None else self.reference_mode]
        return command

    def check_reference(self) -> dict:
        return self._run(None)

    def check_candidate(self, candidate: Path) -> dict:
        candidate = Path(candidate).resolve(strict=True)
        if not candidate.is_file() or candidate.stat().st_size > 1_000_000 or ',' in str(candidate):
            raise SandboxError('Kandidat harus berupa file PHP maksimal 1 MB dan path tanpa koma.')
        ready = self.check_reference()
        if ready['status'] != 'READY':
            return {'status': 'ERROR', 'reason': 'reference_not_ready', 'readiness': ready}
        result = self._run(candidate, image=ready['image_id'])
        result['readiness_directory'] = ready['run_directory']
        if 'run_directory' in result:
            self._write_result(Path(result['run_directory']), result)
        return result

    @staticmethod
    def _write_result(folder, result):
        (folder/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

    def _run(self, candidate, image=None) -> dict:
        if not shutil.which('docker'):
            raise SandboxError('Docker belum ditemukan. Pasang/aktifkan Docker Desktop; tidak ada fallback eksekusi kandidat di host.')
        run_id = 'critic-'+uuid4().hex
        folder = self.output_root/run_id
        folder.mkdir(parents=True, exist_ok=False, mode=0o700)
        reports = folder/'reports'
        reports.mkdir()
        if ',' in str(reports.resolve()):
            raise SandboxError('Path laporan Docker tidak boleh mengandung koma.')
        # Freeze the input used by the runner; never let the user path change mid-run.
        if candidate is not None:
            snapshot = folder/'candidate.php'
            snapshot.write_bytes(candidate.read_bytes())
            candidate = snapshot
        command = self.command(run_id, reports, candidate)
        result = {'status': 'ERROR', 'reason': 'incomplete_run', 'run_directory': str(folder.resolve()),
                  'created_at': datetime.now(timezone.utc).isoformat(), 'image': self.image,
                  'mode': 'candidate' if candidate else 'reference', 'command': command,
                  'timeout_seconds': self.timeout, 'expected_tests': self.candidate_tests if candidate else self.reference_tests}
        if candidate:
            result['candidate_sha256'] = hashlib.sha256(candidate.read_bytes()).hexdigest()
        try:
            identity = self.execute(['docker', 'image', 'inspect', '--format', '{{.Id}}', image or self.image],
                                    capture_output=True, timeout=10, shell=False)
            if identity.returncode:
                result.update(reason='image_unavailable', detail=identity.stderr.decode('utf-8', errors='replace')[:4000])
                return result
            result['image_id'] = identity.stdout.decode('utf-8', errors='replace').strip()
            if not re.fullmatch(r'sha256:[a-f0-9]{64}', result['image_id']):
                raise SandboxError('Docker tidak mengembalikan image ID yang valid.')
            command[-2] = result['image_id']
            process = self.execute(command, capture_output=True, timeout=self.timeout, shell=False)
            (folder/'stdout.log').write_bytes(process.stdout or b'')
            (folder/'stderr.log').write_bytes(process.stderr or b'')
            result['exit_code'] = process.returncode
            report_path = reports/'junit.xml'
            records = [line[len(b'CRITIC_JUNIT_B64:'):] for line in (process.stdout or b'').splitlines()
                       if line.startswith(b'CRITIC_JUNIT_B64:')]
            if process.returncode in (125, 126, 127):
                result['reason'] = 'docker_error'
            elif not records:
                result['reason'] = 'missing_report'
            else:
                if len(records) != 1 or len(records[0]) > 5_333_336:
                    raise SandboxError('Envelope laporan JUnit ambigu atau terlalu besar.')
                try:
                    xml = base64.b64decode(records[0], validate=True)
                except binascii.Error as exc:
                    raise SandboxError('Encoding laporan tidak valid.') from exc
                summary = parse_junit(xml)
                report_path.write_bytes(xml)
                result['summary'] = summary
                if summary['total'] != result['expected_tests']:
                    result['reason'] = 'unexpected_test_count'
                elif process.returncode == 0 and summary['status'] == 'PASSED':
                    result.update(status=self.candidate_pass_status if candidate else 'READY', reason='all_tests_passed')
                else:
                    result.update(status=self.candidate_fail_status if candidate else 'ERROR', reason='tests_failed')
        except OutputLimitError as exc:
            result['reason'] = 'output_limit'
            (folder/'stdout.log').write_bytes(exc.output)
            (folder/'stderr.log').write_bytes(exc.stderr)
        except subprocess.TimeoutExpired as exc:
            result['reason'] = 'timeout'
            (folder/'stdout.log').write_bytes(exc.output or b'')
            (folder/'stderr.log').write_bytes(exc.stderr or b'')
        except (OSError, SandboxError) as exc:
            result.update(reason='runner_error', detail=str(exc))
        finally:
            try:
                cleanup = self.execute(['docker', 'rm', '--force', run_id], capture_output=True, timeout=10, shell=False)
                result['cleanup_exit_code'] = cleanup.returncode
                if cleanup.returncode:
                    result['cleanup_detail'] = cleanup.stderr.decode('utf-8', errors='replace')[:2000]
                    if result['status'] in ('READY', self.candidate_pass_status):
                        result.update(status='ERROR', reason='cleanup_failed')
            except (OSError, subprocess.TimeoutExpired) as exc:
                result['cleanup_detail'] = str(exc)
                if result['status'] in ('READY', self.candidate_pass_status):
                    result.update(status='ERROR', reason='cleanup_failed')
            self._write_result(folder, result)
        return result
