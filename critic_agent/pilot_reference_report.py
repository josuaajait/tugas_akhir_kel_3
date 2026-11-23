"""Join development evaluator results to their source runs and calculate FR-18 metrics."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re


VALID = ('LOLOS', 'BELUM LOLOS')


def _rate(numerator, denominator):
    return {'numerator': numerator, 'denominator': denominator,
            'percent': numerator / denominator * 100 if denominator else None}


def _validated_pair(row, report, path):
    total = report.get('expected_tests')
    image, suite = report.get('image_id'), report.get('suite_sha256')
    if (type(total) is not int or total <= 0
            or not isinstance(image, str) or not re.fullmatch(r'sha256:[a-f0-9]{64}', image)
            or not isinstance(suite, str) or not re.fullmatch(r'[a-f0-9]{64}', suite)):
        raise ValueError(f'Identitas suite/image evaluator tidak valid: {path}')
    run = Path(row['run_directory'])
    pair = {'status': 'EVALUATED', 'report': str(path), 'image_id': image, 'suite_sha256': suite}
    for position in ('initial', 'final'):
        controller = run / f'{position}_controller.php'
        actual = hashlib.sha256(controller.read_bytes()).hexdigest() if controller.is_file() else None
        observation = report.get(position)
        if not isinstance(observation, dict):
            raise ValueError(f'Hasil evaluator {position} tidak tersedia: {path}')
        if actual != row[f'{position}_hash'] or observation.get('code_sha256') != actual:
            raise ValueError(f'Hash kandidat {position} tidak cocok: {path}')
        passed, status = observation.get('passed'), observation.get('status')
        if (type(passed) is not int or not 0 <= passed <= total
                or type(observation.get('total')) is not int or observation['total'] != total):
            raise ValueError(f'Jumlah test evaluator {position} tidak valid: {path}')
        if actual is None:
            allowed = ('UNAVAILABLE_CODE',) if passed == 0 else ()
        elif passed == total:
            allowed = ('PASSED_REFERENCE',)
        elif passed == 0:
            allowed = ('FAILED_REFERENCE', 'UNLOADABLE_CODE')
        else:
            allowed = ('FAILED_REFERENCE',)
        if status not in allowed:
            raise ValueError(f'Status evaluator {position} tidak sesuai hitungan atau kandidat: {path}')
        pair[position] = {'status': status, 'code_sha256': actual, **_rate(passed, total)}
    before, after = pair['initial'], pair['final']
    pair['uplift_pp'] = after['percent'] - before['percent']
    return pair


def attach_evaluations(rows, evaluations):
    """Keep ERROR attempts visible, and bind at most one successful pair to any run."""
    root = Path(evaluations).resolve()
    if not root.is_dir():
        raise ValueError(f'Direktori evaluasi tidak ditemukan: {root}')
    by_id = {}
    for row in rows:
        run_id = row.get('run_id')
        if run_id is not None:
            if run_id in by_id:
                raise ValueError(f'ID run duplikat dalam laporan pilot: {run_id}')
            by_id[run_id] = row
    reports = defaultdict(list)
    for path in sorted(root.rglob('evaluation_result.json')):
        report = json.loads(path.read_bytes())
        if not isinstance(report, dict) or not isinstance(report.get('source_run_id'), str):
            raise ValueError(f'Laporan evaluator tidak memiliki ID run sumber: {path}')
        run_id = report['source_run_id']
        if run_id in by_id:
            reports[run_id].append((report, path))
    for row in rows:
        result = {'status': 'MISSING' if row['status'] in VALID else 'NOT_ELIGIBLE'}
        errors = []
        for report, path in reports[row.get('run_id')]:
            if row['status'] not in VALID or report.get('source_status') != row['status']:
                raise ValueError(f'Status run sumber evaluator tidak cocok: {path}')
            if report.get('status') == 'EVALUATED':
                if result['status'] == 'EVALUATED':
                    raise ValueError(f'Ada lebih dari satu evaluasi berhasil untuk {row["run_id"]}.')
                result = _validated_pair(row, report, path)
            elif report.get('status') == 'ERROR':
                errors.append({'reason': report.get('reason') or 'unspecified', 'report': str(path)})
            else:
                raise ValueError(f'Status laporan evaluator tidak dikenal: {path}')
        if result['status'] == 'MISSING' and errors:
            result['status'] = 'ERROR'
        result['errors'] = errors
        row['evaluation'] = result


def reference_summary(rows, *, require_consistent=True):
    valid = [row for row in rows if row['status'] in VALID]
    pairs = [row['evaluation'] for row in rows if row['evaluation']['status'] == 'EVALUATED']
    identities = {(pair['image_id'], pair['suite_sha256'], pair['initial']['denominator']) for pair in pairs}
    if require_consistent and len(identities) > 1:
        raise ValueError('Image, fingerprint suite atau jumlah test evaluator berbeda dalam satu kelompok.')
    errors = Counter(error['reason'] for row in rows for error in row['evaluation']['errors'])
    failing = [pair for pair in pairs if pair['initial']['percent'] < 100]
    passing = [pair for pair in pairs if pair['initial']['percent'] == 100]
    summary = {
        'n_valid': len(valid),
        'n_pair': len(pairs),
        'loop_errors': sum(row['status'] == 'ERROR' for row in rows),
        'stop_reasons': dict(Counter(row.get('stop_reason') or 'unspecified' for row in rows
                                     if row['status'] in (*VALID, 'ERROR'))),
        'evaluator_errors': sum(errors.values()),
        'evaluator_error_reasons': dict(errors),
        'valid_without_evaluation': sum(row['evaluation']['status'] == 'MISSING' for row in rows),
        'valid_with_only_evaluator_error': sum(row['evaluation']['status'] == 'ERROR' for row in rows),
        'mean_uplift_pp': sum(pair['uplift_pp'] for pair in pairs) / len(pairs) if pairs else None,
        'mean_revisions': sum(row['revision_count'] for row in valid) / len(valid) if valid else None,
        'repair': _rate(sum(pair['final']['percent'] == 100 for pair in failing), len(failing)),
        'regression': _rate(sum(pair['final']['percent'] < 100 for pair in passing), len(passing)),
    }
    for position in ('initial', 'final'):
        summary[f'{position}_pass_rate'] = _rate(
            sum(pair[position]['numerator'] for pair in pairs),
            sum(pair[position]['denominator'] for pair in pairs),
        ) if len(identities) <= 1 else None
    return summary
