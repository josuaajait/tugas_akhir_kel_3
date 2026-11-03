"""Generation archives preserve failures as well as successful extraction."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
from uuid import uuid4

from . import __version__
from .ollama import ModelError, OllamaClient
from .prompts import build_prompt
from .spec import validate_spec


class ExtractionError(ValueError):
    pass


def extract_php(response: str) -> str:
    fences = list(re.finditer(r'^```([^\r\n]*)\r?\n(.*?)^```[ \t]*\r?(?:\n|$)', response, re.M | re.S))
    if fences:
        if len(fences) != 1 or len(re.findall(r'^```', response, re.M)) != 2:
            raise ExtractionError('Respons berisi lebih dari satu blok atau fence tidak lengkap.')
        match = fences[0]
        if '<?php' in response[:match.start()]+response[match.end():]:
            raise ExtractionError('Ada kandidat PHP lain di luar blok kode.')
        language, code = match.group(1), match.group(2)
        if language.strip().lower() not in ('php', ''):
            raise ExtractionError('Blok keluaran bukan PHP.')
    else:
        code = response
    if not code.startswith('<?php') or (len(code) > 5 and not code[5].isspace()):
        raise ExtractionError('Keluaran harus dimulai dengan <?php.')
    if '?>' in code or '\x00' in code:
        raise ExtractionError('Tag penutup PHP dan byte NUL tidak didukung kontrak satu berkas.')
    return code


def _json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def generate(spec: dict, output_root: Path, client: OllamaClient) -> Path:
    validate_spec(spec)
    prompt = build_prompt(spec)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex
    folder = Path(output_root)/run_id
    folder.mkdir(parents=True, exist_ok=False)
    manifest = {'run_id': run_id, 'created_at': datetime.now(timezone.utc).isoformat(),
                'prototype_version': __version__, 'stage': 'generation_foundation',
                'spec_id': spec['spec_id'], 'spec_version': spec['spec_version'],
                'model': client.model, 'endpoint': client.base_url, 'options': client.options,
                'timeout_seconds': client.timeout, 'max_transport_attempts': 2,
                'environment': {'python': platform.python_version(), 'platform': platform.platform()},
                'dynamic_tests': 'not_run', 'status': 'ERROR', 'stop_reason': 'incomplete_generation'}
    _json(folder/'spec.json', spec)
    (folder/'prompt.txt').write_bytes(prompt.encode('utf-8'))
    manifest['prompt_sha256'] = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
    manifest['spec_sha256'] = hashlib.sha256((folder/'spec.json').read_bytes()).hexdigest()
    _json(folder/'run_manifest.json', manifest)
    try:
        result = client.generate(prompt)
        _json(folder/'response.json', result)
        (folder/'response.txt').write_bytes(result['response'].encode('utf-8'))
        code = extract_php(result['response'])
        code_bytes = code.encode('utf-8')
        (folder/'initial_controller.php').write_bytes(code_bytes)
        manifest.update(status='AWAITING_DYNAMIC_TESTS', stop_reason='generation_only',
                        code_sha256=hashlib.sha256(code_bytes).hexdigest())
    except ExtractionError as exc:
        manifest.update(status='FORMAT_FAIL', stop_reason='invalid_output', error=str(exc))
    except ModelError as exc:
        if exc.response is not None:
            _json(folder/'response.json', exc.response)
            if isinstance(exc.response, dict) and isinstance(exc.response.get('response'), str):
                (folder/'response.txt').write_bytes(exc.response['response'].encode('utf-8'))
        manifest.update(status='ERROR', stop_reason='model_error', error=str(exc))
    finally:
        _json(folder/'run_manifest.json', manifest)
    return folder
