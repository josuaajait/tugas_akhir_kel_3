"""Code-only Critic predictions and separately collected independent evidence."""
import copy
from datetime import datetime, timezone
import platform
from pathlib import Path
import re
import time

from .component_corpus import (PROTOCOL, load_corpus, snapshot_corpus, write_json, sha,
                               reference_contract, validate_reference_evidence)
from .feedback import collect_findings
from .reference import ReferenceDockerRunner
from .resource_reference import ResourceReferenceRunner
from .resources import ResourceDockerRunner
from .sandbox import DockerRunner, SandboxError, validate_products_contract
from .static import analyze, StaticEnvironmentError

ROOT = Path(__file__).resolve().parents[1]


def internal_runner(spec, output_root):
    if spec['resource'] == 'products':
        validate_products_contract(spec)
        return DockerRunner(output_root=output_root)
    return ResourceDockerRunner(spec, output_root=output_root)


def reference_runner(spec, output_root):
    if spec['resource'] == 'products':
        validate_products_contract(spec)
        return ReferenceDockerRunner(output_root=output_root)
    return ResourceReferenceRunner(spec, output_root=output_root)


def engine_hash():
    digest = []
    for name in ('component_corpus.py','component_evaluation.py','component_report.py','static.py','feedback.py',
                 'sandbox.py','resources.py','process.py','spec.py'):
        digest.append(name+'\0'+(ROOT/'critic_agent'/name).read_text(encoding='utf-8').replace('\r\n','\n'))
    return sha('\0'.join(digest).encode())


def _complete(raw, count, reference=False):
    summary = raw.get('summary', {})
    numbers = [summary.get(key) for key in ('passed','failure','error','skipped')]
    if (type(raw.get('cleanup_exit_code')) is not int or raw['cleanup_exit_code']!=0
            or summary.get('total') != count or any(type(n) is not int or n < 0 for n in numbers)
            or sum(numbers) != count or summary['skipped'] != 0):
        return False
    suffix = 'REFERENCE' if reference else 'INTERNAL'
    expected = 'PASSED_'+suffix if summary['passed'] == count else 'FAILED_'+suffix
    return raw.get('status') == expected


def _bind(raw, code_hash, pinned, runner):
    image_id = raw.get('image_id')
    if not isinstance(image_id, str) or not re.fullmatch('sha256:[a-f0-9]{64}', image_id):
        raise SandboxError('Image ID hasil kandidat tidak tersedia/invalid.')
    if pinned is not None and image_id != pinned:
        raise SandboxError('Image berubah di dalam satu eksekusi komponen.')
    if raw.get('candidate_sha256') != code_hash:
        raise SandboxError('Hasil runner tidak terikat pada hash kandidat yang diuji.')
    if type(raw.get('cleanup_exit_code')) is not int or raw['cleanup_exit_code']!=0:
        raise SandboxError('Cleanup kandidat tidak berhasil.')
    runner.image = image_id
    return image_id


def run_components(manifest_path, output_root, *, static_analyzer=analyze, runner_factory=internal_runner, timeout=120):
    DockerRunner(timeout=timeout)  # Validate numeric configuration without contacting Docker.
    loaded = load_corpus(manifest_path)
    folder = snapshot_corpus(loaded, output_root, 'component')
    frozen = load_corpus(folder/'corpus.json')
    started = datetime.now(timezone.utc).isoformat()
    manifest = {'protocol_version':PROTOCOL,'engine_sha256':engine_hash(),'created_at':started,'status':'RUNNING',
                'source_manifest_sha256':loaded['manifest_sha256'],'source_manifest':str(loaded['manifest_path']),
                'corpus_sha256':sha((folder/'corpus.json').read_bytes()),'timeout_seconds':timeout,
                'environment':{'python':platform.python_version(),'platform':platform.platform()},
                'backend':'default_php_docker' if static_analyzer is analyze and runner_factory is internal_runner else 'injected_or_custom'}
    write_json(folder/'run_manifest.json', manifest)
    rows, cache, runners, pinned = [], {}, {}, {}
    for record in frozen['records']:
        case = record['case']
        spec_key, key = case['spec_sha256'], (case['spec_sha256'],case['code_sha256'])
        row = {k:case[k] for k in ('case_id','corpus','spec_sha256','code_sha256')}
        start = time.monotonic()
        if key in cache:
            original, result = cache[key]
            row.update(copy.deepcopy(result), reused_from=original, executed=False)
        else:
            result = {'prediction':'unknown','status':'ERROR','findings':[], 'executed':True}
            try:
                # Ground truth/review/provenance are never arguments to either checker.
                static = static_analyzer(record['code'].decode('utf-8'), record['spec'])
                result['static'] = static
                findings = collect_findings(static['findings'], None)
                if findings:
                    result.update(prediction='problematic',status='PREDICTED',findings=findings,reason='static_findings')
                else:
                    if spec_key not in runners:
                        runners[spec_key] = runner_factory(record['spec'], folder/'harness'/record['spec']['spec_id'])
                        runners[spec_key].timeout = timeout
                    runner = runners[spec_key]
                    raw = runner.check_candidate(folder/case['code_path'])
                    result['dynamic'] = raw
                    if not _complete(raw, runner.candidate_tests):
                        raise SandboxError('Hasil internal ERROR/parsial/skipped atau counter/status bertentangan.')
                    pinned[spec_key] = _bind(raw,case['code_sha256'],pinned.get(spec_key),runner)
                    findings = collect_findings([],raw)
                    positive = raw['status'] == 'FAILED_INTERNAL'
                    if positive and not findings:
                        raise SandboxError('Status gagal tanpa bukti temuan Critic.')
                    result.update(prediction='problematic' if positive else 'correct',status='PREDICTED',
                                  findings=findings,reason='internal_findings' if positive else 'all_internal_passed')
            except (SandboxError, StaticEnvironmentError, OSError, ValueError) as exc:
                result.update(reason='prediction_error',detail=str(exc))
            cache[key] = (case['case_id'], copy.deepcopy(result))
            row.update(result)
        row['elapsed_seconds'] = round(time.monotonic()-start,6)
        write_json(folder/'cases'/case['case_id']/'prediction.json', row)
        rows.append(row)
    write_json(folder/'predictions.json', {'protocol_version':PROTOCOL,'cases':rows})
    manifest.update(status='ERROR' if any(row['prediction']=='unknown' for row in rows) else 'COMPLETE',
                    predictions_sha256=sha((folder/'predictions.json').read_bytes()),image_ids=pinned,
                    case_count=len(rows),prediction_errors=sum(row['prediction']=='unknown' for row in rows))
    write_json(folder/'run_manifest.json', manifest)
    return folder


