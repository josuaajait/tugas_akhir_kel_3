"""Independent, hand-authored development evaluation for books and inventory.

Only the reviewed profile contracts are supported. No model or feedback calls.
"""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from uuid import uuid4

from . import __version__
from .reference import ReferenceDockerRunner, SUITE_LABEL, _evaluate_pair, _json, _write
from .resources import resource_contract, _canonical_image_name
from .sandbox import DockerRunner, SandboxError
from .spec import load_spec

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT/'evaluation'/'resource-reference'
RESOURCE_LABEL = 'org.critic.resource-contract-sha256'
SUPPORTED = ('books', 'inventory_items')


def resource_reference_manifest(spec):
    base_contract = resource_contract(spec)
    resource = spec['resource']
    if resource not in SUPPORTED:
        raise ValueError('Evaluator resource hanya mendukung profil books dan inventory_items; products memakai evaluate-products.')
    profile_path = PACKAGE/'profiles'/(resource+'.json')
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    if profile['spec'] != spec:
        raise ValueError('Spesifikasi berbeda dari kontrak profil acuan; buat/tinjau profil baru sebelum mengevaluasi.')
    expected_tests = 11+2*len(profile['invalid'])+2*len(profile['valid'])
    digest = hashlib.sha256(json.dumps(profile, sort_keys=True, separators=(',', ':')).encode())
    digest.update(__version__.encode())
    digest.update(base_contract['contract_sha256'].encode())
    for path in [Path(__file__), PACKAGE/'ResourceReferenceTest.php', PACKAGE/'phpunit.xml',
                 PACKAGE/'Dockerfile', ROOT/'evaluation'/'entrypoint.php']:
        digest.update(path.relative_to(ROOT).as_posix().encode()+b'\0')
        digest.update(path.read_text(encoding='utf-8').replace('\r\n', '\n').encode()+b'\0')
    return {'spec': copy.deepcopy(spec), 'profile': profile, 'suite_id': profile['suite_id'],
            'prototype_version': __version__,
            'expected_tests': expected_tests, 'suite_sha256': digest.hexdigest(),
            'resource_contract_sha256': base_contract['contract_sha256'], 'stage': 'development'}


def render_resource_reference(spec):
    meta = resource_reference_manifest(spec)
    return {'Dockerfile': (PACKAGE/'Dockerfile').read_text(encoding='utf-8'),
            'phpunit.xml': (PACKAGE/'phpunit.xml').read_text(encoding='utf-8'),
            'ResourceReferenceTest.php': (PACKAGE/'ResourceReferenceTest.php').read_text(encoding='utf-8'),
            'entrypoint.php': (ROOT/'evaluation'/'entrypoint.php').read_text(encoding='utf-8'),
            'profile.json': json.dumps(meta['profile'], indent=2)+'\n'}


