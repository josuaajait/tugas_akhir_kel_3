"""Products verification and revision loop, with immutable per-attempt evidence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time
from uuid import uuid4

from . import __version__
from .feedback import build_feedback, collect_findings, revision_prompt
from .generation import extract_php, ExtractionError
from .ollama import ModelError
from .prompts import build_prompt
from .sandbox import SandboxError, validate_products_contract
from .spec import load_spec
from .static import analyze, StaticEnvironmentError
from .resources import resource_contract


def _write_json(path, data):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_bytes((json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    temporary.replace(path)


def _initial_archive(source, spec, client):
    source = Path(source).resolve(strict=True)
    manifest = json.loads((source/'run_manifest.json').read_text(encoding='utf-8-sig'))
    if load_spec(source/'spec.json') != spec:
        raise ValueError('Spesifikasi arsip awal berbeda dengan spesifikasi loop.')
    data = (source/'initial_controller.php').read_bytes()
    if hashlib.sha256(data).hexdigest() != manifest.get('code_sha256'):
        raise ValueError('Hash kode awal tidak cocok dengan arsip generasi.')
    if manifest.get('model') != client.model or manifest.get('options') != client.options:
        raise ValueError('Model/options revisi harus sama dengan konfigurasi arsip awal.')
    return source, manifest, data.decode('utf-8')


def run_products(spec, output_root, client, runner, *, initial_run=None,
                 max_revisions=3, static_analyzer=analyze):
    validate_products_contract(spec)
    return _run_loop(spec, output_root, client, runner, initial_run=initial_run,
                     max_revisions=max_revisions, static_analyzer=static_analyzer,
                     expected_tests=14, stage='products_revision_loop')


def run_resource(spec, output_root, client, runner, *, initial_run=None,
                 max_revisions=3, static_analyzer=analyze):
    contract = resource_contract(spec)
    if (getattr(runner, 'spec', None) != spec
            or getattr(runner, 'contract_sha256', None) != contract['contract_sha256']
            or getattr(runner, 'candidate_tests', None) != contract['internal_tests']):
        raise ValueError('Runner harus terikat pada spesifikasi, template, dan jumlah test resource yang sama.')
    return _run_loop(spec, output_root, client, runner, initial_run=initial_run,
                     max_revisions=max_revisions, static_analyzer=static_analyzer,
                     expected_tests=contract['internal_tests'], stage='resource_revision_loop',
                     contract_sha256=contract['contract_sha256'])


def _run_loop(spec, output_root, client, runner, *, initial_run, max_revisions, static_analyzer,
              expected_tests, stage, contract_sha256=None):
    if type(max_revisions) is not int or not 0 <= max_revisions <= 3:
        raise ValueError('Batas revisi harus bilangan bulat 0–3.')
    imported = _initial_archive(initial_run, spec, client) if initial_run else None
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_loop_'+uuid4().hex
    folder = Path(output_root)/run_id
    (folder/'attempts').mkdir(parents=True, exist_ok=False)
    history = {'run_id': run_id, 'status': 'RUNNING', 'stop_reason': None,
               'revision_count': 0, 'attempts': []}
    manifest = {'run_id': run_id, 'stage': stage, 'created_at': datetime.now(timezone.utc).isoformat(),
                'prototype_version': __version__, 'spec_id': spec['spec_id'], 'spec_version': spec['spec_version'],
                'model': client.model, 'endpoint': client.base_url, 'options': dict(client.options),
                'model_timeout_seconds': client.timeout, 'max_revisions': max_revisions,
                'environment': {'python': platform.python_version(), 'platform': platform.platform()},
                'status': 'RUNNING', 'initial_source': str(imported[0]) if imported else None,
                'expected_internal_tests': expected_tests}
    if contract_sha256 is not None:
        manifest['resource_contract_sha256'] = contract_sha256
    _write_json(folder/'spec.json', spec)
    manifest['spec_sha256'] = hashlib.sha256((folder/'spec.json').read_bytes()).hexdigest()
    if imported:
        _write_json(folder/'initial_source_manifest.json', imported[1])
    _write_json(folder/'run_manifest.json', manifest)
    _write_json(folder/'history.json', history)
    (folder/'run.log').write_text('Resource revision loop started.\n', encoding='utf-8')
    previous_code = None
    previous_output = ''
    feedback = None
    final_code = None
    image_id = None
    for iteration in range(max_revisions+1):
        started = time.monotonic()
        attempt_folder = folder/'attempts'/str(iteration)
        attempt_folder.mkdir()
        entry = {'iteration': iteration, 'dynamic_status': 'skipped', 'findings': []}
        try:
            if iteration == 0 and imported:
                response_text = imported[2]
                response = {'response': response_text, 'origin': 'archived_generation', 'done': True}
                entry['model_called'] = False
                source_response = imported[0]/'response.json'
                if source_response.is_file():
                    (attempt_folder/'source_response.json').write_bytes(source_response.read_bytes())
            else:
                prompt = build_prompt(spec) if iteration == 0 else revision_prompt(spec, previous_output, feedback)
                (attempt_folder/'prompt.txt').write_bytes(prompt.encode('utf-8'))
                entry['prompt_sha256'] = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
                entry['model_called'] = True
                response = client.generate(prompt)
                response_text = response['response']
            history['revision_count'] = iteration
            _write_json(attempt_folder/'response.json', response)
            (attempt_folder/'response.txt').write_bytes(response_text.encode('utf-8'))
            try:
                code = extract_php(response_text)
            except ExtractionError as exc:
                code = None
                entry['findings'] = [{'source': 'format', 'location': {'response': 'model'},
                                      'explanation': str(exc), 'evidence': response_text[:1200]}]
            final_code = code
            if code is not None:
                code_bytes = code.encode('utf-8')
                candidate = attempt_folder/'controller.php'
                candidate.write_bytes(code_bytes)
                entry['code_sha256'] = hashlib.sha256(code_bytes).hexdigest()
                if iteration == 0:
                    (folder/'initial_controller.php').write_bytes(code_bytes)
                if iteration > 0 and previous_code == code:
                    entry.update(reused_from=iteration-1, dynamic_status='reused',
                                 findings=history['attempts'][-1]['findings'])
                    history.update(status='BELUM LOLOS', stop_reason='identical_code')
                else:
                    static = static_analyzer(code, spec)
                    entry['static'] = static
                    entry['findings'] = list(static['findings'])
                    if not entry['findings']:
                        dynamic = runner.check_candidate(candidate)
                        entry['dynamic'] = dynamic
                        entry['dynamic_status'] = dynamic['status']
                        if dynamic['status'] not in ('PASSED_INTERNAL', 'FAILED_INTERNAL'):
                            raise SandboxError(f"Pengujian dinamis tidak dapat dinilai: {dynamic.get('reason', dynamic['status'])}")
                        summary = dynamic.get('summary', {})
                        if summary.get('total') != expected_tests or type(summary.get('passed')) is not int:
                            raise SandboxError(f'Hasil dinamis tidak lengkap untuk kontrak {expected_tests} test.')
                        if dynamic['status'] == 'PASSED_INTERNAL' and (summary['passed'] != expected_tests or
                                any(summary.get(k) != 0 for k in ('failure', 'error', 'skipped'))):
                            raise SandboxError('Status sukses bertentangan dengan hasil test.')
                        current_image = dynamic.get('image_id')
                        if not current_image or (image_id is not None and current_image != image_id):
                            raise SandboxError('Identitas image berubah atau tidak tersedia.')
                        image_id = current_image
                        # Real DockerRunner exposes image so subsequent attempts use the pinned ID.
                        if hasattr(runner, 'image'):
                            runner.image = image_id
                        if dynamic['status'] == 'PASSED_INTERNAL':
                            history.update(status='LOLOS', stop_reason='all_checks_passed')
                        else:
                            entry['findings'] = collect_findings([], dynamic)
                            _write_json(attempt_folder/'dynamic.json', dynamic)
            if history['status'] == 'RUNNING':
                if iteration == max_revisions:
                    history.update(status='BELUM LOLOS', stop_reason='max_revisions')
                else:
                    dynamic = entry.get('dynamic')
                    feedback = build_feedback(entry['findings'] if dynamic is None else [], dynamic, iteration)
                    if not feedback['findings']:
                        raise SandboxError('Pemeriksaan gagal tanpa temuan yang dapat dikirim sebagai feedback.')
                    _write_json(attempt_folder/'feedback.json', feedback)
                    previous_code, previous_output = code, response_text
        except ModelError as exc:
            history.update(status='ERROR', stop_reason='model_error')
            entry['error'] = str(exc)
            if exc.response is not None:
                _write_json(attempt_folder/'response.json', exc.response)
        except (SandboxError, StaticEnvironmentError, OSError) as exc:
            history.update(status='ERROR', stop_reason='environment_error')
            entry['error'] = str(exc)
        finally:
            entry['elapsed_seconds'] = round(time.monotonic()-started, 6)
            history['attempts'].append(entry)
            _write_json(attempt_folder/'result.json', entry)
            _write_json(folder/'history.json', history)
            with (folder/'run.log').open('a', encoding='utf-8') as log:
                log.write(f"Attempt {iteration}: {entry['dynamic_status']}, status={history['status']}\n")
        if history['status'] != 'RUNNING':
            break
    if final_code is not None:
        (folder/'final_controller.php').write_bytes(final_code.encode('utf-8'))
    manifest.update(status=history['status'], stop_reason=history['stop_reason'],
                    revision_count=history['revision_count'], image_id=image_id,
                    final_code_available=final_code is not None)
    _write_json(folder/'run_manifest.json', manifest)
    return folder
