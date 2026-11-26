"""Read-only final A/B execution gate. Never creates review or frozen data."""
from datetime import datetime
import math
from pathlib import Path
import random
import re
from urllib.parse import urlparse

from .ab_archive import ROOT, engine_manifest, local_path, read_json, sha
from .final_package import RESOURCES, package_manifest, suite_cases
from .eval_registry import get_package_api,get_sandbox_api
from .ollama import OllamaClient, ModelError


def _date(value):
    try:
        result=datetime.fromisoformat(value.replace('Z','+00:00'))
        return result if result.utcoffset() is not None else None
    except (ValueError,TypeError,AttributeError):return None


def _people(record,when):
    author,reviewer=record.get('human_author'),record.get('reviewer')
    stamp=_date(record.get('reviewed_at'))
    return (isinstance(author,str) and bool(author.strip()) and isinstance(reviewer,str)
            and bool(reviewer.strip()) and author.strip().casefold()!=reviewer.strip().casefold()
            and stamp is not None and when is not None and stamp<=when)


def review_issues(root,frozen_at,attestations=None,version='final-v1'):
    issues=[];when=_date(frozen_at)
    api=get_package_api(version)
    records=attestations if isinstance(attestations,list) else []
    if len(records)!=len(RESOURCES) or {r.get('resource') for r in records}!=set(RESOURCES):
        issues.append('five_external_review_attestations')
    for resource in RESOURCES:
        try:
            bindings=[r for r in records if r.get('resource')==resource]
            if len(bindings)!=1:raise ValueError('Missing/duplicate external review.')
            binding=bindings[0];file=local_path(root,binding['path'])
            packet=Path(root)/'evaluation'/version
            if file.is_relative_to(packet.resolve()) or sha(file)!=binding['sha256']:
                raise ValueError('Reviews must be external, hash-bound records.')
            review=read_json(file)
            meta=api.package_manifest(resource)
            expected={c['case_id'] for c in api.suite_cases(meta['spec'],meta['profile'])}
            decisions=review.get('decisions',[])
            if (review.get('resource')!=resource or review.get('status')!='reviewed' or not _people(review,when)
                    or review.get('package_sha256')!=meta['package_sha256']
                    or review.get('spec_sha256')!=meta['spec_sha256']
                    or review.get('blank_form_sha256')!=sha(packet/'review'/(resource+'.json'))
                    or len(decisions)!=len(expected) or {d.get('case_id') for d in decisions}!=expected
                    or any(d.get('decision')!='approved' or not isinstance(d.get('rationale'),str)
                           or not d['rationale'].strip() for d in decisions)):
                issues.append('human_review_'+resource)
        except (OSError,ValueError,KeyError,TypeError,AttributeError):issues.append('human_review_'+resource)
    return issues


def _configuration(plan):
    cfg=plan.get('configuration')
    if not isinstance(cfg,dict):return None
    options=cfg.get('options',{})
    endpoint=urlparse(cfg.get('endpoint',''))
    digest=cfg.get('model_digest')
    if (not isinstance(cfg.get('model'),str) or not cfg['model'].strip()
            or not isinstance(digest,str) or not re.fullmatch(r'(?:sha256:)?[a-f0-9]{64}',digest)
            or endpoint.scheme!='http' or endpoint.hostname not in ('localhost','127.0.0.1','::1')
            or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment or endpoint.path not in ('','/')
            or set(options)!= {'temperature','num_ctx','num_predict'}
            or type(options.get('temperature')) not in (int,float) or not math.isfinite(options['temperature'])
            or not 0<=options['temperature']<=2 or any(type(options.get(k)) is not int or options[k]<=0 for k in ('num_ctx','num_predict'))
            or cfg.get('max_revisions')!=3
            or any(type(cfg.get(k)) not in (int,float) or not math.isfinite(cfg[k]) or cfg[k]<=0
                   for k in ('model_timeout_seconds','test_timeout_seconds'))):return None
    return cfg


