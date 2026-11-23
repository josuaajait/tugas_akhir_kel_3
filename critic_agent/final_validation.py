"""Pre-freeze evaluator validation; no Qwen generation or human attestation."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from uuid import uuid4

from .console import progress
from .final_package import PACKAGE, ROOT, RESOURCES, package_manifest, suite_cases, test_id, traceability
from .final_controls import control_catalog, materialize_controls, matrix_rows
from .final_sandbox import FinalRunner, build_final, render_final, verify_base
from .sandbox import SandboxError


def _write(path, value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def local_checks(meta, folder):
    """Only lint, dataset declarations and trusted response assertions run on host."""
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    result={'status':'ERROR','linted_php':0,'providers':{},'assertion_probes':{}}
    try:
        resource=meta['spec']['resource']
        controls=control_catalog(resource)
        expected_files={'catalog.json'}|{c['control_id']+'.php' for c in controls}|{c['control_id']+'.diff' for c in controls if c['diff']}
        if {p.name for p in (PACKAGE/'controls'/resource).iterdir()}!=expected_files:
            raise ValueError('Daftar aset kontrol tersimpan tidak cocok katalog.')
        for control in controls:
            saved=PACKAGE/'controls'/resource/(control['control_id']+'.php')
            if not saved.is_file() or hashlib.sha256(saved.read_bytes()).hexdigest()!=control['sha256']:
                raise ValueError('Kontrol tersimpan hilang/berubah: '+str(saved))
            diff=PACKAGE/'controls'/resource/(control['control_id']+'.diff')
            if control['diff'] and (not diff.is_file() or diff.read_text(encoding='utf-8')!=control['diff']):
                raise ValueError('Diff mutasi tersimpan tidak cocok: '+control['control_id'])
        saved_catalog=json.loads((PACKAGE/'controls'/resource/'catalog.json').read_text(encoding='utf-8'))
        expected_catalog=[{k:v for k,v in c.items() if k not in ('source','diff')}|{'path':c['control_id']+'.php'} for c in controls]
        if saved_catalog['controls']!=expected_catalog:raise ValueError('Katalog kontrol tersimpan tidak cocok.')
        saved_matrix=json.loads((PACKAGE/'traceability'/(resource+'.json')).read_text(encoding='utf-8'))
        if saved_matrix!=matrix_rows(resource,controls):raise ValueError('Matriks tersimpan tidak cocok.')
        sources={c['control_id']:c['source'] for c in controls}
        for role in ('internal','reference'):
            files=render_final(resource,role)
            context=folder/role;context.mkdir()
            for name,source in files.items():
                path=context/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(source.encode())
                if name.endswith('.php'):sources[role+'/'+name]=source
            cls='FinalInternalTest' if role=='internal' else 'FinalReferenceTest'
            script="require $argv[1]; require $argv[2]; echo json_encode(array_keys(FinalEvaluation\\"+cls+"::cases()));"
            deployed=context/'final'/(cls+'.php')
            discovery="require $argv[1]; $c=(new PHPUnit\\Runner\\TestSuiteLoader)->load($argv[2]); echo $c->getShortName();"
            found=subprocess.run(['php','-r',discovery,str(ROOT/'harness/laravel/vendor/autoload.php'),str(deployed.resolve())],capture_output=True,timeout=30,shell=False)
            if found.returncode or found.stdout.decode()!=cls:raise ValueError('Discovery PHPUnit gagal: '+(found.stdout+found.stderr).decode(errors='replace'))
            provider=subprocess.run(['php','-r',script,str(ROOT/'harness/laravel/vendor/autoload.php'),str(deployed.resolve())],capture_output=True,timeout=30,shell=False)
            if provider.returncode:raise ValueError('Enumerasi provider gagal: '+provider.stderr.decode(errors='replace'))
            actual=json.loads(provider.stdout)
            expected=[c['case_id'] for c in suite_cases(meta['spec'],meta['profile'],role=='internal')]
            if actual!=expected:raise ValueError('Daftar provider tidak sesuai matriks.')
            result['providers'][role]={'count':len(actual),'case_ids':actual}
            probe=subprocess.run(['php',str(PACKAGE/'assertion-probe.php'),str(ROOT/'harness/laravel/vendor/autoload.php'),str(PACKAGE/role/'Assertions.php')],capture_output=True,timeout=30,shell=False)
            if probe.returncode:raise ValueError('Probe assertion gagal: '+(probe.stdout+probe.stderr).decode(errors='replace'))
            result['assertion_probes'][role]=json.loads(probe.stdout)
        for name,source in sources.items():
            lint=subprocess.run(['php','-n','-l'],input=source.encode(),capture_output=True,timeout=15,shell=False)
            if lint.returncode:raise ValueError('PHP lint gagal: '+name+' '+(lint.stdout+lint.stderr).decode(errors='replace'))
            result['linted_php']+=1
        result['status']='LOCAL_VALIDATED'
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        result['reason']=str(exc)
    _write(folder/'local.json',result)
    return result


def assess_observation(meta, role, control, raw, pinned):
    unknown=lambda reason:{'status':'UNKNOWN','reason':reason}
    if raw.get('status')=='ERROR':return unknown(raw.get('reason','runner_error'))
    if (raw.get('image_id')!=pinned or raw.get('package_sha256')!=meta['package_sha256']
            or raw.get('suite_sha256')!=meta[role+'_sha256'] or raw.get('candidate_sha256')!=control['sha256']
            or raw.get('cleanup_exit_code')!=0):return unknown('observation_binding_or_cleanup_failed')
    expected={tuple(test_id(role,c['case_id']).values()) for c in suite_cases(meta['spec'],meta['profile'],role=='internal')}
    summary=raw.get('summary',{})
    cases=summary.get('cases',[])
    if (len(cases)!=len(expected) or {(c.get('class'),c.get('name')) for c in cases}!=expected
            or summary.get('total')!=len(expected)):return unknown('incomplete_test_cases')
    counts={outcome:sum(c.get('outcome')==outcome for c in cases) for outcome in ('passed','failure','error','skipped')}
    if sum(counts.values())!=len(expected) or any(summary.get(k)!=v for k,v in counts.items()) or counts['error'] or counts['skipped']:
        return unknown('invalid_counters_errors_or_skips')
    should_pass=control['expected']=='pass' if role=='reference' else control['expected_internal']=='pass'
    suffix='INTERNAL' if role=='internal' else 'REFERENCE'
    if raw.get('status')!=('PASSED_' if counts['failure']==0 else 'FAILED_')+suffix:
        return unknown('status_contradicts_test_cases')
    if should_pass:
        return {'status':'PASS' if not counts['failure'] else 'FAIL','reason':'positive_or_internal_control',
                'failed_case_ids':[c['name'] for c in cases if c['outcome']=='failure']}
    available={c['case_id'] for c in suite_cases(meta['spec'],meta['profile'],role=='internal')}
    target_ids=control['target_case_ids'] if role=='reference' else control['internal_target_case_ids']
    if not target_ids or not set(target_ids)<=available:return unknown('missing_explicit_targets')
    targets=[test_id(role,cid)['name'] for cid in target_ids]
    failed={c['name'] for c in cases if c['outcome']=='failure' and c.get('evidence','').strip()}
    detected=all(name in failed for name in targets)
    for cid in target_ids:
        row=next(c for c in cases if c['name']==test_id(role,cid)['name'])
        evidence=control['failure_evidence'][cid]
        marker='FINAL_ASSERTION:'+cid+':'+evidence['phase']+':HTTP'+str(evidence['http_status'])+' '
        if row['outcome']=='failure' and marker not in row.get('evidence',''):
            return unknown('failure_does_not_match_expected_assertion')
    return {'status':'PASS' if detected else 'FAIL','reason':'intended_targets_detected' if detected else 'intended_target_survived',
            'target_test_ids':targets,'failed_case_ids':sorted(failed),
            'failure_evidence':control['failure_evidence']}


def _signature(raw):
    return (raw.get('status'),sorted((c.get('class'),c.get('name'),c.get('outcome')) for c in raw.get('summary',{}).get('cases',[])))


def validate_final(output_root, *, resources=None, build=False, local_only=False,
                   base_image='critic-laravel:dev',timeout=120,build_timeout=600,
                   runner_factory=None,builder=None):
    if any(type(value) not in (int,float) or not math.isfinite(value) or value<=0 for value in (timeout,build_timeout)):
        raise ValueError('Timeout validasi/build harus positif dan berhingga.')
    names=list(RESOURCES if resources is None else resources)
    if not names or len(names)!=len(set(names)) or any(n not in RESOURCES for n in names):
        raise ValueError('Pilih resource final-v1 yang unik dan dikenal.')
    if local_only and build:raise ValueError('--local-only tidak dapat digabung --build.')
    output_root=Path(output_root).resolve()
    if any(output_root.is_relative_to(ROOT/p) for p in ('evaluation','critic_agent','harness','resource_templates','tests','.git')) or ',' in str(output_root):
        raise ValueError('Output validasi harus terpisah dari sumber dan tanpa koma.')
    runner_factory=runner_factory or FinalRunner;builder=builder or build_final
    folder=output_root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_final-validation_'+uuid4().hex)
    folder.mkdir(parents=True,exist_ok=False)
    report={'package':'final-v1','stage':'pre_freeze_validation','created_at':datetime.now(timezone.utc).isoformat(),
            'status':'RUNNING','functional_validation':'NOT_RUN','ready_for_final':False,
            'human_review':'pending','package_sha256':None,'resources':[],
            'run_directory':str(folder),'source_hashes':{}}
    for resource in names:
        report['resources'].append({'resource':resource,'planned_controls':None,'observations':[],
                                    'readiness':{},'builds':{},'status':'PENDING'})
    _write(folder/'validation.json',report)
    prepared={}
    try:
        initial=package_manifest(names[0])
        report.update(package_sha256=initial['package_sha256'],source_hashes=initial['source_hashes'],
                      canonical_source_hashes=initial['canonical_source_hashes'])
        for name,expected in initial['source_hashes'].items():
            data=(ROOT/name).read_bytes()
            if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Source changed while snapshotting: '+name)
            target=folder/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        # Complete all local work even when Docker is unavailable.
        for entry in report['resources']:
            resource=entry['resource'];current=folder/resource
            try:
                progress('Final-v1 '+resource+': memeriksa aset, assertion dan dataset lokal...')
                meta=package_manifest(resource);controls=control_catalog(resource)
                entry.update(planned_controls=len(controls),spec_sha256=meta['spec_sha256'],
                             internal_tests=meta['internal_tests'],reference_tests=meta['reference_tests'])
                current.mkdir()
                materialize_controls(resource,current/'controls')
                rows=matrix_rows(resource,controls)
                _write(current/'spec.json',meta['spec']);_write(current/'profile.json',meta['profile'])
                _write(current/'traceability.json',rows)
                entry['local']=local_checks(meta,current/'local')
                entry['status']=entry['local']['status']
                if entry['status']=='LOCAL_VALIDATED':prepared[resource]=(meta,controls,rows)
            except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired,SandboxError) as exc:
                entry.update(status='ERROR',reason=str(exc))
            _write(folder/'validation.json',report)
        if not local_only:
            report['functional_validation']='INCOMPLETE'
            if build:
                report['base_runtime']=verify_base(base_image,folder/'base-runtime',timeout=build_timeout)
                base_image=report['base_runtime']['image_id']
            for entry in report['resources']:
                resource=entry['resource'];current=folder/resource
                if resource not in prepared:continue
                meta,controls,rows=prepared[resource]
                try:
                    runners={}
                    for role in ('internal','reference'):
                        built_image=None
                        if build:
                            progress('Final-v1 '+resource+': membangun image '+role+'...')
                            built=builder(resource,role,current/'builds',base_image=base_image,timeout=build_timeout)
                            entry['builds'][role]=json.loads((built/'build_result.json').read_text(encoding='utf-8'))|{'run_directory':str(built.resolve())}
                            if entry['builds'][role]['status']!='BUILT':raise SandboxError('Build '+role+' belum berhasil.')
                            built_image=entry['builds'][role]['image_id']
                        kwargs={'output_root':current/'docker'/role,'timeout':timeout}
                        if built_image:kwargs['image']=built_image
                        runner=runner_factory(resource,role,**kwargs)
                        ready=runner.check_reference();entry['readiness'][role]=ready
                        if ready.get('status')!='READY' or not re.fullmatch(r'sha256:[a-f0-9]{64}',ready.get('image_id','')):
                            raise SandboxError('Readiness '+role+' belum READY; lihat bukti lingkungan/image.')
                        if built_image and ready['image_id']!=built_image:raise SandboxError('Readiness tidak memakai image hasil build.')
                        runner.image=ready['image_id'];runners[role]=runner
                    if runners['internal'].image==runners['reference'].image:raise SandboxError('Image internal/acuan harus berbeda.')
                    repeats=[c for c in controls if c['expected']=='pass']+[next(c for c in controls if c['expected']=='fail')]
                    first={}
                    for repetition,selected in ((1,controls),(2,repeats)):
                        for control in selected:
                            progress('Final-v1 '+resource+': '+control['control_id']+' (pengamatan '+str(repetition)+')...')
                            for role,runner in runners.items():
                                candidate=current/'controls'/(control['control_id']+'.php')
                                if hashlib.sha256(candidate.read_bytes()).hexdigest()!=control['sha256']:raise SandboxError('Snapshot kontrol berubah.')
                                raw=runner.check_candidate(candidate)
                                assessment=assess_observation(meta,role,control,raw,runner.image)
                                key=(role,control['control_id'])
                                consistent=True if repetition==1 else first.get(key)==_signature(raw)
                                if repetition==1:first[key]=_signature(raw)
                                if not consistent:assessment={'status':'UNKNOWN','reason':'repeated_outcomes_differ'}
                                record={'control_id':control['control_id'],'role':role,'repetition':repetition,
                                        'repeat_consistent':consistent,'assessment':assessment,'raw':raw}
                                entry['observations'].append(record)
                                evidence_file='observation_'+str(len(entry['observations'])).zfill(4)+'.json'
                                _write(current/evidence_file,record)
                                for row in rows:
                                    if role=='internal' and not row['internal_test_id']:continue
                                    if control['expected']=='pass' or row['case_id'] in control['target_case_ids']:
                                        row['validation']['observations'].append({'control_id':control['control_id'],
                                            'role':role,'repetition':repetition,'status':assessment['status'],'evidence':evidence_file})
                                _write(current/'traceability.json',rows)
                                _write(folder/'validation.json',report)
                    outcomes=[r['assessment']['status'] for r in entry['observations']]
                    entry['status']='ERROR' if 'UNKNOWN' in outcomes else 'FAILED' if 'FAIL' in outcomes else 'VALIDATED'
                    for row in rows:
                        values=[r['status'] for r in row['validation']['observations']]
                        row['validation']['status']='UNKNOWN' if 'UNKNOWN' in values else 'FAIL' if 'FAIL' in values else 'PASS' if values else 'PENDING'
                    _write(current/'traceability.json',rows)
                except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired,SandboxError) as exc:
                    entry.update(status='ERROR',reason=str(exc))
                _write(folder/'validation.json',report)
        if package_manifest(names[0])['package_sha256']!=report['package_sha256']:
            raise ValueError('package_changed_during_validation')
    except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired,SandboxError) as exc:
        report.update(status='ERROR',reason=str(exc))
    finally:
        statuses=[r['status'] for r in report['resources']]
        if report['status']!='ERROR':
            report['status']='ERROR' if any(s in ('ERROR','PENDING') for s in statuses) else 'FAILED' if 'FAILED' in statuses else 'LOCAL_VALIDATED' if local_only else 'VALIDATED'
        known=all(r['planned_controls'] is not None for r in report['resources'])
        report['planned']=sum(2*(r['planned_controls']+3) for r in report['resources']) if known else None
        report['executed']=sum(len(r['observations']) for r in report['resources'])
        report['unexecuted']=report['planned']-report['executed'] if known else None
        if not local_only and (not known or report['unexecuted']!=0):
            report['status']='ERROR'
            report.setdefault('reason','incomplete_observation_plan')
        report['counts']={status:sum(o['assessment']['status']==status for r in report['resources'] for o in r['observations']) for status in ('PASS','FAIL','UNKNOWN')}
        for entry in report['resources']:
            entry['planned']=2*(entry['planned_controls']+3) if entry['planned_controls'] is not None else None
            entry['executed']=len(entry['observations'])
            entry['unexecuted']=entry['planned']-entry['executed'] if entry['planned'] is not None else None
        if not local_only and known and report['unexecuted']==0 and report['counts']['UNKNOWN']==0:
            report['functional_validation']='COMPLETE'
        _write(folder/'validation.json',report)
    return folder
