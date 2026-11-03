"""Read-only prerequisite checks; does not download models or start services."""
import json
import platform
import shutil
import subprocess
import sys
from urllib.error import URLError
from urllib.request import urlopen


def doctor() -> dict:
    checks = {'python': {'ok': sys.version_info >= (3, 11), 'detail': platform.python_version()}}
    for tool, args in [('php', ['--version']), ('docker', ['info', '--format', '{{json .ServerVersion}}'])]:
        binary = shutil.which(tool)
        if not binary:
            checks[tool] = {'ok': False, 'detail': f'{tool} belum ditemukan di PATH.'}
            continue
        try:
            result = subprocess.run([binary, *args], capture_output=True, timeout=8)
            detail = (result.stdout if result.returncode == 0 else result.stderr).decode('utf-8', errors='replace').strip()
            checks[tool] = {'ok': result.returncode == 0, 'detail': detail[:500]}
        except (OSError, subprocess.TimeoutExpired) as exc:
            checks[tool] = {'ok': False, 'detail': str(exc)}
    try:
        with urlopen('http://127.0.0.1:11434/api/tags', timeout=2) as response:
            data = json.load(response)
        models = [m['name'] for m in data.get('models', []) if isinstance(m, dict) and isinstance(m.get('name'), str)]
        checks['ollama'] = {'ok': True, 'detail': models}
        checks['qwen'] = {'ok': 'qwen2.5:7b-instruct' in models, 'detail': 'Diperlukan qwen2.5:7b-instruct; digest/kuantisasi diverifikasi saat pilot.'}
    except (OSError, URLError, ValueError, TypeError, AttributeError) as exc:
        checks['ollama'] = {'ok': False, 'detail': str(exc)}
        checks['qwen'] = {'ok': False, 'detail': 'Model belum dapat diperiksa.'}
    return {'ready': all(c['ok'] for c in checks.values()), 'checks': checks}