def check_protocol(path,*,root=ROOT):
    path=Path(path).resolve();root=Path(root).resolve()
    result={'status':'BLOCKED','integrity':'VERIFIED','ready_for_final':False,'pending':[],
            'manifest':str(path),'manifest_sha256':sha(path),'planned_pairs':0}
    try:
        plan=read_json(path);result['plan']=plan
        api=get_package_api(plan.get('package'))
        entries=plan.get('specifications');schedule=plan.get('schedule')
        if not isinstance(entries,list) or len(entries)!=5 or not isinstance(schedule,list) or len(schedule)!=20:
            raise ValueError('Final protocol must contain five specifications and20 pair slots.')
        slots={};resources=set()
        for item in entries:
            slot=item['slot']
            if slot in slots:raise ValueError('Duplicate spec slot.')
            spec_path=local_path(root,item['spec_path'])
            from .spec import load_spec
            spec=load_spec(spec_path);meta=api.package_manifest(spec['resource']);resources.add(spec['resource'])
            if (spec!=meta['spec'] or sha(spec_path)!=item['spec_sha256'] or item['spec_sha256']!=meta['spec_sha256']
                    or plan.get('package_sha256')!=meta['package_sha256']
                    or any(item[role+'_suite_sha256']!=meta[role+'_sha256'] for role in ('internal','reference'))):
                raise ValueError('Spec/package/suite binding changed: '+slot)
            if (any(not re.fullmatch(r'sha256:[a-f0-9]{64}',item.get(role+'_image_id','')) for role in ('internal','reference'))
                    or item['internal_image_id']==item['reference_image_id']):raise ValueError('Invalid role image IDs.')
            slots[slot]=item
        if resources!=set(RESOURCES):raise ValueError('Protocol must cover each final resource once.')
        seen=set();repetitions={key:set() for key in slots}
        for job in schedule:
            if not isinstance(job.get('pair_slot'),str) or not re.fullmatch(r'P[0-9]{2,}',job['pair_slot']):raise ValueError('Unsafe pair slot.')
            if job['pair_slot'] in seen or job['spec_slot'] not in slots:raise ValueError('Unknown/duplicate pair slot.')
            seen.add(job['pair_slot']);reps=repetitions[job['spec_slot']]
            if type(job['repetition']) is not int or job['repetition'] not in (1,2,3,4) or job['repetition'] in reps:
                raise ValueError('Invalid/duplicate repetition.')
            reps.add(job['repetition'])
            seeds=job['revision_seeds']
            if not isinstance(seeds,list) or len(seeds)!=3 or any(type(v) is not int or v<0 for v in [job['seed'],job['order_seed'],*seeds]):
                raise ValueError('Invalid initial/order/revision seeds.')
            order=['A','B'];random.Random(job['order_seed']).shuffle(order)
            if order!=job['order']:raise ValueError('Declared order differs from order seed.')
        if any(reps!={1,2,3,4} for reps in repetitions.values()):raise ValueError('Incomplete repetitions.')
        result['planned_pairs']=len(schedule)
        pending=result['pending']
        if plan.get('status')!='FROZEN' or plan.get('ready_for_final') is not True:pending.append('protocol_not_frozen')
        if _configuration(plan) is None:pending.append('final_configuration')
        if not _date(plan.get('frozen_at')):pending.append('frozen_timestamp')
        if plan.get('engine_source_sha256')!=engine_manifest()[0]:pending.append('prototype_source_freeze')
        pending.extend(review_issues(root,plan.get('frozen_at'),plan.get('review_attestations'),plan['package']))
        decisions=plan.get('decisions',{})
        if not isinstance(decisions,dict) or decisions.get('status')!='approved' or not _people(decisions,_date(plan.get('frozen_at'))):
            pending.append('reviewed_K2_FR20_component_decisions')
        else:
            k2=decisions.get('k2',{})
            if (decisions.get('fr20')!='execute' or decisions.get('component_review')!='reviewed'
                    or set(k2)!={'precision_min_percent','recall_min_percent','fpr_max_percent'}
                    or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=100 for v in k2.values())):
                pending.append('reviewed_K2_FR20_component_decisions')
        evidence=plan.get('validation_evidence',{})
        artifacts=plan.get('artifacts',[])
        required={item['path'] for item in plan.get('review_attestations',[])}
        if not isinstance(evidence,dict) or not evidence.get('path'):pending.append('final_suite_validation_evidence')
        else:
            required.add(evidence['path'])
            record=local_path(root,evidence['path'])
            if not record.is_file() or sha(record)!=evidence.get('sha256'):raise ValueError('Validation evidence hash changed.')
            validated=read_json(record)
            if validated.get('package_sha256')!=plan['package_sha256'] or validated.get('status')!='VALIDATED':
                raise ValueError('Validation evidence is not for this package.')
            bindings={r['resource']:r for r in validated['resources']}
            for entry in entries:
                resource=load_spec(local_path(root,entry['spec_path']))['resource']
                if any(bindings[resource][role+'_image_id']!=entry[role+'_image_id'] for role in ('internal','reference')):
                    raise ValueError('Validation image differs from execution image.')
        if not isinstance(artifacts,list) or not artifacts:pending.append('review_evidence_artifacts')
        else:
            indexed={}
            for artifact in artifacts:
                name=artifact['path'];file=local_path(root,name)
                if name in indexed or not file.is_file() or sha(file)!=artifact['sha256']:raise ValueError('Review/protocol artifact changed.')
                indexed[name]=artifact['sha256']
            if not required<=indexed.keys():pending.append('review_evidence_artifacts')
            if any(indexed.get(item['path'])!=item['sha256'] for item in plan.get('review_attestations',[])):
                raise ValueError('External review binding differs from artifact index.')
            decision_path=decisions.get('evidence_path') if isinstance(decisions,dict) else None
            if not decision_path or decision_path not in indexed:pending.append('decision_evidence_artifact')
            elif read_json(local_path(root,decision_path))!={k:v for k,v in decisions.items() if k!='evidence_path'}:
                raise ValueError('Decision record differs from its evidence file.')
        result['pending']=sorted(set(pending))
        if not pending:result.update(status='READY',ready_for_final=True)
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        result.update(status='BLOCKED',integrity='FAILED',detail=str(exc))
    return result


