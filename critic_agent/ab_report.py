"""Evidence-checked paired A/B summaries, separate by origin and protocol."""
from collections import Counter,defaultdict
import hashlib
import json
import math
from pathlib import Path
import re

from .ab_archive import local_path,read_json,relative,sha,verify_artifacts
from .ab import _cost
from .spec import load_spec
from .generation import extract_php,ExtractionError
from .feedback import revision_prompt,build_feedback
from .prompts import build_prompt
from .final_package import suite_cases,test_id

VALID=('LOLOS','BELUM LOLOS')
STATES=('EVALUATED','ERROR','INCOMPLETE','INVALID','AMBIGUOUS')


def rate(n,d):return {'numerator':n,'denominator':d,'percent':n/d*100 if d else None}
def mean(values):return sum(values)/len(values) if values else None


def _same(a,b,label):
    if a!=b:raise ValueError(label+' differs from source evidence.')


def _file(folder,record,relative_key,absolute_key,strict=False):
    if record.get(relative_key):return local_path(folder,record[relative_key])
    if strict:raise ValueError('Final evidence requires a local relative path: '+relative_key)
    if record.get(absolute_key):return Path(record[absolute_key]).resolve()
    raise ValueError('Missing evidence path: '+relative_key)


def _code(run,name,expected):
    file=run/name
    if expected is None:
        if file.exists():raise ValueError('Code present without an archived hash: '+str(file))
    elif not file.is_file() or sha(file)!=expected:raise ValueError('Candidate code missing/changed: '+str(file))
    return expected


def _raw_binding(raw,packet,role,candidate,image):
    for key,value in [('candidate_sha256',candidate),('image_id',image),
                      ('package_sha256',packet['package_sha256']),('suite_sha256',packet[role+'_sha256'])]:
        _same(raw.get(key),value,'Raw '+role+' '+key)
    if raw.get('status')=='UNLOADABLE_CODE':return
    expected={(t['class'],t['name']) for t in (test_id(role,c['case_id']) for c in
              suite_cases(packet['spec'],packet['profile'],role=='internal'))}
    summary=raw.get('summary',{});cases=summary.get('cases',[])
    _same(summary.get('total'),packet[role+'_tests'],'Raw planned count')
    if len(cases)!=len(expected) or {(c.get('class'),c.get('name')) for c in cases}!=expected:
        raise ValueError('Raw testcase IDs differ from planned suite.')
    counts=[summary.get(k) for k in ('passed','failure','error','skipped')]
    if (any(type(n) is not int or n<0 for n in counts) or sum(counts)!=len(expected)
            or counts[2:]!=[0,0] or raw.get('cleanup_exit_code')!=0):raise ValueError('Raw outcome counters/cleanup invalid.')
    for outcome,count in zip(('passed','failure','error','skipped'),counts):
        _same(sum(c.get('outcome')==outcome for c in cases),count,'Raw '+outcome+' count')
    _same(raw.get('status'),('PASSED_' if counts[0]==len(expected) else 'FAILED_')+role.upper(),'Raw functional status')


def _response(source,code_hash):
    response=read_json(source/'response.json');data=(source/'response.txt').read_bytes()
    _same(response.get('response'),data.decode('utf-8'),'Raw response')
    try:code=extract_php(data.decode('utf-8'))
    except ExtractionError:code=None
    _same(hashlib.sha256(code.encode()).hexdigest() if code is not None else None,code_hash,'Extracted response code')
    return data.decode('utf-8')


