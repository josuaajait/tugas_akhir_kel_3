"""Versioned final CRUD assets. No model access and no legacy suite mutation."""
import copy
import hashlib
import json
from pathlib import Path

from .resources import validate_resource_spec
from .spec import load_spec

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT/'evaluation'/'final-v1'
RESOURCES = ('categories', 'rooms', 'assets', 'courses', 'shipments')


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _valid_payload(spec, payload):
    if set(payload) != {f['name'] for f in spec['fields']}:
        return False
    for field in spec['fields']:
        value = payload[field['name']]
        if field['type'] == 'string':
            if not isinstance(value, str) or not value.strip():
                return False
            size = len(value)
        else:
            if type(value) is not int:
                return False
            size = value
        for rule in field['rules']:
            if rule.startswith('min:') and size < int(rule[4:]):
                return False
            if rule.startswith('max:') and size > int(rule[4:]):
                return False
    return True


def validate_profile(spec, profile):
    validate_resource_spec(spec)
    if profile.get('spec') != spec or profile.get('package') != 'final-v1':
        raise ValueError('Profil final harus cocok persis dengan spesifikasi paket.')
    fixtures = profile.get('fixtures', {})
    if set(fixtures) != {'new', 'target', 'other', 'updated'}:
        raise ValueError('Empat fixture acuan wajib tersedia.')
    if not all(_valid_payload(spec, body) for body in fixtures.values()):
        raise ValueError('Fixture acuan tidak memenuhi kontrak.')
    for field in spec['fields']:
        values = [body[field['name']] for body in fixtures.values()]
        if len(set(values)) != len(values):
            raise ValueError('Nilai setiap field fixture harus berbeda antar-record.')
    names = set()
    for case in profile.get('invalid', []) + profile.get('valid', []):
        if not isinstance(case, dict) or case.get('name') in names:
            raise ValueError('Dataset kosong atau duplikat.')
        names.add(case.get('name'))
        if case.get('field') not in fixtures['new'] or not isinstance(case.get('payload'), dict):
            raise ValueError('Dataset harus memiliki field dan payload eksplisit.')
    if not profile.get('invalid') or not profile.get('valid'):
        raise ValueError('Dataset positif dan negatif wajib tersedia.')
    return profile


def _base_cases(fixtures):
    return [dict(case_id=name, kind=name, operation=verb, payload=fixtures['updated' if name=='update' else 'new'])
            for name, verb in [('index','GET'), ('store','POST'), ('show','GET'),
                               ('update','PUT'), ('destroy','DELETE')]] + [
        dict(case_id='missing_'+verb, kind='missing_id', operation=verb, payload=fixtures['new'])
        for verb in ('GET', 'PUT', 'DELETE')]


def internal_fixtures(spec):
    """Final-only fixtures distinguish fields and avoid request boundary collisions."""
    roles=('new','target','other','updated','missing')
    result={role:{} for role in roles}
    for number,field in enumerate(spec['fields']):
        bounds={r.split(':')[0]:int(r.split(':')[1]) for r in field['rules'] if r.startswith(('min:','max:'))}
        for index,role in enumerate(roles):
            if field['type']=='string':
                length=max(4,bounds.get('min',1)+2)
                length=min(length,bounds.get('max',256)-1)
                value=chr(65+number)+str(index)+'x'*(length-2)
            else:
                low,high=bounds.get('min',0),bounds.get('max',1000)
                value=low+[1,2,0,3,4][index] if high-low<=5 else min(high-5,low+10+number*7)+index
            result[role][field['name']]=value
    return result


def suite_cases(spec, profile, internal=False):
    fixtures = internal_fixtures(spec) if internal else profile['fixtures']
    cases = _base_cases(fixtures)
    if internal:
        for verb in ('POST', 'PUT'):
            for field in spec['fields']:
                name = field['name']
                body = dict(fixtures['new'])
                del body[name]
                cases.append(dict(case_id=verb+'_missing_'+name, kind='invalid', operation=verb,
                                  field=name, vector='missing', payload=body))
    else:
        cases += [dict(case_id='empty', kind='empty', operation='GET'),
                  dict(case_id='sequence', kind='sequence', operation='SEQUENCE')]
        for group, kind in [('invalid', 'invalid'), ('valid', 'boundary')]:
            for verb in ('POST', 'PUT'):
                for item in profile[group]:
                    cases.append(dict(copy.deepcopy(item), case_id=verb+'_'+item['name'],
                                      kind=kind, operation=verb))
        for field in spec['fields']:
            if any(r.startswith('unique:') for r in field['rules']):
                body = dict(fixtures['updated'])
                body[field['name']] = fixtures['target'][field['name']]
                cases.append(dict(case_id='PUT_own_'+field['name'], kind='own_unique', operation='PUT',
                                  field=field['name'], vector='own_unique', payload=body))
    return cases