def collect_component_evidence(manifest_path, output_root, *, runner_factory=reference_runner, timeout=120):
    DockerRunner(timeout=timeout)
    loaded = load_corpus(manifest_path)
    folder = snapshot_corpus(loaded, output_root, 'reference-evidence')
    frozen = load_corpus(folder/'corpus.json')
    cache, runners, pinned, outcomes, decisions = {}, {}, {}, [], []
    for index, record in enumerate(frozen['records']):
        case = record['case']
        spec_key, key = case['spec_sha256'], (case['spec_sha256'],case['code_sha256'])
        reused = None
        contract={'expected_tests':None,'suite_sha256':None}
        try: contract=reference_contract(record['spec'])
        except ValueError: pass
        if key in cache:
            reused, raw = cache[key]
        else:
            try:
                if spec_key not in runners:
                    runners[spec_key] = runner_factory(record['spec'], folder/'harness'/record['spec']['spec_id'])
                    runners[spec_key].timeout = timeout
                runner = runners[spec_key]
                raw = runner.check_candidate(folder/case['code_path'])
                syntax = raw.get('status')=='UNLOADABLE_CODE' and raw.get('reason')=='invalid_syntax' and raw.get('executed') is False
                if not syntax and not _complete(raw,runner.candidate_tests,reference=True):
                    raise SandboxError('Bukti acuan ERROR/parsial/skipped atau counter/status bertentangan.')
                pinned[spec_key] = _bind(raw,case['code_sha256'],pinned.get(spec_key),runner)
            except (SandboxError,OSError,ValueError) as exc:
                raw = {'status':'ERROR','reason':'reference_evidence_error','detail':str(exc)}
            cache[key] = (case['case_id'],raw)
        evidence = {'evidence_type':'independent_reference','protocol_version':PROTOCOL,
                    **contract,
                    'code_sha256':case['code_sha256'],'spec_sha256':case['spec_sha256'],
                    'result':raw,'reused_from':reused}
        try: validate_reference_evidence(evidence,case,record['spec'])
        except ValueError as exc:
            evidence['result']=raw={'status':'ERROR','reason':'invalid_reference_evidence','detail':str(exc)}
        relative = 'cases/'+case['case_id']+'/independent-evidence.json'
        write_json(folder/relative,evidence)
        case['label']['evidence'].append({'kind':'independent_reference','path':relative,'sha256':sha((folder/relative).read_bytes())})
        outcomes.append({'case_id':case['case_id'],'status':raw['status'],'reused_from':reused,'path':relative})
        # Blind packet deliberately excludes proposed labels, prompts/feedback and Critic predictions.
        review_id = f'R{index+1:03}'
        packet = folder/'review'
        packet.mkdir(exist_ok=True)
        (packet/(review_id+'.php')).write_bytes(record['code'])
        (packet/(review_id+'.spec.json')).write_bytes(record['spec_bytes'])
        write_json(packet/(review_id+'.reference.json'),evidence)
        decisions.append({'review_id':review_id,'value':None,'violations':[], 'author':None,'reviewer':None,
                          'reviewed_at':None,'blinded_to_prediction':False,'notes':''})
    write_json(folder/'corpus.json', frozen['manifest'])
    write_json(folder/'review/decisions.json',{'instructions':'Independent human review only; no labels approved automatically.', 'cases':decisions})
    write_json(folder/'review-map.json',{'cases':[{ 'review_id':f'R{i+1:03}','case_id':row['case_id']} for i,row in enumerate(outcomes)]})
    write_json(folder/'evidence_manifest.json',{'protocol_version':PROTOCOL,'created_at':datetime.now(timezone.utc).isoformat(),
               'status':'ERROR' if any(row['status']=='ERROR' for row in outcomes) else 'COMPLETE',
               'source_manifest_sha256':loaded['manifest_sha256'],'corpus_sha256':sha((folder/'corpus.json').read_bytes()),
               'image_ids':pinned,'cases':outcomes,'labels_promoted':False})
    load_corpus(folder/'corpus.json')
    return folder