def _evaluate(folder,path,run,hashes,expected_suite,expected_image,packet=None):
    e=read_json(path)
    if e.get('status')!='EVALUATED':return None
    total=e.get('expected_tests');image=e.get('image_id');suite=e.get('suite_sha256')
    if type(total) is not int or total<=0 or not re.fullmatch(r'sha256:[a-f0-9]{64}',image or '') or not re.fullmatch('[a-f0-9]{64}',suite or ''):
        raise ValueError('Invalid evaluator identity/count.')
    if expected_suite:_same(suite,expected_suite,'Reference suite')
    if expected_image:_same(image,expected_image,'Reference image')
    if packet:
        _same(total,packet['reference_tests'],'Planned reference count')
        _same(e.get('package_sha256'),packet['package_sha256'],'Evaluation packet')
        _same(read_json(path.parent/'source_manifest.json'),read_json(run/'run_manifest.json'),'Evaluator source manifest')
        _same(read_json(path.parent/'source_history.json'),read_json(run/'history.json'),'Evaluator source history')
        _same(load_spec(path.parent/'spec.json'),packet['spec'],'Evaluator source spec')
    result={'image_id':image,'suite_sha256':suite,'total':total}
    for position in ('initial','final'):
        value=e.get(position,{})
        _same(value.get('code_sha256'),hashes[position],position+' evaluated hash')
        passed=value.get('passed');status=value.get('status')
        if type(passed) is not int or not 0<=passed<=total or value.get('total')!=total:raise ValueError('Invalid evaluator counters.')
        allowed=('UNAVAILABLE_CODE',) if hashes[position] is None else ('PASSED_REFERENCE',) if passed==total else ('FAILED_REFERENCE','UNLOADABLE_CODE') if passed==0 else ('FAILED_REFERENCE',)
        if status not in allowed:raise ValueError('Evaluator status contradicts code/count.')
        if packet and hashes[position] is not None:
            _raw_binding(value.get('runner_result',{}),packet,'reference',hashes[position],image)
            _code(path.parent,position+'_controller.php',hashes[position])
        if packet and value.get('shared_from'):
            shared=read_json(_file(folder,value,'shared_from_path','shared_from',True))
            _same({k:v for k,v in value.items() if k not in ('shared_from','shared_from_path')},shared.get(position),'Shared reference receipt')
        if status in ('UNAVAILABLE_CODE','UNLOADABLE_CODE'):
            raw=value.get('runner_result',{})
            if passed!=0 or raw.get('executed') is not False:raise ValueError('Unexecuted code must score zero explicitly.')
            if status=='UNLOADABLE_CODE' and (raw.get('reason')!='invalid_syntax' or raw.get('cleanup_exit_code')!=0
                    or raw.get('image_id')!=image or 'Errors parsing /input/controller.php' not in raw.get('diagnostic','')):
                raise ValueError('Syntax diagnosis lacks Docker proof.')
        else:
            raw=value.get('runner_result',{});summary=raw.get('summary',{})
            counters=[summary.get(k) for k in ('passed','failure','error','skipped')]
            if (raw.get('image_id')!=image or raw.get('cleanup_exit_code')!=0 or raw.get('status')!=status
                    or summary.get('total')!=total or any(type(n) is not int or n<0 for n in counters)
                    or sum(counters)!=total or counters[0]!=passed or counters[-1]!=0):raise ValueError('Raw evaluator evidence incomplete.')
            cases=summary.get('cases')
            if cases is not None:
                if len(cases)!=total or len({(c.get('class'),c.get('name')) for c in cases})!=total:
                    raise ValueError('Duplicate/incomplete raw testcase IDs.')
                for outcome,count in zip(('passed','failure','error','skipped'),counters):
                    if sum(c.get('outcome')==outcome for c in cases)!=count:raise ValueError('Raw testcase counters changed.')
        percent=passed/total*100
        _same(value.get('pass_rate'),percent,'Reference pass rate')
        result[position]={'passed':passed,'total':total,'pass_rate':percent,'status':status,'code_sha256':hashes[position]}
    result['uplift_pp']=result['final']['pass_rate']-result['initial']['pass_rate']
    _same(e.get('uplift_pp'),result['uplift_pp'],'Reference uplift')
    return result


