"""Prepare and verify development evidence for the FR-19 freeze gate."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from . import __version__
from .spec import load_spec


PENDING = (
    'held_out_package', 'independent_human_review', 'final_suite_validation',
    'k2_thresholds', 'fr20_decision', 'final_configuration_and_schedule',
)


def _safe_path(root, name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError(f'Path artefak tidak valid: {name!r}')
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or relative.as_posix() != name:
        raise ValueError(f'Path artefak tidak valid: {name!r}')
    path = (root / Path(*relative.parts)).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'Path artefak keluar dari proyek: {name}')
    return path


def _sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def create_draft(output, root, artifacts, *, development=None):
    root = Path(root).resolve()
    entries = []
    for role, paths in sorted(artifacts.items()):
        for file in sorted(paths):
            path = Path(file).resolve()
            if not path.is_relative_to(root):
                raise ValueError(f'Path artefak keluar dari proyek: {path}')
            entries.append({'role': role, 'path': path.relative_to(root).as_posix(), 'sha256': _sha256(path)})
    if not entries:
        raise ValueError('Paket draf harus memuat artefak.')
    manifest = {'schema_version': '1.0', 'status': 'DRAFT',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'prototype_version': __version__, 'development': development or {},
                'final_plan': {'held_out_cases': [], 'repetitions': None, 'configuration': None,
                               'seed_schedule': [], 'conditions': None},
                'artifacts': entries, 'pending': list(PENDING)}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    return output.resolve()


def prepare_project_draft(output, root, pilot_report):
    root = Path(root).resolve()
    pilot_report = Path(pilot_report).resolve()
    pilot = json.loads(pilot_report.read_bytes())
    if pilot.get('stage') != 'development' or not pilot.get('reference', {}).get('n_pair'):
        raise ValueError('Gunakan laporan pilot development yang menyertakan hasil evaluator.')
    specs = [root/'examples'/f'{name}.json' for name in ('products', 'books', 'inventory_items')]
    source = root/'critic_agent'
    harness = root/'harness'
    evaluation = root/'evaluation'
    artifacts = {
        'protocol': [root/'PRD_Critic_Agent_v1.3.md', root/'docs/evidence/fr-19-traceability.md'],
        'prototype': list(source.glob('*.py')),
        'prompts': [source/'prompts.py', source/'feedback.py'],
        'development_specifications': specs,
        'development_internal': [
            source/'resources.py', harness/'products-contract.json', harness/'Dockerfile',
            harness/'entrypoint.php', harness/'runtime.php',
            *sorted((root/'resource_templates').glob('*.php')),
            *(path for directory in ('app', 'config', 'database', 'routes', 'tests')
              for path in (harness/'laravel'/directory).rglob('*.php')),
            *(harness/'laravel'/'bootstrap').glob('*.php'),
            harness/'laravel'/'composer.json', harness/'laravel'/'composer.lock', harness/'laravel'/'phpunit.xml',
        ],
        'development_reference': [
            evaluation/'Dockerfile', evaluation/'entrypoint.php', evaluation/'phpunit-evaluation.xml',
            evaluation/'suite.json', *evaluation.glob('reference-tests/*.php'),
            *evaluation.glob('products-v2/*.php'), *evaluation.glob('products-v2/*.xml'),
            *[evaluation/'resource-reference'/name for name in ('Dockerfile', 'phpunit.xml', 'ResourceReferenceTest.php')],
            *evaluation.glob('resource-reference/profiles/*.json'),
        ],
        'pilot_evidence': [pilot_report, pilot_report.parent/'environment.json',
                           *{Path(job['manifest']) for job in pilot['jobs']}],
        'reference_evidence': [Path(job['evaluation']['report']) for job in pilot['jobs']
                               if job['evaluation']['status'] == 'EVALUATED'],
    }
    environment = json.loads((pilot_report.parent/'environment.json').read_bytes())
    groups = [{'spec': Path(group['spec']).name, 'temperature': group['temperature'],
               'n_pair': group['reference']['n_pair'], 'internal_image_ids': group['image_ids']}
              for group in pilot['groups']]
    ids = {(job['evaluation']['suite_sha256'], job['evaluation']['image_id'])
           for job in pilot['jobs'] if job['evaluation']['status'] == 'EVALUATED'}
    development = {'spec_ids': [load_spec(path)['spec_id'] for path in specs],
                   'n_valid': pilot['reference']['n_valid'], 'n_pair': pilot['reference']['n_pair'],
                   'model': environment['model'], 'ollama_version': environment['ollama_version'],
                   'seeds': sorted({job['seed'] for job in pilot['jobs']}),
                   'temperatures': sorted({job['temperature'] for job in pilot['jobs']}),
                   'groups': groups,
                   'reference_suites': [{'suite_sha256': suite, 'image_id': image} for suite, image in sorted(ids)]}
    return create_draft(output, root, artifacts, development=development)


def check_draft(manifest_path, root):
    root = Path(root).resolve()
    manifest = json.loads(Path(manifest_path).read_bytes())
    if not isinstance(manifest, dict) or manifest.get('schema_version') != '1.0' or manifest.get('status') != 'DRAFT':
        raise ValueError('Hanya manifest FR-19 berstatus DRAFT yang dapat diperiksa.')
    entries = manifest.get('artifacts')
    if not isinstance(entries, list) or not entries:
        raise ValueError('Manifest tidak memuat artefak.')
    seen = set()
    changed = []
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError('Entri artefak tidak valid.')
        name, role, fingerprint = (item.get(key) for key in ('path', 'role', 'sha256'))
        path = _safe_path(root, name)
        if (not isinstance(role, str) or not role or not isinstance(fingerprint, str)
                or not re.fullmatch('[a-f0-9]{64}', fingerprint) or (role, name) in seen):
            raise ValueError(f'Entri artefak tidak valid atau duplikat: {name}')
        seen.add((role, name))
        if not path.is_file():
            changed.append({'path': name, 'reason': 'missing'})
        elif _sha256(path) != fingerprint:
            changed.append({'path': name, 'reason': 'hash_mismatch'})
    return {'status': 'BLOCKED', 'ready_for_final': False, 'pending': list(PENDING),
            'integrity': 'FAILED' if changed else 'VERIFIED',
            'artifact_count': len(entries), 'changes': changed}