class FrozenClient:
    def __init__(self,client,digest,guard=None):self.client=client;self.digest=digest;self.guard=guard
    def __getattr__(self,name):return getattr(self.client,name)
    def verify(self):
        if self.guard:self.guard()
        identity=self.client.model_identity()
        if identity.get('status')!='observed' or identity.get('digest','').removeprefix('sha256:')!=self.digest.removeprefix('sha256:'):
            raise ModelError('Actual model digest/identity differs from frozen protocol.')
        return identity
    def generate(self,prompt):
        self.client.last_transport_attempts=[]
        self.verify();result=self.client.generate(prompt)
        try:self.verify()
        except ModelError as exc:raise ModelError(str(exc),response=result) from exc
        return result


_ACTIVE_PERMITS={}


def validate_final_context(context,spec,client,runner,reference):
    if not isinstance(context,dict) or not context.get('protocol_path'):raise ValueError('Final execution requires a frozen protocol.')
    permit=_ACTIVE_PERMITS.get(context.get('_permit'))
    if not permit or str(Path(context['protocol_path']).resolve())!=str(permit['path']):
        raise ValueError('Final execution must use an exclusively claimed protocol slot.')
    checked=check_protocol(context['protocol_path'])
    if checked['status']!='READY':raise ValueError('Final protocol is blocked: '+', '.join(checked['pending']))
    if checked['manifest_sha256']!=permit['sha256'] or context.get('pair_slot')!=permit['slot']:
        raise ValueError('Claimed protocol/slot changed.')
    plan=checked['plan'];job=next((j for j in plan['schedule'] if j['pair_slot']==context.get('pair_slot')),None)
    if job is None:raise ValueError('Pair slot not in frozen protocol.')
    entry=next(e for e in plan['specifications'] if e['slot']==job['spec_slot'])
    cfg=plan['configuration']
    from .spec import load_spec
    if (spec!=load_spec(local_path(ROOT,entry['spec_path'])) or runner.image!=entry['internal_image_id']
            or reference.image!=entry['reference_image_id'] or client.model!=cfg['model']
            or client.options!={**cfg['options'],'seed':job['seed']} or client.timeout!=cfg['model_timeout_seconds']
            or runner.timeout!=cfg['test_timeout_seconds'] or reference.timeout!=cfg['test_timeout_seconds']
            or client.base_url.rstrip('/')!=cfg['endpoint'].rstrip('/')):
        raise ValueError('Requested execution differs from frozen settings.')
    if (not isinstance(client,FrozenClient) or client.digest.removeprefix('sha256:')!=cfg['model_digest'].removeprefix('sha256:')
            or client.guard is not permit['guard']):raise ValueError('Final client must enforce the frozen model and source.')
    return {'package':plan['package'],'stage':'final','origin':'qwen_final','protocol_path':str(Path(context['protocol_path']).resolve()),
            'protocol_sha256':checked['manifest_sha256'],'pair_slot':job['pair_slot'],'spec_slot':job['spec_slot'],
            'schedule':job,'frozen_engine_source_sha256':plan['engine_source_sha256'],
            'model_timeout_seconds':cfg['model_timeout_seconds'],'test_timeout_seconds':cfg['test_timeout_seconds']}