def _branch(folder,pair,condition,spec,packet=None):
    branch=pair.get('branches',{}).get(condition,{'status':'NOT_STARTED'})
    status=branch.get('status','NOT_STARTED')
    result={'status':status,'reason':branch.get('reason'),'evaluation':None,'cost':branch.get('cost'),
            'revision_count':None,'requires_revision':None,'evaluator_status':'NOT_RUN'}
    if status=='NOT_STARTED':return result
    if status not in (*VALID,'ERROR'):raise ValueError('Unknown branch status.')
    if not branch.get('run_path') and not branch.get('run_directory'):
        if status!='ERROR':raise ValueError('Completed branch missing its loop.')
        return result
    run=_file(folder,branch,'run_path','run_directory',packet is not None)
    if status=='ERROR' and (not (run/'run_manifest.json').is_file() or not (run/'history.json').is_file()):return result
    manifest=read_json(run/'run_manifest.json');history=read_json(run/'history.json')
    _same(load_spec(run/'spec.json'),spec,'Loop specification')
    _same(manifest.get('spec_sha256'),sha(run/'spec.json'),'Loop spec hash')
    _same(manifest.get('status'),status,'Loop manifest status');_same(history.get('status'),status,'Loop history status')
    _same(manifest.get('stop_reason'),branch.get('reason'),'Loop stop reason')
    _same(history.get('stop_reason'),branch.get('reason'),'History stop reason')
    _same(manifest.get('model'),pair['model'],'Loop model');_same(manifest.get('options'),pair['options'],'Loop options')
    _same(manifest.get('max_revisions'),pair['max_revisions'],'Loop revision budget')
    ab=manifest.get('ab',{})
    _same(ab.get('pair_id'),pair['pair_id'],'Loop pair ID');_same(ab.get('condition'),condition,'Loop condition')
    _same(ab.get('revision_seeds'),pair['revision_seeds'],'Loop revision seeds')
    attempts=history.get('attempts',[])
    if not attempts or any(a.get('iteration')!=i for i,a in enumerate(attempts)):raise ValueError('Incomplete/out-of-order loop history.')
    if len(attempts)>pair['max_revisions']+1:raise ValueError('Revision budget exceeded.')
    first=attempts[0]
    _same(first.get('code_sha256'),pair.get('initial_code_sha256'),'Shared initial code')
    hashes={'initial':_code(run,'initial_controller.php',first.get('code_sha256')),
            'final':_code(run,'final_controller.php',attempts[-1].get('code_sha256')) if status in VALID else None}
    if status in VALID:
        _same(manifest.get('final_code_available'),hashes['final'] is not None,'Final availability')
        _same(history.get('revision_count'),len(attempts)-1,'Revision count')
        if manifest.get('image_id'):_same(manifest['image_id'],pair.get('internal_image_id'),'Internal image')
        if packet:
            last=attempts[-1];reason=branch.get('reason')
            if reason=='all_checks_passed':
                if status!='LOLOS' or last.get('dynamic_status')!='PASSED_INTERNAL' or last.get('findings'):
                    raise ValueError('LOLOS lacks passing internal evidence.')
            elif reason=='identical_code':
                if (status!='BELUM LOLOS' or len(attempts)<2 or not last.get('code_sha256')
                        or last['code_sha256']!=attempts[-2].get('code_sha256')
                        or last.get('reused_from')!=len(attempts)-2 or last.get('dynamic_status')!='reused'):
                    raise ValueError('Identical-code stop lacks matching candidates.')
            elif reason=='max_revisions':
                if status!='BELUM LOLOS' or len(attempts)-1!=pair['max_revisions'] or not last.get('findings'):
                    raise ValueError('Revision-limit stop lacks failed final attempt.')
            else:raise ValueError('Unknown functional stop reason.')
    for i,attempt in enumerate(attempts):
        source=run/'attempts'/str(i)
        if packet:
            _same(read_json(source/'result.json'),attempt,'Iteration receipt')
            if (source/'response.txt').is_file():
                text=_response(source,attempt.get('code_sha256'))
                if i==0:_same(hashlib.sha256(text.encode()).hexdigest(),pair.get('initial_input_sha256'),'Shared initial response')
            if i and (source/'prompt.txt').is_file():
                prompt=(source/'prompt.txt').read_bytes().decode('utf-8')
                _same(sha(source/'prompt.txt'),attempt.get('prompt_sha256'),'Revision prompt hash')
                prior=run/'attempts'/str(i-1);feedback=read_json(prior/'feedback.json')
                previous=(prior/'response.txt').read_bytes().decode('utf-8')
                _same(prompt,revision_prompt(spec,previous,feedback),'Revision prompt replay')
                if condition=='B':
                    _same(feedback,{'message':'Keluaran ini belum lolos pemeriksaan. Periksa dan perbaiki agar sesuai spesifikasi. Kembalikan satu berkas controller PHP.'},'Generic feedback')
                else:
                    previous_attempt=attempts[i-1];dynamic=previous_attempt.get('dynamic')
                    _same(feedback,build_feedback(previous_attempt['findings'] if dynamic is None else [],dynamic,i-1),'Specific feedback')
            dynamic=attempt.get('dynamic')
            if dynamic and dynamic.get('status') in ('PASSED_INTERNAL','FAILED_INTERNAL'):
                _raw_binding(dynamic,packet,'internal',attempt.get('code_sha256'),pair.get('internal_image_id'))
            if i==0 and (source/'source_response.json').is_file():
                initial=local_path(folder,pair['initial_archive_path'])
                _same(read_json(source/'source_response.json'),read_json(initial/'response.json'),'Shared raw response')
        if attempt.get('code_sha256'):_code(source,'controller.php',attempt['code_sha256'])
        if attempt.get('model_called'):
            options=(attempt.get('model_request') or {}).get('options')
            expected=dict(pair['options'],seed=pair['revision_seeds'][i-1]) if i else pair['options']
            _same(options,expected,'Effective revision options')
        if i==0 and attempt.get('model_called') is not False:raise ValueError('Branch regenerated the shared initial candidate.')
        if pair.get('origin')=='qwen_final' and attempt.get('model_called'):
            _same(attempt.get('model_request',{}).get('timeout_seconds'),pair.get('model_timeout_seconds'),'Frozen revision timeout')
    calls=[a for a in attempts if a.get('model_called')]
    seconds=round(sum(a['elapsed_seconds'] for a in attempts),6) if all(type(a.get('elapsed_seconds')) in (int,float) and a['elapsed_seconds']>=0 for a in attempts) else None
    cost=_cost([a.get('model_request') for a in calls],[run/'attempts'/str(a['iteration'])/'response.json' for a in calls],seconds)
    if branch.get('cost') is not None:_same(branch['cost'],cost,'Branch cost')
    dynamic=first.get('dynamic',{}).get('status',first.get('dynamic_status'))
    needs=bool(first.get('findings')) or dynamic=='FAILED_INTERNAL'
    if dynamic not in ('PASSED_INTERNAL','FAILED_INTERNAL') and not first.get('findings'):needs=None
    result.update(revision_count=history.get('revision_count'),requires_revision=needs,cost=cost,
                  initial_hash=hashes['initial'],final_hash=hashes['final'],
                  initial_signature=(dynamic,[(c.get('class'),c.get('name'),c.get('outcome')) for c in first.get('dynamic',{}).get('summary',{}).get('cases',[])]),
                  model_digest=manifest.get('provenance',{}).get('model_identity',{}).get('digest'))
    if pair.get('origin')=='qwen_final':
        _same(manifest.get('model_timeout_seconds'),pair.get('model_timeout_seconds'),'Frozen loop timeout')
        _same(manifest.get('provenance',{}).get('tests',{}).get('test_timeout_seconds'),pair.get('test_timeout_seconds'),'Frozen harness timeout')
        _same(manifest.get('endpoint','').rstrip('/'),pair['frozen_endpoint'].rstrip('/'),'Frozen loop endpoint')
        if status in VALID and manifest.get('provenance',{}).get('model_identity',{}).get('status')!='observed':
            raise ValueError('Final loop lacks observed model identity.')
    evaluation=branch.get('evaluation',{})
    if status in VALID and evaluation.get('status')=='EVALUATED':
        path=_file(folder,evaluation,'report_path','report',packet is not None)
        result['evaluation']=_evaluate(folder,path,run,hashes,pair.get('reference_suite_sha256'),pair.get('reference_image_id'),packet)
        if result['evaluation'] is None:raise ValueError('Pair claims an unsuccessful evaluator as complete.')
        for name,value in [('initial_pass_rate',result['evaluation']['initial']['pass_rate']),
                           ('final_pass_rate',result['evaluation']['final']['pass_rate']),('uplift_pp',result['evaluation']['uplift_pp'])]:
            _same(evaluation.get(name),value,'Pair '+name)
    result['evaluator_status']=evaluation.get('status','NOT_RUN')
    result['evaluator_reason']=evaluation.get('reason')
    if evaluation.get('report_path'):
        _same(read_json(local_path(folder,evaluation['report_path'])).get('reason'),evaluation.get('reason'),'Evaluator reason')
    return result