def build_resource_reference(spec, output_root, *, image=None, base_image=None, timeout=600,
                             execute=subprocess.run):
    meta = resource_reference_manifest(spec)
    resource = spec['resource']
    image = image or 'critic-resource-'+resource+'-evaluation:dev'
    base_image = base_image or 'critic-resource-'+resource+':dev'
    DockerRunner(image=image, timeout=timeout)
    DockerRunner(image=base_image, timeout=timeout)
    protected = [base_image, 'critic-laravel:dev', 'critic-laravel-evaluation:dev']
    protected += ['critic-resource-'+name+':dev' for name in SUPPORTED]
    if _canonical_image_name(image) in {_canonical_image_name(name) for name in protected}:
        raise ValueError('Image evaluator harus terpisah dari base/internal/products evaluator.')
    folder = Path(output_root)/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex)
    context = folder/'context'
    context.mkdir(parents=True, exist_ok=False)
    files = render_resource_reference(spec)
    for name, source in files.items():
        (context/name).write_bytes(source.encode('utf-8'))
    _write(folder/'suite_manifest.json', meta)
    result = {'status': 'ERROR', 'stage': 'inspect_base', 'timeout_seconds': timeout,
              'image': image, 'base_image': base_image, 'context': str(context.resolve()),
              'suite_sha256': meta['suite_sha256'], 'expected_tests': meta['expected_tests'],
              'resource_contract_sha256': meta['resource_contract_sha256'],
              'files': {name: hashlib.sha256(source.encode()).hexdigest() for name, source in files.items()}}
    temporary_base = None
    try:
        inspected = execute(['docker', 'image', 'inspect', '--format', '{{json .}}', base_image],
                            capture_output=True, timeout=timeout, shell=False)
        if inspected.returncode:
            raise SandboxError('Base resource tidak tersedia: '+(inspected.stderr or b'').decode('utf-8', errors='replace')[:2000])
        try:
            base = json.loads(inspected.stdout)
        except (ValueError, TypeError) as exc:
            raise SandboxError('Metadata base resource tidak valid.') from exc
        config = base.get('Config', {}) if isinstance(base, dict) else {}
        labels = config.get('Labels') or {}
        if (config.get('Entrypoint') != ['php', '/opt/critic-resource-entrypoint.php']
                or not isinstance(labels, dict) or SUITE_LABEL in labels
                or labels.get(RESOURCE_LABEL) != meta['resource_contract_sha256']):
            raise SandboxError('Base harus image internal resource dengan kontrak yang sama, bukan evaluator atau resource lain.')
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', base.get('Id', '')):
            raise SandboxError('Image ID base tidak valid.')
        result['base_image_id'] = base['Id']
        result['stage'] = 'lint_suite'
        for name, source in files.items():
            if name.endswith('.php'):
                lint = subprocess.run(['php', '-n', '-l'], input=source.encode(), capture_output=True, timeout=15, shell=False)
                if lint.returncode:
                    raise SandboxError('PHP suite gagal lint: '+(lint.stdout+lint.stderr).decode('utf-8', errors='replace'))
        result['stage'] = 'pin_base'
        temporary_base = 'critic-evaluation-base-'+uuid4().hex+':dev'
        pin = ['docker', 'image', 'tag', base['Id'], temporary_base]
        result.update(base_pin_command=pin, base_build_reference=temporary_base)
        tagged = execute(pin, capture_output=True, timeout=timeout, shell=False)
        if tagged.returncode:
            raise SandboxError('Base resource gagal dipertahankan untuk build.')
        result['stage'] = 'build'
        command = ['docker', 'build', '--tag', image, '--build-arg', 'RESOURCE_IMAGE='+temporary_base,
                   '--build-arg', 'SUITE_SHA256='+meta['suite_sha256'], str(context.resolve())]
        result['command'] = command
        built = execute(command, timeout=timeout, shell=False)
        result['exit_code'] = built.returncode
        if built.returncode:
            result.update(reason='docker_build_failed', failed_stage='build')
        else:
            result.update(status='BUILT', stage='completed', reason='build_completed')
    except subprocess.TimeoutExpired as exc:
        result.update(reason='timeout', failed_stage=result['stage'], detail=str(exc))
    except (OSError, SandboxError) as exc:
        result.update(reason='build_error', failed_stage=result['stage'], detail=str(exc))
    finally:
        if temporary_base is not None:
            cleanup = ['docker', 'image', 'rm', temporary_base]
            result['base_cleanup_command'] = cleanup
            try:
                cleaned = execute(cleanup, capture_output=True, timeout=timeout, shell=False)
                result['base_cleanup_exit_code'] = cleaned.returncode
                if cleaned.returncode:
                    result['base_cleanup_detail'] = (cleaned.stderr or b'').decode('utf-8', errors='replace')[:2000]
                    if result['status'] == 'BUILT':
                        result.update(status='ERROR', reason='cleanup_failed', failed_stage='cleanup_base')
            except (OSError, subprocess.TimeoutExpired) as exc:
                result['base_cleanup_detail'] = str(exc)
                if result['status'] == 'BUILT':
                    result.update(status='ERROR', reason='cleanup_failed', failed_stage='cleanup_base')
        _write(folder/'build_result.json', result)
    return folder


class ResourceReferenceRunner(ReferenceDockerRunner):
    def __init__(self, spec, *, image=None, **kwargs):
        meta = resource_reference_manifest(spec)
        self.spec = copy.deepcopy(spec)
        self.expected_suite_sha256 = meta['suite_sha256']
        self.candidate_tests = self.reference_tests = meta['expected_tests']
        self.resource_contract_sha256 = meta['resource_contract_sha256']
        super().__init__(image=image or 'critic-resource-'+spec['resource']+'-evaluation:dev', **kwargs)

    def suite_hash(self):
        return resource_reference_manifest(self.spec)['suite_sha256']

    def check_reference(self):
        result = super().check_reference()
        if result['status'] != 'READY':
            return result
        try:
            inspected = self.execute(['docker', 'image', 'inspect', '--format',
                                      '{{ index .Config.Labels "'+RESOURCE_LABEL+'" }}', result['image_id']],
                                     capture_output=True, timeout=self.timeout, shell=False)
            actual = inspected.stdout.decode('utf-8', errors='replace').strip()
            result.update(resource_contract_sha256=actual,
                          expected_resource_contract_sha256=self.resource_contract_sha256)
            if inspected.returncode or actual != self.resource_contract_sha256:
                result.update(status='ERROR', reason='base_contract_mismatch')
        except (OSError, subprocess.TimeoutExpired, SandboxError) as exc:
            result.update(status='ERROR', reason='base_contract_inspection_error', detail=str(exc))
        self._write_result(Path(result['run_directory']), result)
        return result


def evaluate_resource(loop_directory, output_root, runner):
    source_spec = load_spec(Path(loop_directory)/'spec.json')
    meta = resource_reference_manifest(source_spec)
    if (getattr(runner, 'spec', None) != source_spec
            or getattr(runner, 'candidate_tests', None) != meta['expected_tests']
            or getattr(runner, 'expected_suite_sha256', None) != meta['suite_sha256']):
        raise ValueError('Runner evaluator harus sesuai spesifikasi, suite dan jumlah kasus arsip.')
    def validate_contract(current):
        if current != source_spec:
            raise ValueError('Spesifikasi arsip berubah sebelum evaluasi.')
        resource_reference_manifest(current)
    folder = _evaluate_pair(loop_directory, output_root, runner, expected_tests=meta['expected_tests'],
                            suite_sha256=meta['suite_sha256'], validate_contract=validate_contract)
    result = _json(folder/'evaluation_result.json')
    result.update(suite_id=meta['suite_id'], resource=source_spec['resource'],
                  evaluator_version=__version__,
                  resource_contract_sha256=meta['resource_contract_sha256'])
    _write(folder/'evaluation_result.json', result)
    _write(folder/'suite_manifest.json', meta)
    return folder
