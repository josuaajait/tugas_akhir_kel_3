"""Versioned controls reuse old faults and add the three audited fault families."""
import difflib
import hashlib
import json
from pathlib import Path
import re

from .eval_package_v2 import PACKAGE,package_manifest,suite_cases,traceability

def control_catalog(resource):
    """Consume only persisted v2 assets; archived v1 files are not runtime inputs."""
    meta=package_manifest(resource)
    cases={c['case_id'] for c in suite_cases(meta['spec'],meta['profile'])}
    internal={c['case_id'] for c in suite_cases(meta['spec'],meta['profile'],True)}
    folder=PACKAGE/'controls'/resource;document=json.loads((folder/'catalog.json').read_bytes())
    if document.get('resource')!=resource or document.get('package')!='final-v2':raise ValueError('Wrong v2 control catalog.')
    entries=document.get('controls')
    if not isinstance(entries,list) or not entries:raise ValueError('Empty v2 control catalog.')
    controls=[];seen=set()
    for entry in entries:
        name=entry.get('control_id');targets=entry.get('target_case_ids');evidence=entry.get('failure_evidence')
        if (not isinstance(name,str) or not re.fullmatch('[a-z][a-z0-9_]*',name) or name in seen
                or entry.get('path')!=name+'.php' or entry.get('expected') not in ('pass','fail')
                or entry.get('expected_internal') not in ('pass','fail') or not isinstance(targets,list)
                or not targets or not all(isinstance(cid,str) for cid in targets)
                or len(set(targets))!=len(targets) or not set(targets)<=cases or not isinstance(evidence,dict)):
            raise ValueError('Invalid v2 control metadata: '+str(name))
        seen.add(name);source=(folder/(name+'.php')).read_bytes()
        if hashlib.sha256(source).hexdigest()!=entry.get('sha256'):raise ValueError('Stored v2 control changed: '+name)
        if entry.get('internal_target_case_ids')!=sorted(internal.intersection(targets)):
            raise ValueError('Incorrect internal control targets: '+name)
        if entry['expected']=='pass':
            if set(targets)!=cases or entry['expected_internal']!='pass' or evidence or entry.get('base_control') is not None:
                raise ValueError('Invalid positive control: '+name)
            diff=''
        else:
            if (entry.get('base_control')!='eloquent' or set(evidence)!=set(targets)
                    or entry['expected_internal']=='fail' and not entry['internal_target_case_ids']):
                raise ValueError('Missing negative targets: '+name)
            for marker in evidence.values():
                if (not isinstance(marker,dict) or not isinstance(marker.get('phase'),str) or not marker['phase']
                        or type(marker.get('http_status')) is not int or not 100<=marker['http_status']<500):
                    raise ValueError('Invalid failure evidence: '+name)
            diff=(folder/(name+'.diff')).read_bytes().decode('utf-8')
        controls.append({k:v for k,v in entry.items() if k!='path'}|{'source':source.decode('utf-8'),'diff':diff})
    if [c['control_id'] for c in controls if c['expected']=='pass']!=['eloquent','explicit']:
        raise ValueError('Both positive implementation styles are required.')
    base=next(c['source'] for c in controls if c['control_id']=='eloquent')
    for control in controls:
        if control['expected']=='fail':
            expected=''.join(difflib.unified_diff(base.splitlines(True),control['source'].splitlines(True),fromfile='eloquent.php',tofile=control['control_id']+'.php'))
            if not expected or control['diff']!=expected:raise ValueError('Control diff does not match source: '+control['control_id'])
    return controls

def matrix_rows(resource,controls=None):
    controls=control_catalog(resource) if controls is None else controls
    rows=traceability(resource)
    for row in rows:
        negatives=[c for c in controls if c['expected']=='fail' and row['case_id'] in c['target_case_ids']]
        row['negative_control_ids']=[c['control_id'] for c in negatives]
        row['negative_controls']=[{'control_id':c['control_id'],'sha256':c['sha256'],'expected_evidence':c['failure_evidence'][row['case_id']]} for c in negatives]
        row['positive_controls']=[{'control_id':c['control_id'],'sha256':c['sha256']} for c in controls if c['expected']=='pass']
    return rows

def materialize_controls(resource,destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    result={'resource':resource,'package':'final-v2','prepared_by':'OpenAI Codex','human_review_completed':False,'controls':[]}
    for control in control_catalog(resource):
        name=control['control_id']
        with (destination/(name+'.php')).open('x',encoding='utf-8',newline='\n') as stream:stream.write(control['source'])
        if control['diff']:
            with (destination/(name+'.diff')).open('x',encoding='utf-8',newline='\n') as stream:stream.write(control['diff'])
        result['controls'].append({k:v for k,v in control.items() if k not in ('source','diff')}|{'path':name+'.php'})
    with (destination/'catalog.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    return result