def read_pair(path):
    path=Path(path).resolve();folder=path.parent;pair=read_json(path)
    row={'pair_id':pair.get('pair_id',folder.name),'report':str(path),'report_sha256':sha(path),'status':pair.get('status'),
         'kind':pair.get('kind'),
         'pair_slot':pair.get('pair_slot'),'protocol_sha256':pair.get('protocol_sha256'),
         'origin':pair.get('origin','qwen_development'),'stage':pair.get('stage','development'),
         'scenario':pair.get('scenario'),
         'package_sha256':pair.get('package_sha256'),'engine_source_sha256':pair.get('engine_source_sha256'),
         'model':pair.get('model'),'options':pair.get('options'),'max_revisions':pair.get('max_revisions'),
         'initial_hash':pair.get('initial_code_sha256'),'initial_cost':pair.get('initial_cost'),
         'branches':{},'reason':pair.get('reason'),'n_ab':0,'delta_final_pp':None,
         'initial_output_state':'NOT_STARTED',
         'internal_image_id':pair.get('internal_image_id'),'reference_image_id':pair.get('reference_image_id'),
         'internal_suite_sha256':pair.get('internal_suite_sha256'),'reference_suite_sha256':pair.get('reference_suite_sha256')}
    incomplete=pair.get('status')=='RUNNING'
    if incomplete:row['status']='INCOMPLETE'
    if pair.get('status') not in ('EVALUATED','ERROR','RUNNING'):raise ValueError('Unknown pair state.')
    packet=None
    if pair.get('kind')=='final':
        if not incomplete:verify_artifacts(folder,pair.get('artifacts'))
        if incomplete and not (folder/'package_manifest.json').is_file():return row
        packet=read_json(folder/'package_manifest.json')
        _same(packet['package_sha256'],pair['package_sha256'],'Packet hash')
        encoded=json.dumps(packet['source_hashes'],sort_keys=True).encode()
        _same(hashlib.sha256(encoded).hexdigest(),packet['package_sha256'],'Archived packet fingerprint')
        sources=pair['engine_sources']
        _same(hashlib.sha256(json.dumps(sources,sort_keys=True,separators=(',',':')).encode()).hexdigest(),pair['engine_source_sha256'],'Prototype fingerprint')
        for name,expected in sources.items():_same(sha(local_path(folder,'sources/'+name)),expected,'Prototype source')
        if pair.get('origin')=='synthetic_validation':
            if pair.get('stage')!='synthetic_validation' or pair.get('qwen_calls')!=0 or pair.get('model')!='synthetic-fixture-final-v1':
                raise ValueError('Synthetic evidence cannot be represented as Qwen/final data.')
        elif pair.get('origin')=='qwen_final':
            protocol=read_json(folder/'protocol.json')
            _same(sha(folder/'protocol.json'),pair.get('protocol_sha256'),'Protocol snapshot')
            if protocol.get('status')!='FROZEN' or protocol.get('ready_for_final') is not True:raise ValueError('Final result lacks a frozen protocol.')
            _same(protocol.get('engine_source_sha256'),pair['engine_source_sha256'],'Frozen prototype')
            if pair.get('stage')!='final':raise ValueError('Final origin requires final stage.')
            _same(protocol.get('package_sha256'),packet['package_sha256'],'Frozen package')
            jobs=[j for j in protocol['schedule'] if j['pair_slot']==pair['pair_slot']]
            if len(jobs)!=1:raise ValueError('Missing/duplicate frozen pair slot.')
            job=jobs[0]
            _same(pair.get('spec_slot'),job['spec_slot'],'Frozen spec slot')
            entries=[e for e in protocol['specifications'] if e['slot']==job['spec_slot']]
            if len(entries)!=1:raise ValueError('Missing/duplicate frozen specification.')
            entry=entries[0]
            for key in ('internal_image_id','reference_image_id','internal_suite_sha256','reference_suite_sha256'):
                _same(pair.get(key),entry[key],'Frozen '+key)
            _same(packet['spec_sha256'],entry['spec_sha256'],'Frozen spec hash')
            for key in ('revision_seeds','repetition','order_seed','order'):_same(pair.get(key),job[key],'Frozen '+key)
            _same(pair['options'],{**protocol['configuration']['options'],'seed':job['seed']},'Frozen model options')
            _same(pair['model'],protocol['configuration']['model'],'Frozen model name')
            cfg=protocol['configuration'];pair['frozen_endpoint']=cfg['endpoint']
            _same(pair['max_revisions'],cfg['max_revisions'],'Frozen revision budget')
            for key in ('model_timeout_seconds','test_timeout_seconds'):_same(pair.get(key),cfg[key],'Frozen '+key)
            if pair.get('initial_imported') is not False:raise ValueError('Final initial candidate was imported.')
            for artifact in protocol['artifacts']:_same(sha(local_path(folder,'protocol_evidence/'+artifact['path'])),artifact['sha256'],'Frozen review evidence')
        else:raise ValueError('Unknown final-package data origin.')
    if type(pair.get('max_revisions')) is not int or not 0<=pair['max_revisions']<=3 or len(pair.get('revision_seeds',[]))!=pair['max_revisions']:
        raise ValueError('Invalid revision budget/schedule.')
    spec=load_spec(folder/'spec.json');_same(pair.get('spec_sha256'),sha(folder/'spec.json'),'Pair spec hash')
    row.update(spec=spec,spec_key=hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':')).encode()).hexdigest())
    if pair.get('kind')=='final':_same(packet['spec'],spec,'Packet specification')
    order=['A','B']
    import random
    random.Random(pair.get('order_seed')).shuffle(order);_same(order,pair.get('order'),'Branch order')
    initial_path=(_file(folder,pair,'initial_archive_path','initial_generation',packet is not None)
                  if pair.get('initial_archive_path') or pair.get('initial_generation') else None)
    initial_digest=None
    if initial_path is not None and initial_path.is_dir() and (initial_path/'run_manifest.json').is_file():
        initial=read_json(initial_path/'run_manifest.json')
        row['initial_output_state']='EXTRACTED' if initial.get('code_sha256') else 'FORMAT_FAIL' if initial.get('status')=='FORMAT_FAIL' else 'ERROR'
        _same(initial.get('options'),pair['options'],'Initial model options');_same(initial.get('model'),pair['model'],'Initial model')
        _same(load_spec(initial_path/'spec.json'),spec,'Initial specification')
        _same(initial.get('code_sha256'),pair.get('initial_code_sha256'),'Initial generation code hash')
        initial_digest=initial.get('provenance',{}).get('model_identity',{}).get('digest')
        if packet:
            _same(sha(initial_path/'spec.json'),initial.get('spec_sha256'),'Initial spec hash')
            _same((initial_path/'prompt.txt').read_bytes().decode('utf-8'),build_prompt(spec),'Initial prompt')
            _same(sha(initial_path/'prompt.txt'),initial.get('prompt_sha256'),'Initial prompt hash')
            if initial.get('status')!='ERROR':
                _response(initial_path,initial.get('code_sha256'))
                _same(sha(initial_path/'response.txt'),initial.get('response_sha256'),'Initial response hash')
        if pair.get('origin')=='qwen_final':
            _same(initial.get('endpoint','').rstrip('/'),cfg['endpoint'].rstrip('/'),'Frozen initial endpoint')
            _same(initial.get('timeout_seconds'),cfg['model_timeout_seconds'],'Frozen initial timeout')
            if initial.get('status')!='ERROR' and (not initial_digest or initial.get('provenance',{}).get('model_identity',{}).get('status')!='observed'):
                raise ValueError('Final generation lacks observed model identity.')
        if initial.get('code_sha256'):
            _same(sha(initial_path/'initial_controller.php'),initial['code_sha256'],'Initial generation code')
            _same(pair.get('initial_input_sha256'),initial['code_sha256'],'Shared initial input')
        elif initial.get('status')=='FORMAT_FAIL':_same(pair.get('initial_input_sha256'),sha(initial_path/'response.txt'),'Shared invalid response')
        if pair.get('initial_cost') is not None:
            cost=_cost([initial.get('model_request')],[initial_path/'response.json'],pair['initial_cost']['attempt_seconds'])
            _same(cost,pair['initial_cost'],'Initial generation cost')
    if pair.get('kind')=='final' and (folder/'initial_cost.json').exists():
        _same(read_json(folder/'initial_cost.json')['cost'],pair.get('initial_cost'),'Initial cost receipt')
    for condition in ('A','B'):row['branches'][condition]=_branch(folder,pair,condition,spec,packet)
    a,b=(row['branches'][k] for k in ('A','B'))
    if a['status'] in VALID and b['status'] in VALID:
        _same(a['initial_signature'],b['initial_signature'],'Initial internal observations')
    if not incomplete and a['evaluation'] and b['evaluation']:
        _same(a['evaluation']['initial'],b['evaluation']['initial'],'Shared reference initial')
        _same(a['evaluation']['image_id'],b['evaluation']['image_id'],'A/B reference image')
        _same(a['evaluation']['suite_sha256'],b['evaluation']['suite_sha256'],'A/B reference suite')
        row.update(n_ab=1,delta_final_pp=a['evaluation']['final']['pass_rate']-b['evaluation']['final']['pass_rate'])
    _same(pair.get('n_ab'),row['n_ab'],'Complete A/B denominator');_same(pair.get('delta_final_pp'),row['delta_final_pp'],'A/B delta')
    if not incomplete:_same(pair['status']=='EVALUATED',row['n_ab']==1,'Pair completion status')
    digests={b['model_digest'] for b in row['branches'].values() if b.get('model_digest')}
    if initial_digest:digests.add(initial_digest)
    if len(digests)>1:raise ValueError('Model identity changed between conditions.')
    row['model_digest']=next(iter(digests),None)
    if pair.get('origin')=='qwen_final':
        expected=protocol['configuration']['model_digest'].removeprefix('sha256:')
        if any(d.removeprefix('sha256:')!=expected for d in digests):raise ValueError('Model digest differs from frozen protocol.')
        if row['n_ab'] and not digests:raise ValueError('Final model identity is missing.')
    for name in ('reference_image_id','reference_suite_sha256'):
        if row.get(name) is None:
            values={b['evaluation']['image_id' if name=='reference_image_id' else 'suite_sha256']
                    for b in row['branches'].values() if b.get('evaluation')}
            if len(values)==1:row[name]=next(iter(values))
    row['assurance']='artifact_hashes' if pair.get('artifacts') else 'legacy_source_checks'
    return row