def test_id(role, case_id):
    cls = 'FinalInternalTest' if role == 'internal' else 'FinalReferenceTest'
    return {'class': 'FinalEvaluation.'+cls, 'name': 'test_contract with data set "'+case_id+'"'}


def package_manifest(resource):
    if resource not in RESOURCES:
        raise ValueError('Resource final-v1 tidak dikenal.')
    spec = load_spec(PACKAGE/'specs'/(resource+'.json'))
    if spec['resource'] != resource or spec['spec_id'] != 'final_'+resource+'_v1':
        raise ValueError('Identitas spesifikasi final tidak sesuai registry.')
    profile = json.loads((PACKAGE/'profiles'/(resource+'.json')).read_text(encoding='utf-8'))
    validate_profile(spec, profile)
    sources = sorted(p for p in PACKAGE.rglob('*') if p.is_file() and p.suffix in {'.php', '.json', '.xml', '.diff'}
                     and p.name not in {'manifest.json', 'decisions.json'})
    sources += sorted((ROOT/'critic_agent').glob('final_*.py'))
    sources += [ROOT/'critic_agent'/name for name in ('resources.py','sandbox.py','process.py','spec.py','__init__.py')]
    sources += [ROOT/'harness/runtime.php', ROOT/'harness/laravel/phpunit.xml',
                ROOT/'harness/laravel/composer.lock']
    hashes = {p.relative_to(ROOT).as_posix(): _hash(p.read_bytes()) for p in sources}
    canonical = {p.relative_to(ROOT).as_posix(): _hash(p.read_bytes().replace(b'\r\n', b'\n')) for p in sources}
    digest = _hash(json.dumps(hashes, sort_keys=True).encode())
    return {'package': 'final-v1', 'stage': 'pre_freeze_validation', 'ready_for_final': False,
            'spec': spec, 'profile': profile, 'spec_sha256': _hash((PACKAGE/'specs'/(resource+'.json')).read_bytes()),
            'package_sha256': digest, 'source_hashes': hashes, 'canonical_source_hashes':canonical,
            'internal_fixtures': internal_fixtures(spec), 'internal_tests': len(suite_cases(spec, profile, True)),
            'reference_tests': len(suite_cases(spec, profile)),
            'internal_sha256': _hash((digest+resource+'internal').encode()),
            'reference_sha256': _hash((digest+resource+'reference').encode())}


def load_package(resource=None):
    return [package_manifest(name) for name in ([resource] if resource else RESOURCES)]


def traceability(resource):
    meta = package_manifest(resource)
    internal = {c['case_id']: c for c in suite_cases(meta['spec'], meta['profile'], True)}
    rows = []
    for case in suite_cases(meta['spec'], meta['profile']):
        cid = case['case_id']
        rows.append({'case_id': cid, 'spec_id': meta['spec']['spec_id'], 'operation': case['operation'],
                     'field': case.get('field'), 'vector': case.get('vector', case['kind']),
                     'rule_id': (case.get('field', 'crud')+'.'+case.get('vector', case['kind'])),
                     'fixture': copy.deepcopy(case), 'reference_test_id': test_id('reference', cid),
                     'internal_test_id': test_id('internal', cid) if cid in internal else None,
                     'coverage': 'internal_covered' if cid in internal else 'reference_only',
                     'expected_status': [201,200,200,200,200,204,404] if case['kind']=='sequence' else 422 if case['kind']=='invalid' else 404 if case['kind']=='missing_id'
                     else 204 if case['kind']=='destroy' else 201 if case['operation']=='POST' else 200,
                     'expected_body': {'shape':'object','errors_field':case['field']} if case['kind']=='invalid'
                     else {'shape':'object'} if case['kind']=='missing_id' else {'raw':''} if case['kind']=='destroy'
                     else {'data':meta['profile']['fixtures']['target'],'id':'requested target integer'} if case['kind']=='show'
                     else {'data':case.get('expected',case.get('payload')),'id':'new integer' if case['operation']=='POST' else 'requested target integer'} if case['kind'] in ('store','update','boundary','own_unique')
                     else {'data':'array of exact ID-bound fixture records' if case['kind']=='index' else []} if case['kind']!='sequence'
                     else {'steps':['create','read','replace','read','list','delete','read missing']},
                     'expected_state': 'unchanged' if case['kind'] in ('index','show','empty','invalid','missing_id')
                     else 'target removed; neighbour unchanged' if case['kind']=='destroy'
                     else 'create/read/update/read/list/delete/read missing; database empty at end' if case['kind']=='sequence'
                     else 'exactly one new record; existing records unchanged' if case['operation']=='POST'
                     else 'only requested target replaced; neighbour unchanged',
                     'validation':{'status':'PENDING','observations':[]},
                     'positive_control_ids': ['eloquent', 'explicit'], 'negative_control_ids': [],
                     'review_status': 'pending', 'human_author': None, 'reviewer': None, 'reviewed_at': None})
    return rows
