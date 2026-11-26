"""Final-v2 contract assets, isolated from the immutable final-v1 fingerprint."""
import copy
import hashlib
import json
from pathlib import Path

from .final_package import RESOURCES,ROOT,internal_fixtures,test_id,validate_profile as _validate_profile,suite_cases as _v1_cases
from .spec import load_spec

PACKAGE=ROOT/'evaluation/final-v2'

def validate_profile(spec,profile):
    candidate=copy.deepcopy(profile);candidate['package']='final-v1'
    _validate_profile(spec,candidate)
    if profile.get('package')!='final-v2':raise ValueError('Profile must belong to final-v2.')
    return profile

def short_fields(spec):
    return [f for f in spec['fields'] if f['type']=='string' and not any(r.startswith('min:') for r in f['rules'])]

def suite_cases(spec,profile,internal=False):
    fixtures=internal_fixtures(spec) if internal else profile['fixtures']
    cases=_v1_cases(spec,profile,internal)
    for method,verb in [('show','GET'),('update','PUT'),('destroy','DELETE')]:
        cases.append({'case_id':method+'_second','kind':method,'operation':verb,'target_position':2,
                      'payload':copy.deepcopy(fixtures['updated' if method=='update' else 'new'])})
    if internal:
        for verb in ('POST','PUT'):
            for number,field in enumerate(short_fields(spec)):
                for length in (1,2):
                    payload=copy.deepcopy(fixtures['new']);payload[field['name']]=chr(65+number)*length
                    cases.append({'case_id':f'{verb}_short{length}_{field["name"]}','kind':'boundary','operation':verb,
                                  'name':f'short{length}_{field["name"]}','field':field['name'],'vector':f'short{length}','payload':payload})
    if len({c['case_id'] for c in cases})!=len(cases):raise ValueError('Duplicate final-v2 case ID.')
    return cases

def package_manifest(resource):
    if resource not in RESOURCES:raise ValueError('Unknown final-v2 resource.')
    spec=load_spec(PACKAGE/'specs'/(resource+'.json'))
    if spec['spec_id']!='final_'+resource+'_v2':raise ValueError('Wrong final-v2 spec identity.')
    profile=json.loads((PACKAGE/'profiles'/(resource+'.json')).read_bytes());validate_profile(spec,profile)
    paths=sorted(p for p in PACKAGE.rglob('*') if p.is_file() and p.suffix in ('.php','.json','.xml','.diff')
                 and p.name not in ('manifest.json','decisions.json'))
    paths+=sorted((ROOT/'critic_agent').glob('eval_*_v2.py'))
    for name in ('eval_registry.py','final_package.py','final_controls.py','final_sandbox.py',
                 'resources.py','sandbox.py','process.py','spec.py','__init__.py'):
        file=ROOT/'critic_agent'/name
        if file.is_file():paths.append(file)
    paths += [ROOT/'harness/runtime.php',ROOT/'harness/laravel/phpunit.xml',ROOT/'harness/laravel/composer.lock']
    paths += sorted((ROOT/'resource_templates').glob('*.php'))
    digest=lambda data:hashlib.sha256(data).hexdigest()
    hashes={p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(set(paths))}
    canonical={p.relative_to(ROOT).as_posix():digest(p.read_bytes().replace(b'\r\n',b'\n')) for p in sorted(set(paths))}
    fingerprint=digest(json.dumps(hashes,sort_keys=True).encode())
    return {'package':'final-v2','stage':'pre_freeze_validation','ready_for_final':False,'spec':spec,'profile':profile,
            'spec_sha256':digest((PACKAGE/'specs'/(resource+'.json')).read_bytes()),'package_sha256':fingerprint,
            'source_hashes':hashes,'canonical_source_hashes':canonical,'internal_fixtures':internal_fixtures(spec),
            'internal_tests':len(suite_cases(spec,profile,True)),'reference_tests':len(suite_cases(spec,profile)),
            'internal_sha256':digest((fingerprint+resource+'internal').encode()),
            'reference_sha256':digest((fingerprint+resource+'reference').encode())}

def traceability(resource):
    meta=package_manifest(resource);internal={c['case_id'] for c in suite_cases(meta['spec'],meta['profile'],True)}
    rows=[]
    for case in suite_cases(meta['spec'],meta['profile']):
        cid=case['case_id'];kind=case['kind'];verb=case['operation']
        status=([201,200,200,200,200,204,404] if kind=='sequence' else 422 if kind=='invalid' else
                404 if kind=='missing_id' else 204 if kind=='destroy' else 201 if verb=='POST' else 200)
        if kind=='invalid':body={'shape':'object','errors_field':case['field']}
        elif kind=='missing_id':body={'shape':'object'}
        elif kind=='destroy':body={'raw':''}
        elif kind=='show':body={'data':meta['profile']['fixtures']['other' if case.get('target_position')==2 else 'target'],'id':'requested target integer'}
        elif kind in ('store','update','boundary','own_unique'):body={'data':case.get('expected',case.get('payload')),'id':'new integer' if verb=='POST' else 'requested target integer'}
        elif kind=='sequence':body={'steps':['create','read','replace','read','list','delete','read missing']}
        else:body={'data':'array of exact ID-bound fixture records' if kind=='index' else []}
        state=('unchanged' if kind in ('index','show','empty','invalid','missing_id') else
               'target removed; neighbour unchanged' if kind=='destroy' else
               'create/read/update/read/list/delete/read missing; database empty at end' if kind=='sequence' else
               'exactly one new record; existing records unchanged' if verb=='POST' else 'only requested target replaced; neighbour unchanged')
        rows.append({'case_id':cid,'spec_id':meta['spec']['spec_id'],'operation':verb,'field':case.get('field'),
            'vector':case.get('vector',kind),'rule_id':case.get('field','crud')+'.'+case.get('vector',kind),
            'fixture':copy.deepcopy(case),'reference_test_id':test_id('reference',cid),
            'internal_test_id':test_id('internal',cid) if cid in internal else None,
            'coverage':'internal_covered' if cid in internal else 'reference_only','expected_status':status,
            'expected_body':body,'expected_state':state,'validation':{'status':'PENDING','observations':[]},
            'positive_control_ids':['eloquent','explicit'],'negative_control_ids':[],
            'review_status':'pending','human_author':None,'reviewer':None,'reviewed_at':None})
    return rows