def summarize_spec(rows):
    complete=[r for r in rows if r.get('n_ab')==1]
    result={'n_ab':len(complete),'mean_delta_final_pp':mean([r['delta_final_pp'] for r in complete]),'conditions':{},
            'pair_errors':sum(r.get('status')=='ERROR' for r in rows),
            'pair_error_reasons':dict(Counter(r.get('reason') or 'unspecified' for r in rows if r.get('status')=='ERROR'))}
    for condition in ('A','B'):
        branches=[r['branches'][condition] for r in rows if condition in r.get('branches',{})]
        valid=[b for b in branches if b['status'] in VALID];paired=[b for b in valid if b.get('evaluation')]
        failed=[b for b in paired if b['evaluation']['initial']['pass_rate']<100]
        passed=[b for b in paired if b['evaluation']['initial']['pass_rate']==100]
        revised=[b for b in valid if b['revision_count']>0];identical=sum(b['reason']=='identical_code' for b in valid)
        result['conditions'][condition]={'n_valid':len(valid),'n_pair':len(paired),
            'loop_errors':sum(b['status']=='ERROR' for b in branches),
            'evaluator_errors':sum(b['evaluator_status']=='ERROR' for b in valid),
            'mean_initial_pass_rate':mean([b['evaluation']['initial']['pass_rate'] for b in paired]),
            'mean_final_pass_rate':mean([b['evaluation']['final']['pass_rate'] for b in paired]),
            'mean_uplift_pp':mean([b['evaluation']['uplift_pp'] for b in paired]),
            'repair':rate(sum(b['evaluation']['final']['pass_rate']==100 for b in failed),len(failed)),
            'regression':rate(sum(b['evaluation']['final']['pass_rate']<100 for b in passed),len(passed)),
            'mean_revisions':mean([b['revision_count'] for b in valid]),
            'lolos':rate(sum(b['status']=='LOLOS' for b in valid),len(valid)),
            'identical_among_valid':rate(identical,len(valid)),
            'identical_among_revised':rate(identical,len(revised)),
            'stop_reasons':dict(Counter(b['reason'] or 'unspecified' for b in branches)),
            'requiring_revision':sum(b.get('requires_revision') is True for b in valid)}
        result['conditions'][condition]['cost']=_sum_costs([b['cost'] for b in branches if b.get('cost')],
                                  all(r.get('origin')=='synthetic_validation' for r in rows))
        result['conditions'][condition]['outputs']={position:dict(Counter(b['evaluation'][position]['status'] for b in paired))
                                                    for position in ('initial','final')}
        result['conditions'][condition]['evaluator_reasons']=dict(Counter(b.get('evaluator_reason') or 'unspecified'
                                                    for b in branches if b.get('evaluator_status')=='ERROR'))
    needing=[r for r in complete if r['branches']['A'].get('requires_revision') is True]
    result['requiring_revision_subset']={'n_ab':len(needing),'mean_delta_final_pp':mean([r['delta_final_pp'] for r in needing])}
    hashes=[r['initial_hash'] for r in rows if r.get('initial_hash')]
    result['initial_codes']={'extracted':len(hashes),'unique':len(set(hashes)),'duplicates':len(hashes)-len(set(hashes)),
                             'not_extracted':sum(r.get('initial_output_state')=='FORMAT_FAIL' for r in rows),
                             'generation_errors':sum(r.get('initial_output_state')=='ERROR' for r in rows),
                             'not_started':sum(r.get('initial_output_state')=='NOT_STARTED' for r in rows)}
    costs=[r['initial_cost'] for r in rows if r.get('initial_cost') is not None]
    costs += [b['cost'] for r in rows for b in r.get('branches',{}).values() if b.get('cost') is not None]
    result['cost']={'logical_generation_calls':sum(c['model_calls'] for c in costs),
                    'qwen_calls':0 if all(r.get('origin')=='synthetic_validation' for r in rows) else sum(c['model_calls'] for c in costs),
                    'receipts_with_cost':len(costs)}
    for key in ('prompt_tokens_observed','output_tokens_observed','http_attempts_observed','http_retries_observed','attempt_seconds'):
        values=[c[key] for c in costs if c.get(key) is not None]
        result['cost'][key]={'value':sum(values) if values else None,'receipts_with_value':len(values),'receipts_total':len(costs)}
    return result


