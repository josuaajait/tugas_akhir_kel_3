"""Observations attached to new archives for FR-16."""
import hashlib
import os
from pathlib import Path
import platform
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def _tree_hash(paths):
    digest = hashlib.sha256()
    for path in sorted(paths):
        content = path.read_bytes().replace(b'\r\n', b'\n')
        digest.update(path.relative_to(ROOT).as_posix().encode() + b'\0')
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()


def _memory_bytes():
    try:
        if os.name == 'nt':
            import ctypes
            value = ctypes.c_ulonglong()
            if ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(value)):
                return value.value * 1024
            return None
        return os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
    except (OSError, ValueError, AttributeError):
        return None


def _probe(command):
    try:
        result = subprocess.run(command, capture_output=True, timeout=3, check=False)
        if result.returncode == 0:
            return result.stdout.decode('utf-8', errors='replace').strip() or None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def run_provenance(client, runner=None, resource_hash=None):
    capture_identity = getattr(client, 'model_identity', None)
    identity = capture_identity() if capture_identity else {'status': 'unavailable', 'issues': ['client_unsupported']}
    live = getattr(client, 'metadata_transport', None) is not None
    result = {
        'schema_version': '1.0',
        'prototype_source_sha256': _tree_hash((ROOT/'critic_agent').glob('*.py')),
        'model_identity': identity,
        'hardware': {'architecture': platform.machine(), 'cpu': platform.processor() or os.environ.get('PROCESSOR_IDENTIFIER'),
                     'logical_cpus': os.cpu_count(), 'ram_bytes': _memory_bytes(),
                     'nvidia_gpu_name_and_vram_mib': _probe(['nvidia-smi', '--query-gpu=name,memory.total',
                                                           '--format=csv,noheader,nounits']) if live else None},
        'tools': {'php_cli': _probe(['php', '--version']) if live else None,
                  'docker_server_version': _probe(['docker', 'info', '--format', '{{.ServerVersion}}'])
                  if live and runner is not None else None},
    }
    if runner is not None:
        tests = {'configured_image': getattr(runner, 'image', None),
                 'test_timeout_seconds': getattr(runner, 'timeout', None),
                 'resource_contract_sha256': resource_hash}
        if resource_hash is None:
            harness = ROOT/'harness'
            paths = [harness/'entrypoint.php', harness/'runtime.php', harness/'Dockerfile',
                     harness/'laravel'/'phpunit.xml', harness/'laravel'/'composer.lock',
                     *sorted((harness/'laravel'/'tests'/'Feature').glob('Products*.php'))]
            tests['local_products_suite_sha256'] = _tree_hash(paths) if all(path.is_file() for path in paths) else None
        result['tests'] = tests
    return result


def model_request(client):
    events = getattr(client, 'last_transport_attempts', None)
    return {'options': dict(client.options), 'timeout_seconds': client.timeout,
            'transport_attempts': list(events) if events else None}
