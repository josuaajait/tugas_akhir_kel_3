"""Interactive specification entry and preparation for the existing resource loop."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from .doctor import doctor
from .ollama import OllamaClient
from .orchestrator import run_resource
from .process import bounded_run, OutputLimitError
from .resources import build_resource, resource_contract, ResourceDockerRunner, validate_resource_spec
from .sandbox import SandboxError
from .spec import OPERATIONS, SpecError
from .console import current_console, progress


ROOT = Path(__file__).resolve().parents[1]


def _write(text):
    console = current_console()
    if console is None:
        print(text, file=sys.stderr, flush=True)
    else:
        console.message(text)


def _read(prompt):
    console = current_console()
    if console is not None and console.pretty:
        return console.read(prompt)
    print(prompt, end='', file=sys.stderr, flush=True)
    return input()


def _ask(prompt, convert, read, write):
    while True:
        try:
            return convert(read(prompt).strip())
        except ValueError as exc:
            write(str(exc))


def _yes_no(value):
    if value.lower() in ('y', 'ya'):
        return True
    if value.lower() in ('n', 'tidak'):
        return False
    raise ValueError('Jawab y/ya atau n/tidak.')


def collect_spec(*, read=None, write=_write):
    read = read or _read
    spec = {'spec_id': 'interactive', 'spec_version': '1.0', 'resource': 'items',
            'model': 'Item', 'controller': 'ItemController',
            'fields': [{'name': 'value', 'type': 'string', 'rules': ['required', 'string']}],
            'operations': copy.deepcopy(OPERATIONS)}

    def identifier(key):
        def convert(value):
            candidate = dict(spec, **{key: value})
            validate_resource_spec(candidate)
            return value
        return convert

    write('Spesifikasi CRUD baru. Semua field wajib diisi pada POST dan PUT.')
    write('Operasi index/store/show/update/destroy memakai status HTTP kontrak v1.')
    spec['resource'] = _ask('Nama resource/tabel (contoh books): ', identifier('resource'), read, write)
    spec['model'] = _ask('Nama model (contoh Book): ', identifier('model'), read, write)
    spec['controller'] = _ask('Nama controller (contoh BookController): ', identifier('controller'), read, write)
    spec['spec_id'] = spec['resource']

    def count(value):
        number = int(value)
        if not 1 <= number <= 20:
            raise ValueError('Jumlah field harus 1–20.')
        return number

    total = _ask('Jumlah field (1–20, ID/timestamp otomatis): ', count, read, write)
    fields = []
    for index in range(total):
        write(f'Field {index+1} dari {total}')

        def field_name(value):
            candidate = dict(spec, fields=fields+[
                {'name': value, 'type': 'string', 'rules': ['required', 'string']}])
            validate_resource_spec(candidate)
            return value

        name = _ask('Nama field: ', field_name, read, write)

        def field_type(value):
            if value not in ('string', 'integer'):
                raise ValueError('Tipe yang didukung adalah string atau integer.')
            return value

        kind = _ask('Tipe (string/integer): ', field_type, read, write)

        def bound(value):
            if not value:
                return None
            number = int(value)
            if abs(number) > 1_000_000 or (kind == 'string' and not 0 <= number <= 256):
                raise ValueError('Batas string 0–256 karakter, integer -1000000 sampai 1000000.')
            return number

        while True:
            unit = 'panjang' if kind == 'string' else 'nilai'
            minimum = _ask(f'Minimum {unit} (Enter tanpa batas): ', bound, read, write)
            maximum = _ask(f'Maksimum {unit} (Enter tanpa batas): ', bound, read, write)
            unique = _ask('Harus unik? (y/n): ', _yes_no, read, write)
            rules = ['required', kind]
            if minimum is not None:
                rules.append(f'min:{minimum}')
            if maximum is not None:
                rules.append(f'max:{maximum}')
            if unique:
                rules.append(f"unique:{spec['resource']},{name}")
            field = {'name': name, 'type': kind, 'rules': rules}
            try:
                validate_resource_spec(dict(spec, fields=fields+[field]))
            except SpecError as exc:
                write(f'{exc} Masukkan ulang batas dan aturan unique field ini.')
                continue
            fields.append(field)
            break
    spec['fields'] = fields
    resource_contract(spec)
    return spec


def _save(path, data):
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temporary.replace(path)


def _docker(command, folder, name, timeout):
    """Archive each trusted preparation command, including failed/partial output."""
    record = {'command': command, 'timeout_seconds': timeout}
    stdout, stderr = b'', b''
    try:
        result = bounded_run(command, timeout=timeout, capture_output=True, shell=False)
        stdout, stderr = result.stdout, result.stderr
        record['exit_code'] = result.returncode
        return result
    except (subprocess.TimeoutExpired, OutputLimitError) as exc:
        stdout, stderr = exc.output or b'', exc.stderr or b''
        record['error'] = str(exc)
        raise
    except OSError as exc:
        record['error'] = str(exc)
        raise
    finally:
        (folder/(name+'.stdout.log')).write_bytes(stdout)
        (folder/(name+'.stderr.log')).write_bytes(stderr)
        _save(folder/(name+'.json'), record)


def prepare_base(folder, *, timeout, write=_write):
    inspection = _docker(['docker', 'image', 'inspect', '--format', '{{.Id}}', 'critic-laravel:dev'],
                         folder, 'base-inspect', timeout)
    if inspection.returncode == 0:
        return 'critic-laravel:dev'
    image = 'critic-interactive-base-'+uuid4().hex+':dev'
    write('Menyiapkan image dasar Laravel. Build pertama memerlukan jaringan dan dapat memakan waktu.')
    result = _docker(['docker', 'build', '--tag', image, str(ROOT/'harness')], folder, 'base-build', timeout)
    if result.returncode:
        raise SandboxError('Build image dasar gagal. Baca base-build.stderr.log pada folder sesi.')
    return image


def start_interactive(output_root, *, model='qwen2.5:7b-instruct', temperature=0.2, seed=42,
                      timeout=300, test_timeout=120, build_timeout=600, max_revisions=3,
                      read=None, write=_write):
    # Validate CLI options before asking questions or creating any files.
    client = OllamaClient(model=model, temperature=temperature, seed=seed, timeout=timeout)
    if any(not math.isfinite(value) or value <= 0 for value in (test_timeout, build_timeout)):
        raise ValueError('Timeout build dan test harus positif dan finite.')
    if type(max_revisions) is not int or not 0 <= max_revisions <= 3:
        raise ValueError('Maksimal revisi harus 0–3.')
    read = read or _read
    session = None
    result = {'status': 'CANCELLED', 'stage': 'input'}
    try:
        spec = collect_spec(read=read, write=write)
        write('Ringkasan spesifikasi')
        write(json.dumps(spec, ensure_ascii=False, indent=2))
        write(f'Model {model}, suhu {temperature}, seed {seed}, maksimal {max_revisions} revisi.')
        if not _ask('Simpan dan jalankan self-debugging? (y/n): ', _yes_no, read, write):
            return result
        session = Path(output_root).resolve()/(
            datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_interactive_'+uuid4().hex)
        session.mkdir(parents=True, exist_ok=False)
        _save(session/'spec.json', spec)
        result = {'status': 'RUNNING', 'stage': 'prerequisites',
                  'session_directory': str(session), 'spec_file': str(session/'spec.json'),
                  'spec_sha256': hashlib.sha256((session/'spec.json').read_bytes()).hexdigest(),
                  'configuration': {'model': model, 'options': client.options,
                                    'model_timeout_seconds': timeout, 'test_timeout_seconds': test_timeout,
                                    'build_timeout_seconds': build_timeout, 'max_revisions': max_revisions},
                  'created_at': datetime.now(timezone.utc).isoformat()}
        _save(session/'session.json', result)
        write(f'Spesifikasi dan riwayat sesi disimpan di {session}')
        write('Memeriksa Python, PHP, Docker, dan model Ollama.')
        progress('Memeriksa prasyarat Python, PHP, Docker, dan Ollama...')
        prerequisites = doctor()
        # doctor checks the development Qwen name; start must check the selected model.
        checks = prerequisites['checks']
        if checks.get('ollama', {}).get('ok'):
            checks['qwen'] = {'ok': model in checks['ollama']['detail'], 'detail': f'Model yang dipilih {model}'}
        prerequisites['ready'] = all(check.get('ok') for check in checks.values())
        _save(session/'prerequisites.json', prerequisites)
        if not prerequisites['ready']:
            failed = [f"{name}: {check.get('detail', 'tidak siap')}"
                      for name, check in checks.items() if not check.get('ok')]
            raise SandboxError('Prasyarat belum siap. '+' | '.join(failed))
        result['stage'] = 'prepare_base'
        _save(session/'session.json', result)
        progress('Menyiapkan image dasar Laravel...')
        base = prepare_base(session, timeout=build_timeout, write=write)
        image = 'critic-interactive-'+uuid4().hex+':dev'
        result.update(stage='build_resource', image=image, base_image=base)
        _save(session/'session.json', result)
        write('Membangun harness sesuai spesifikasi.')
        progress('Membangun harness sesuai spesifikasi...')
        command_index = 0

        def execute(command, **kwargs):
            nonlocal command_index
            command_index += 1
            return _docker(command, session, f'resource-command-{command_index}', kwargs['timeout'])

        build = build_resource(spec, session/'builds', image=image, base_image=base,
                               timeout=build_timeout, execute=execute)
        result['build_directory'] = str(build.resolve())
        build_result = json.loads((build/'build_result.json').read_text(encoding='utf-8'))
        if build_result['status'] != 'BUILT':
            raise SandboxError(build_result.get('detail') or build_result.get('reason') or 'Build resource gagal.')
        result['stage'] = 'readiness'
        _save(session/'session.json', result)
        write('Memeriksa kesiapan harness Docker.')
        progress('Memeriksa kesiapan harness Docker...')
        runner = ResourceDockerRunner(spec, image=image, output_root=session/'harness', timeout=test_timeout)
        readiness = runner.check_reference()
        _save(session/'readiness.json', readiness)
        if readiness['status'] != 'READY':
            raise SandboxError('Harness belum siap. Baca readiness.json pada folder sesi.')
        runner.image = readiness['image_id']
        result.update(stage='loop', image_id=runner.image)
        _save(session/'session.json', result)
        write('Menjalankan Qwen dan loop self-debugging. Setiap percobaan diarsipkan.')
        run = run_resource(spec, session/'runs', client, runner, max_revisions=max_revisions)
        history = json.loads((run/'history.json').read_text(encoding='utf-8'))
        result.update(status=history['status'], stage='completed', stop_reason=history['stop_reason'],
                      revision_count=history['revision_count'], run_directory=str(run.resolve()))
        return result
    except (EOFError, KeyboardInterrupt):
        result.update(status='CANCELLED', reason='input_or_execution_cancelled')
        if session is not None and result.get('stage') == 'loop':
            # This UUID session owns at most one new loop. Close only its interrupted archive.
            for run in (session/'runs').glob('*_loop_*'):
                if not (run/'history.json').is_file() or not (run/'run_manifest.json').is_file():
                    continue
                history = json.loads((run/'history.json').read_text(encoding='utf-8'))
                if history['status'] == 'RUNNING':
                    history.update(status='ERROR', stop_reason='user_cancelled')
                    if history['attempts']:
                        entry = history['attempts'][-1]
                        entry['error'] = 'Eksekusi dibatalkan pengguna.'
                        _save(run/'attempts'/str(entry['iteration'])/'result.json', entry)
                    _save(run/'history.json', history)
                    manifest = json.loads((run/'run_manifest.json').read_text(encoding='utf-8'))
                    manifest.update(status='ERROR', stop_reason='user_cancelled',
                                    revision_count=history['revision_count'], final_code_available=False)
                    _save(run/'run_manifest.json', manifest)
                result['run_directory'] = str(run.resolve())
        return result
    except (OSError, ValueError, SandboxError, subprocess.TimeoutExpired, OutputLimitError) as exc:
        result.update(status='ERROR', reason=str(exc))
        return result
    finally:
        if session is not None:
            _save(session/'session.json', result)