def _sum_costs(costs,synthetic):
    result={'logical_generation_calls':sum(c['model_calls'] for c in costs),
            'qwen_calls':0 if synthetic else sum(c['model_calls'] for c in costs),'receipts_with_cost':len(costs)}
    for key in ('prompt_tokens_observed','output_tokens_observed','http_attempts_observed','http_retries_observed','attempt_seconds'):
        values=[c[key] for c in costs if c.get(key) is not None]
        result[key]={'value':sum(values) if values else None,'receipts_with_value':len(values),'receipts_total':len(costs)}
    return result


def macro_summary(specifications):
    eligible=[s for s in specifications if s.get('mean_delta_final_pp') is not None]
    result={'specifications':len(specifications),'specifications_with_ab':len(eligible),
            'mean_delta_final_pp':mean([s['mean_delta_final_pp'] for s in eligible]),'conditions':{}}
    for condition in ('A','B'):
        result['conditions'][condition]={}
        for metric in ('mean_initial_pass_rate','mean_final_pass_rate','mean_uplift_pp','mean_revisions'):
            values=[s.get('conditions',{}).get(condition,{}).get(metric) for s in specifications]
            values=[v for v in values if v is not None]
            result['conditions'][condition][metric]={'value':mean(values),'specifications_with_value':len(values)}
        for metric in ('repair','regression','lolos','identical_among_valid','identical_among_revised'):
            values=[s.get('conditions',{}).get(condition,{}).get(metric,{}).get('percent') for s in specifications]
            values=[v for v in values if v is not None]
            result['conditions'][condition][metric]={'value':mean(values),'specifications_with_value':len(values)}
    result['weighting']='equal_specifications'
    return result


