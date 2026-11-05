"""Bounded development corpus and independent label metadata; no predictions."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from uuid import uuid4

from .spec import load_spec

ROOT = Path(__file__).resolve().parents[1]
ORIGINS = ('synthetic', 'qwen_formative', 'qwen_held_out')
PROTOCOL = '1.0'
SOURCE_RUNS = (
    '20261104T031502Z_loop_713c3f8803f441929ae6ed8f38077232',
    '20261104T044458Z_loop_52c1faef1c1644f3ac228b14eebdebcf',
    '20261104T044936Z_loop_4c8045891ecc4a74a31e0117ed15932a',
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    path = Path(path)
    if path.stat().st_size > 8_000_000:
        raise ValueError('JSON melebihi batas8MB: '+str(path))
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Diperlukan object JSON: '+str(path))
    return data


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode())


def utc_timestamp(value):
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError('Timestamp harus ISO8601 dengan timezone.') from exc
    if parsed.tzinfo is None:
        raise ValueError('Timestamp memerlukan timezone.')
    return parsed


def asset(root, relative, expected_hash, *, limit=8_000_000):
    if (not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative
            or Path(relative).is_absolute() or '..' in Path(relative).parts):
        raise ValueError('Path korpus harus relatif dan tetap di dalam paket.')
    root = Path(root).resolve()
    path = (root/relative).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size > limit:
        raise ValueError('File korpus keluar paket, hilang, atau terlalu besar.')
    data = path.read_bytes()
    if not isinstance(expected_hash, str) or not re.fullmatch('[a-f0-9]{64}', expected_hash) or sha(data) != expected_hash:
        raise ValueError('Hash file korpus tidak cocok: '+relative)
    return data


def reference_contract(spec):
    if spec['resource']=='products':
        from .sandbox import validate_products_contract
        from .reference import REFERENCE_TESTS, reference_suite_hash
        validate_products_contract(spec)
        return {'expected_tests':REFERENCE_TESTS,'suite_sha256':reference_suite_hash()}
    from .resource_reference import resource_reference_manifest
    meta=resource_reference_manifest(spec)
    return {key:meta[key] for key in ('expected_tests','suite_sha256')}


def validate_reference_evidence(data, case, spec):
    if (not isinstance(data,dict) or data.get('evidence_type')!='independent_reference'
            or data.get('code_sha256')!=case['code_sha256'] or data.get('spec_sha256')!=case['spec_sha256']):
        raise ValueError('Bukti independen bukan untuk kode/spec ini.')
    raw=data.get('result',{})
    if not isinstance(raw,dict): raise ValueError('Bukti memerlukan result object.')
    if raw.get('status')=='ERROR': return False
    expected=reference_contract(spec)
    if any(data.get(key)!=value for key,value in expected.items()):
        raise ValueError('Bukti tidak cocok dengan suite/jumlah test acuan yang didukung.')
    if (raw.get('candidate_sha256')!=case['code_sha256'] or not isinstance(raw.get('image_id'),str)
            or not re.fullmatch('sha256:[a-f0-9]{64}',raw['image_id'])
            or type(raw.get('cleanup_exit_code')) is not int or raw['cleanup_exit_code']!=0):
        raise ValueError('Bukti kandidat/image/cleanup tidak lengkap atau tidak cocok.')
    if raw.get('status')=='UNLOADABLE_CODE':
        if (raw.get('reason')!='invalid_syntax' or raw.get('executed') is not False or raw.get('exit_code')!=65
                or 'Errors parsing /input/controller.php' not in raw.get('diagnostic','')):
            raise ValueError('Bukti kegagalan sintaks tidak lengkap.')
        return True
    summary=raw.get('summary',{})
    if not isinstance(summary,dict): raise ValueError('Counter acuan tidak valid.')
    count=expected['expected_tests']
    numbers=[summary.get(key) for key in ('passed','failure','error','skipped')]
    if (summary.get('total')!=count or any(type(n) is not int or n<0 for n in numbers)
            or sum(numbers)!=count or summary['skipped']!=0):
        raise ValueError('Bukti acuan parsial atau counter bertentangan.')
    status='PASSED_REFERENCE' if summary['passed']==count else 'FAILED_REFERENCE'
    cases=summary.get('cases')
    if raw.get('status')!=status or not isinstance(cases,list) or len(cases)!=count:
        raise ValueError('Status/daftar testcase acuan tidak lengkap.')
    identities=set();outcomes={'passed':0,'failure':0,'error':0,'skipped':0}
    for row in cases:
        if not isinstance(row,dict) or not row.get('name') or row.get('outcome') not in outcomes:
            raise ValueError('Identitas/outcome testcase acuan invalid.')
        identity=(row.get('class',''),row['name'])
        if identity in identities: raise ValueError('Testcase acuan duplikat.')
        identities.add(identity);outcomes[row['outcome']]+=1
    if any(outcomes[key]!=summary[key] for key in outcomes):
        raise ValueError('Outcome testcase tidak cocok dengan counter acuan.')
    return True


def load_corpus(manifest_path):
    path = Path(manifest_path).resolve(strict=True)
    if path.stat().st_size > 8_000_000:
        raise ValueError('Manifest korpus melebihi batas 8MB.')
    manifest_bytes = path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict):
        raise ValueError('Manifest korpus harus object JSON.')
    if manifest.get('schema_version') != PROTOCOL or manifest.get('stage') != 'development':
        raise ValueError('Protokol komponen1.0 saat ini hanya untuk development.')
    cases = manifest.get('cases')
    if not isinstance(cases, list) or not 1 <= len(cases) <= 200:
        raise ValueError('Korpus harus berisi1–200 contoh kode.')
    identifiers, records = set(), []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError('Setiap kasus korpus harus object JSON.')
        case_id = case.get('case_id')
        if not isinstance(case_id, str) or not re.fullmatch('[a-z][a-z0-9_]{0,63}', case_id) or case_id in identifiers:
            raise ValueError('case_id kosong, tidak aman atau duplikat.')
        identifiers.add(case_id)
        if case.get('corpus') not in ORIGINS or type(case.get('used_for_development')) is not bool:
            raise ValueError('Asal korpus/pemakaian pengembangan harus eksplisit.')
        if case['corpus'] == 'qwen_held_out' and case['used_for_development']:
            raise ValueError('Kode yang dipakai pengembangan tidak boleh disebut held-out.')
        code = asset(path.parent, case.get('code_path'), case.get('code_sha256'), limit=1_000_000)
        code.decode('utf-8')
        spec_bytes = asset(path.parent, case.get('spec_path'), case.get('spec_sha256'), limit=1_000_000)
        spec = load_spec(path.parent/case['spec_path'])
        label = case.get('label', {})
        if not isinstance(label, dict):
            raise ValueError('Label harus object JSON.')
        if label.get('value') not in ('correct', 'problematic', 'uncertain'):
            raise ValueError('Label harus correct/problematic/uncertain.')
        violations = label.get('violations')
        if not isinstance(violations, list) or (label['value'] == 'problematic' and not violations):
            raise ValueError('Label problematic memerlukan daftar pelanggaran.')
        if label['value'] == 'correct' and violations:
            raise ValueError('Label correct tidak boleh memiliki pelanggaran.')
        for violation in violations:
            if (not isinstance(violation, dict) or violation.get('coverage') not in ('internal_covered', 'reference_only')
                    or not isinstance(violation.get('detail'), str) or not violation['detail'].strip()):
                raise ValueError('Setiap pelanggaran memerlukan coverage dan alasan.')
        evidence = label.get('evidence')
        if not isinstance(evidence, list) or not evidence:
            raise ValueError('Label memerlukan catatan bukti, bukan prediksi Critic.')
        independent = False
        for item in evidence:
            if not isinstance(item, dict):
                raise ValueError('Bukti label harus object JSON.')
            if item.get('kind') == 'independent_reference':
                raw = json.loads(asset(path.parent, item.get('path'), item.get('sha256')))
                valid=validate_reference_evidence(raw,case,spec)
                independent=independent or valid
            elif item.get('kind') != 'code_inspection' or not item.get('detail'):
                raise ValueError('Jenis bukti label tidak didukung.')
        review = label.get('review', {})
        if not isinstance(review, dict):
            raise ValueError('Review harus object JSON.')
        if review.get('status') not in ('draft', 'reviewed', 'disputed'):
            raise ValueError('Status review label harus draft/reviewed/disputed.')
        if review['status'] == 'reviewed':
            author, reviewer = review.get('author'), review.get('reviewer')
            if (not isinstance(author, str) or not author.strip() or not isinstance(reviewer, str) or not reviewer.strip()
                    or author.strip().casefold() == reviewer.strip().casefold()
                    or review.get('blinded_to_prediction') is not True or not independent):
                raise ValueError('Review memerlukan dua nama berbeda, blind attestation, dan bukti acuan yang cocok.')
            utc_timestamp(review.get('reviewed_at'))
        origin = case.get('origin', {})
        if not isinstance(origin, dict) or not isinstance(origin.get('artifacts', []), list):
            raise ValueError('Origin harus object dengan daftar artifacts.')
        artifacts = origin.get('artifacts', [])
        for item in artifacts:
            if not isinstance(item, dict):
                raise ValueError('Artifact asal harus object JSON.')
            asset(path.parent, item.get('path'), item.get('sha256'))
        records.append({'case': case, 'spec': spec, 'code': code, 'spec_bytes': spec_bytes})
    return {'manifest': manifest, 'manifest_bytes': manifest_bytes, 'manifest_path': path, 'manifest_sha256': sha(manifest_bytes),
            'root': path.parent, 'records': records}


def snapshot_corpus(loaded, output_root, prefix):
    folder = Path(output_root)/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+prefix+'_'+uuid4().hex)
    folder.mkdir(parents=True, exist_ok=False)
    manifest = copy.deepcopy(loaded['manifest'])
    (folder/'source_manifest.json').write_bytes(loaded['manifest_bytes'])
    for record, case in zip(loaded['records'], manifest['cases']):
        base = 'cases/'+case['case_id']
        destination = folder/base
        destination.mkdir(parents=True)
        (destination/'controller.php').write_bytes(record['code'])
        (destination/'spec.json').write_bytes(record['spec_bytes'])
        case.update(code_path=base+'/controller.php', spec_path=base+'/spec.json')
        for index, item in enumerate(case['label']['evidence']):
            if item['kind'] == 'independent_reference':
                data = asset(loaded['root'], item['path'], item['sha256'])
                relative = base+f'/label-evidence-{index}.json'
                (folder/relative).write_bytes(data)
                item['path'] = relative
        for index, item in enumerate(case.get('origin', {}).get('artifacts', [])):
            data = asset(loaded['root'], item['path'], item['sha256'])
            relative = base+'/artifact-'+str(index)+Path(item['path']).suffix
            (folder/relative).write_bytes(data)
            item['path'] = relative
    write_json(folder/'corpus.json', manifest)
    return folder


def _draft(value, violations, note):
    return {'value': value, 'violations': violations,
            'evidence': [{'kind': 'code_inspection', 'detail': note}],
            'review': {'status': 'draft', 'author': None, 'reviewer': None,
                       'reviewed_at': None, 'blinded_to_prediction': False}}


def prepare_development_corpus(output_root, *, synthetic_only=False, runs_root=ROOT/'runs'):
    baseline = (ROOT/'corpora/templates/BookController.php').read_text(encoding='utf-8')
    title_rule = "['required', 'string', 'max:80']"
    pages_rule = "['required', 'integer', 'min:1', 'max:5000']"
    def replace_once(text, old, new):
        if text.count(old) != 1: raise ValueError('Anchor mutasi berubah; periksa template.')
        return text.replace(old, new)
    split = baseline.index('    public function update(')
    update_missing = baseline[:split]+replace_once(baseline[split:], title_rule, "['string', 'max:80']")
    show_start, show_end = baseline.index('    public function show('), split
    show_missing = baseline[:show_start]+replace_once(baseline[show_start:show_end], 'Book::findOrFail($id)', 'Book::find($id)')+baseline[show_end:]
    variants = [
        ('syn_array_valid', baseline, 'correct', None, 'Array-rule implementation requires code and independent execution review.'),
        ('syn_string_valid', baseline.replace(title_rule, "'required|string|max:80'").replace(pages_rule, "'required|integer|min:1|max:5000'"), 'correct', None, 'Equivalent string-rule implementation, not a Qwen output.'),
        ('syn_syntax', baseline.rstrip()[:-1], 'problematic', 'internal_covered', 'Removed final class brace; PHP cannot parse the controller.'),
        ('syn_missing_method', replace_once(baseline, 'public function show($id)', 'public function lookup($id)'), 'problematic', 'internal_covered', 'Required public show method is absent.'),
        ('syn_store_status', replace_once(baseline, "return response()->json(['data' => $book], 201);", "return response()->json(['data' => $book], 200);"), 'problematic', 'internal_covered', 'Store success returns200 instead of201.'),
        ('syn_update_required', update_missing, 'problematic', 'internal_covered', 'PUT accepts missing title because required is omitted.'),
        ('syn_missing_id', show_missing, 'problematic', 'internal_covered', 'Show returns data:null/200 rather than404 for unknown ID.'),
        ('syn_wrong_delete', replace_once(baseline, 'Book::findOrFail($id)->delete();', 'Book::query()->delete();'), 'problematic', 'internal_covered', 'Destroy deletes all records rather than only requested ID.'),
        ('syn_reference_max', baseline.replace("'string', 'max:80'", "'string'"), 'problematic', 'reference_only', 'Both write methods omit title max80; internal cases do not cover that boundary.'),
        ('syn_reference_min', baseline.replace("'integer', 'min:1', 'max:5000'", "'integer', 'max:5000'"), 'problematic', 'reference_only', 'Both write methods omit pages min1; internal cases do not cover that boundary.'),
    ]
    entries = []
    book_spec = (ROOT/'examples/books.json').read_bytes()
    for case_id, code, value, coverage, note in variants:
        entries.append((case_id, 'synthetic', code.encode(), book_spec,
                        _draft(value, [] if coverage is None else [{'category':case_id, 'coverage':coverage, 'detail':note}], note),
                        {'kind':'controlled_mutation', 'template_sha256':sha(baseline.encode()), 'artifacts':[]}, {}))
    if not synthetic_only:
        for run_id in SOURCE_RUNS:
            source = Path(runs_root)/run_id
            manifest, history = read_json(source/'run_manifest.json'), read_json(source/'history.json')
            spec_bytes = (source/'spec.json').read_bytes()
            if manifest.get('spec_sha256') != sha(spec_bytes): raise ValueError('Spesifikasi run sumber berubah.')
            for attempt in history['attempts']:
                number = attempt['iteration']
                attempt_root = source/'attempts'/str(number)
                code = (attempt_root/'controller.php').read_bytes()
                if sha(code) != attempt.get('code_sha256'): raise ValueError('Kode Qwen sumber berubah.')
                if attempt.get('prompt_sha256') is not None:
                    if not (attempt_root/'prompt.txt').is_file() or sha((attempt_root/'prompt.txt').read_bytes())!=attempt['prompt_sha256']:
                        raise ValueError('Prompt Qwen sumber berubah atau hilang.')
                resource = json.loads(spec_bytes)['resource']
                case_id = 'qwen_'+resource+'_'+str(number)
                notes = []
                if resource == 'products' and number == 0:
                    notes = [('destroy_response', 'ResponseFactory::setContent is absent; independent evaluation observed500 instead of204.')]
                elif resource == 'inventory_items':
                    notes = [('update_required', 'Update omits required for all4 fields; independently observed missing-field PUT200 instead of422.')]
                    if number == 0: notes.append(('destroy_response', 'ResponseFactory::empty is absent; independently observed500 instead of204.'))
                violations = [{'category':category, 'coverage':'internal_covered', 'detail':note} for category,note in notes]
                note = 'Draft based on source inspection and earlier independent development evaluation; obtain fresh independent evidence and human review.'
                label = _draft('problematic' if notes else 'correct', violations, note)
                artifacts = {name:(attempt_root/name).read_bytes() for name in ('response.json','response.txt','source_response.json','prompt.txt') if (attempt_root/name).is_file()}
                artifacts['source_run_manifest.json']=(source/'run_manifest.json').read_bytes()
                artifacts['source_history.json']=(source/'history.json').read_bytes()
                imported_manifest=source/'initial_source_manifest.json'
                if number==0 and imported_manifest.is_file():
                    imported=read_json(imported_manifest)
                    initial_source=Path(manifest['initial_source']).resolve(strict=True)
                    if not initial_source.is_relative_to(Path(runs_root).resolve()):
                        raise ValueError('Arsip generasi awal harus berada di runs-root yang dipilih.')
                    original_spec=(initial_source/'spec.json').read_bytes()
                    if (imported.get('code_sha256')!=sha(code) or imported.get('spec_sha256')!=sha(original_spec)
                            or load_spec(initial_source/'spec.json')!=json.loads(spec_bytes)):
                        raise ValueError('Manifest generasi awal tidak cocok dengan kode/spec sumbernya.')
                    prompt=(initial_source/'prompt.txt').read_bytes()
                    if sha(prompt)!=imported.get('prompt_sha256'):
                        raise ValueError('Prompt generasi awal berubah.')
                    artifacts['initial_prompt.txt']=prompt
                    artifacts['initial_spec.json']=original_spec
                    artifacts['initial_source_manifest.json']=imported_manifest.read_bytes()
                # Bind archived raw output to the unchanged extracted candidate.
                if 'response.json' not in artifacts or 'response.txt' not in artifacts:
                    raise ValueError('Arsip Qwen tidak memiliki raw response lengkap.')
                from .generation import extract_php
                response=json.loads(artifacts['response.json'])
                if response.get('response','').encode()!=artifacts['response.txt'] or extract_php(response['response']).encode()!=code:
                    raise ValueError('Raw response Qwen tidak cocok dengan kandidat.')
                if 'source_response.json' in artifacts:
                    original=json.loads(artifacts['source_response.json'])
                    if extract_php(original['response']).encode()!=code:
                        raise ValueError('Raw response generasi awal tidak cocok dengan kandidat.')
                origin = {'kind':'archived_qwen_attempt', 'source_run_id':run_id, 'source_attempt':number,
                          'model':manifest['model'], 'options':manifest['options'], 'prototype_version':manifest['prototype_version'],
                          'artifacts':[]}
                entries.append((case_id,'qwen_formative',code,spec_bytes,label,origin,artifacts))
    folder = Path(output_root)/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_corpus_'+uuid4().hex)
    cases = []
    for case_id, corpus, code, spec_bytes, label, origin, artifacts in entries:
        base = 'cases/'+case_id
        destination = folder/base
        destination.mkdir(parents=True)
        (destination/'controller.php').write_bytes(code)
        (destination/'spec.json').write_bytes(spec_bytes)
        for name, data in artifacts.items():
            (destination/name).write_bytes(data)
            origin['artifacts'].append({'path':base+'/'+name,'sha256':sha(data)})
        cases.append({'case_id':case_id,'corpus':corpus,'used_for_development':True,'origin':origin,
                      'code_path':base+'/controller.php','code_sha256':sha(code),
                      'spec_path':base+'/spec.json','spec_sha256':sha(spec_bytes),'label':label})
    write_json(folder/'corpus.json', {'schema_version':PROTOCOL,'corpus_id':folder.name,'stage':'development',
        'selection':{'description':'10 planned controlled examples plus ALL attempts from3 explicitly selected formative development loops, including duplicates; not a random or held-out sample.',
                     'source_runs':[] if synthetic_only else list(SOURCE_RUNS),'held_out_available':False},'cases':cases})
    load_corpus(folder/'corpus.json')
    return folder
