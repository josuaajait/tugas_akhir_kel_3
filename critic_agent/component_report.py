"""Descriptive code-level confusion matrices, never pooled across corpora."""
from collections import Counter, defaultdict
import copy
from pathlib import Path

from .component_corpus import ORIGINS, PROTOCOL, load_corpus, read_json, write_json, sha, utc_timestamp


def _ratio(numerator,denominator):
    return {'numerator':numerator,'denominator':denominator,'percent':numerator/denominator*100 if denominator else None}


def _scope(case):
    coverage = {item['coverage'] for item in case['label']['violations']}
    return next(iter(coverage)) if len(coverage)==1 else ('mixed' if coverage else 'correct')


def summarize_components(rows, *, provisional=False, started_at):
    started = utc_timestamp(started_at)
    report = {'protocol_version':PROTOCOL,'stage':'development',
              'label_mode':'provisional_unreviewed' if provisional else 'reviewed_only',
              'duplicate_policy':'one eligible code/spec hash per corpus; conflicting labels excluded',
              'groups':{}}
    for corpus in ORIGINS:
        selected = [row for row in rows if row['corpus']==corpus]
        excluded, matrix, subsets = Counter(), Counter({'TP':0,'FP':0,'TN':0,'FN':0}), {}
        candidates = defaultdict(list)
        for row in selected:
            label = row['label']; review = label['review']
            if row.get('prediction') not in ('correct','problematic') or row.get('status')!='PREDICTED':
                excluded['prediction_error']+=1
            elif label['value']=='uncertain' or review['status']=='disputed':
                excluded['uncertain_label']+=1
            elif not provisional and review['status']!='reviewed':
                excluded['unreviewed_label']+=1
            elif review['status']=='reviewed' and utc_timestamp(review['reviewed_at'])>started:
                excluded['review_after_prediction']+=1
            else:
                candidates[(row['spec_sha256'],row['code_sha256'])].append(row)
        included=[]
        for key,duplicates in candidates.items():
            if len({row['label']['value'] for row in duplicates})!=1:
                excluded['conflicting_labels']+=len(duplicates)
                continue
            excluded['duplicate']+=len(duplicates)-1
            row=duplicates[0]
            positive=row['prediction']=='problematic'
            truth=row['label']['value']=='problematic'
            outcome=('TP' if truth else 'FP') if positive else ('FN' if truth else 'TN')
            matrix[outcome]+=1
            scope=_scope(row)
            if scope not in subsets: subsets[scope]={'TP':0,'FP':0,'TN':0,'FN':0}
            subsets[scope][outcome]+=1
            included.append({'case_id':row['case_id'],'outcome':outcome,'coverage_group':scope})
        report['groups'][corpus]={'total':len(selected),'eligible':sum(matrix.values()),'excluded':dict(excluded),
            'draft_labels':sum(row['label']['review']['status']=='draft' for row in selected),
            'matrix':dict(matrix),'precision':_ratio(matrix['TP'],matrix['TP']+matrix['FP']),
            'recall':_ratio(matrix['TP'],matrix['TP']+matrix['FN']),
            'fpr':_ratio(matrix['FP'],matrix['FP']+matrix['TN']), 'by_coverage':subsets,'included':included}
    return report


def component_report(run_directory, *, provisional=False):
    folder=Path(run_directory)
    manifest=read_json(folder/'run_manifest.json')
    if manifest.get('status') not in ('COMPLETE','ERROR'):
        raise ValueError('Run prediksi belum selesai.')
    for name,key in [('corpus.json','corpus_sha256'),('predictions.json','predictions_sha256'),
                     ('source_manifest.json','source_manifest_sha256')]:
        if sha((folder/name).read_bytes())!=manifest.get(key):
            raise ValueError('Snapshot run berubah; laporan ditolak.')
    loaded=load_corpus(folder/'corpus.json')
    predictions=read_json(folder/'predictions.json')['cases']
    if len(predictions)!=len(loaded['records']):
        raise ValueError('Prediksi tidak lengkap untuk seluruh korpus.')
    rows=[]
    for record,prediction in zip(loaded['records'],predictions):
        case=record['case']
        if any(case[key]!=prediction.get(key) for key in ('case_id','corpus','code_sha256','spec_sha256')):
            raise ValueError('Prediksi berbeda dengan identitas snapshot kode/spec.')
        row=copy.deepcopy(case)
        row.update({key:prediction.get(key) for key in ('prediction','status','findings')})
        rows.append(row)
    report=summarize_components(rows,provisional=provisional,started_at=manifest['created_at'])
    report.update(engine_sha256=manifest['engine_sha256'],backend=manifest['backend'],
                  source_run_status=manifest['status'],corpus_sha256=manifest['corpus_sha256'])
    write_json(folder/('report-provisional.json' if provisional else 'report-reviewed.json'),report)
    return report