def ab_report(runs,*,plan=None):
    root=Path(runs).resolve();rows=[]
    for path in sorted(root.rglob('pair.json')) if root.exists() else []:
        try:rows.append(read_pair(path))
        except (OSError,ValueError,KeyError,TypeError,AttributeError,IndexError,StopIteration) as exc:
            rows.append({'status':'INVALID','report':str(path),'report_sha256':sha(path),'reason':str(exc),
                         'pair_id':path.parent.name,'branches':{},'n_ab':0})
    by_id=defaultdict(list)
    for row in rows:
        if row['status']!='INVALID':by_id[row['pair_id']].append(row)
    for copies in by_id.values():
        if len(copies)>1:
            for row in copies:row.update(status='AMBIGUOUS',reason='duplicate_pair_id',n_ab=0,delta_final_pp=None)
    claims=[]
    for file in sorted(root.rglob('execution.json')) if root.exists() else []:
        try:
            claim=read_json(file)
            if claim.get('status') not in ('RUNNING','ERROR','EVALUATED') or not isinstance(claim.get('pair_slot'),str):raise ValueError('Invalid execution receipt.')
            claims.append({**claim,'report':str(file),'sha256':sha(file)})
        except (OSError,ValueError,TypeError) as exc:claims.append({'status':'INVALID','report':str(file),'reason':str(exc)})
    slots=defaultdict(lambda:{'rows':[],'claims':[]})
    for row in rows:
        if row.get('protocol_sha256') and row.get('pair_slot'):
            slots[(row['protocol_sha256'],row['pair_slot'])]['rows'].append(row)
    for claim in claims:
        if not claim.get('protocol_sha256') or not claim.get('pair_slot'):continue
        group=slots[(claim['protocol_sha256'],claim['pair_slot'])];group['claims'].append(claim)
        children=[r for r in rows if Path(r['report']).is_relative_to(Path(claim['report']).parent)]
        for child in children:
            if child not in group['rows'] or child.get('kind')!='final' or child.get('origin')!='qwen_final':
                child.update(status='INVALID',reason='execution_claim_binding_mismatch',n_ab=0,delta_final_pp=None)
    for group in slots.values():
        attempts=len(group['claims'])+sum(not any(Path(r['report']).is_relative_to(Path(c['report']).parent)
                                                for c in group['claims']) for r in group['rows'])
        if attempts>1 or len(group['rows'])>1:
            for row in group['rows']:row.update(status='AMBIGUOUS',reason='multiple_attempts_for_slot',n_ab=0,delta_final_pp=None)
            group['status']='AMBIGUOUS'
        elif group['rows']:group['status']=group['rows'][0]['status']
        else:group['status']='ERROR' if any(c['status']=='ERROR' for c in group['claims']) else 'INCOMPLETE'
        if attempts==1 and group['claims'] and group['rows'] and group['status']=='EVALUATED':
            receipt=group['claims'][0]
            if receipt['status']!='EVALUATED':
                group['status']='ERROR' if receipt['status']=='ERROR' else 'INCOMPLETE'
                group['rows'][0].update(status=group['status'],reason='execution_receipt_'+receipt['status'].lower(),n_ab=0,delta_final_pp=None)
    result={'schema_version':'1.0','runs_root':str(root),'runs_root_exists':root.exists(),
            'counts':{s:sum(r['status']==s for r in rows) for s in STATES},'pairs':rows,
            'cohorts':[],'planned_slots':[],'execution_records':claims,'ready_for_final':False}
    if plan is not None:
        proto=read_json(plan);fingerprint=sha(plan)
        result['plan']={'path':str(Path(plan).resolve()),'sha256':fingerprint,'status':proto.get('status')}
        for job in proto['schedule']:
            group=slots.get((fingerprint,job['pair_slot']),{'rows':[],'claims':[],'status':'NOT_STARTED'})
            executions=group['claims'];matches=group['rows']
            result['planned_slots'].append({'pair_slot':job['pair_slot'],'spec_slot':job['spec_slot'],
                'status':group['status'],
                'attempt_reports':[r['report'] for r in matches],'execution_reports':[c['report'] for c in executions]})
        result['plan_summary']={'planned':len(proto['schedule']),
            'n_ab':sum(s['status']=='EVALUATED' for s in result['planned_slots']),
            'counts':dict(Counter(s['status'] for s in result['planned_slots']))}
    cohorts=defaultdict(list)
    for row in rows:
        if row['status'] not in ('EVALUATED','ERROR','INCOMPLETE') or not row.get('spec'):continue
        opts={k:v for k,v in (row.get('options') or {}).items() if k!='seed'}
        key=(row.get('origin'),row.get('stage'),row.get('package_sha256'),row.get('protocol_sha256'),
             row.get('engine_source_sha256'),row.get('model'),row.get('model_digest'),json.dumps(opts,sort_keys=True),row.get('max_revisions'),row.get('scenario'))
        cohorts[key].append(row)
    for key,members in cohorts.items():
        groups=defaultdict(list)
        for row in members:
            identities=tuple(row.get(k) for k in ('internal_image_id','reference_image_id','internal_suite_sha256','reference_suite_sha256'))
            groups[(row.get('spec_key'),identities)].append(row)
        specs=[]
        for _,group in groups.items():
            summary=summarize_spec(group);summary.update(spec=group[0]['spec'],spec_key=group[0]['spec_key'],pair_ids=[r['pair_id'] for r in group])
            specs.append(summary)
        mixed=len({s['spec_key'] for s in specs})!=len(specs)
        result['cohorts'].append({'origin':key[0],'stage':key[1],'package_sha256':key[2],'protocol_sha256':key[3],
            'engine_source_sha256':key[4],'model':key[5],'model_digest':key[6],'options':json.loads(key[7]),
            'max_revisions':key[8],'scenario':key[9],'specifications':specs,'mixed_spec_configurations':mixed,
            'macro':None if mixed else macro_summary(specs)})
    result['counts']={s:sum(r['status']==s for r in rows) for s in STATES}
    return result