def execute_protocol_pair(path,pair_slot,output_root):
    checked=check_protocol(path)
    if checked['status']!='READY':return {k:v for k,v in checked.items() if k!='plan'}
    plan=checked['plan'];job=next((j for j in plan['schedule'] if j['pair_slot']==pair_slot),None)
    if job is None:raise ValueError('Unknown pair slot.')
    claim=Path(output_root).resolve()/checked['manifest_sha256']/pair_slot
    try:claim.mkdir(parents=True,exist_ok=False)
    except FileExistsError:
        return {'status':'BLOCKED','reason':'slot_already_claimed','pair_slot':pair_slot,
                'claim_directory':str(claim),'message':'Existing work is preserved; no new initial candidate generated.'}
    from .orchestrator import _write_json
    state={'status':'RUNNING','pair_slot':pair_slot,'protocol_sha256':checked['manifest_sha256']}
    _write_json(claim/'execution.json',state)
    try:
        source=Path(path).read_bytes();(claim/'protocol.json').write_bytes(source)
        if sha(claim/'protocol.json')!=checked['manifest_sha256']:raise ValueError('Protocol changed after check.')
        return _execute_checked_pair(claim/'protocol.json',plan,job,claim,state)
    except (OSError,ValueError,ModelError) as exc:
        state.update(status='ERROR',reason=str(exc));return dict(state,claim_directory=str(claim))
    except KeyboardInterrupt:
        state.update(status='ERROR',reason='user_cancelled');raise
    finally:_write_json(claim/'execution.json',state)


def _execute_checked_pair(path,plan,job,claim,state):
    from .ab import run_ab
    from .ab_final import reference_runner
    from .spec import load_spec
    entry=next(e for e in plan['specifications'] if e['slot']==job['spec_slot']);cfg=plan['configuration']
    api=get_package_api(plan['package']);sandbox=get_sandbox_api(plan['package'])
    spec=load_spec(local_path(ROOT,entry['spec_path']))
    client=OllamaClient(model=cfg['model'],base_url=cfg['endpoint'],seed=job['seed'],
                        temperature=cfg['options']['temperature'],timeout=cfg['model_timeout_seconds'])
    client.options.update(cfg['options'])
    fingerprint=sha(path)
    def guard():
        if (sha(path)!=fingerprint or fingerprint!=state['protocol_sha256']
                or engine_manifest()[0]!=plan['engine_source_sha256']
                or api.package_manifest(spec['resource'])['package_sha256']!=plan['package_sha256']
                or client.model!=cfg['model'] or client.base_url.rstrip('/')!=cfg['endpoint'].rstrip('/')
                or client.timeout!=cfg['model_timeout_seconds']
                or {k:v for k,v in client.options.items() if k!='seed'}!=cfg['options']
                or client.options.get('seed') not in [job['seed'],*job['revision_seeds']]
                or runner.timeout!=cfg['test_timeout_seconds'] or reference.timeout!=cfg['test_timeout_seconds']
                or runner.image!=entry['internal_image_id'] or reference.image!=entry['reference_image_id']):
            raise ModelError('Frozen protocol/source/configuration changed before or during generation.')
        if wrapped.digest.removeprefix('sha256:')!=cfg['model_digest'].removeprefix('sha256:'):
            raise ModelError('Frozen model enforcement digest changed.')
    wrapped=FrozenClient(client,cfg['model_digest'],guard)
    runner=sandbox.FinalRunner(spec['resource'],'internal',image=entry['internal_image_id'],timeout=cfg['test_timeout_seconds'])
    reference=reference_runner(plan['package'],spec['resource'],image=entry['reference_image_id'],timeout=cfg['test_timeout_seconds'])
    token=object();_ACTIVE_PERMITS[token]={'path':Path(path).resolve(),'sha256':state['protocol_sha256'],
                                        'slot':job['pair_slot'],'guard':guard}
    try:
        folder=run_ab(spec,claim,wrapped,runner,reference,kind='final',order_seed=job['order_seed'],
                      revision_seeds=job['revision_seeds'],repetition=job['repetition'],
                      final_context={'package':plan['package'],'protocol_path':str(path),'pair_slot':job['pair_slot'],'_permit':token})
    finally:_ACTIVE_PERMITS.pop(token,None)
    result=read_json(folder/'pair.json')|{'run_directory':str(folder)}
    state.update(status=result['status'],run_directory=str(folder))
    return result
