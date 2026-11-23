"""Read-only progress and descriptive metrics for pilot manifests."""
from collections import Counter, defaultdict
import json
from pathlib import Path

from .pilot_metadata import read_pilot_metadata
from .pilot_reference_report import VALID, attach_evaluations, reference_summary
from .pilot_runner import validate_pilot_manifest


STATUSES = (*VALID, 'ERROR', 'INCOMPLETE', 'PLANNED')


def _token_counts(run, attempt_count):
    counts = []
    for iteration in range(attempt_count):
        path = run / 'attempts' / str(iteration) / 'response.json'
        if path.is_file():
            response = json.loads(path.read_bytes())
            if isinstance(response, dict):
                tokens = response.get('prompt_eval_count'), response.get('eval_count')
                if all(type(value) is int and value >= 0 for value in tokens):
                    counts.append(tokens)
    return {'prompt_tokens_observed': sum(prompt for prompt, _ in counts),
            'completion_tokens_observed': sum(output for _, output in counts),
            'responses_with_counts': len(counts)}


def _job_row(manifest, job):
    folder = manifest.parent / 'executions' / job['job_id']
    result_path = folder / 'pilot_result.json'
    row = {key: job[key] for key in ('job_id', 'spec', 'spec_sha256', 'model', 'seed',
                                    'temperature', 'max_revisions')}
    row['manifest'] = str(manifest)
    if not result_path.is_file():
        return dict(row, status='INCOMPLETE' if folder.exists() else 'PLANNED')
    result = json.loads(result_path.read_bytes())
    for key in ('job_id', 'config_sha256', 'spec_sha256'):
        if result.get(key) != job[key]:
            raise ValueError(f'Arsip {result_path} tidak cocok dengan manifest ({key}).')
    status = result.get('status')
    if status not in (*VALID, 'ERROR'):
        raise ValueError(f'Status hasil pilot tidak dikenal di {result_path}.')
    row.update(status=status, stop_reason=result.get('stop_reason'), error=result.get('error'),
               kind=result.get('kind'), result_path=str(result_path))
    if status == 'ERROR' and not result.get('run_directory'):
        return row
    metadata = read_pilot_metadata(folder)
    for key in ('model', 'seed', 'temperature', 'max_revisions'):
        if metadata['configuration'][key] != job[key]:
            raise ValueError(f'Konfigurasi loop tidak cocok dengan manifest di {result_path} ({key}).')
    outcome, execution = metadata['outcome'], metadata['execution']
    run = Path(metadata['source_files']['history']).parent
    first = metadata['tests']['initial']
    row.update(run_directory=str(run), run_id=metadata['run_id'], revision_count=outcome['revision_count'],
               initial_hash=metadata['code']['initial_sha256'], final_hash=metadata['code']['final_sha256'],
               initial_test=first,
               initial_failed=(first['status'] != 'PASSED_INTERNAL') if status in VALID else None,
               image_id=metadata['environment']['docker_image_id'],
               attempt_seconds=execution['total_attempt_seconds'],
               model_calls_with_history=execution['model_call_count'],
               transport_attempts_observed=execution['transport_attempts_observed'],
               transport_retries_observed=execution['transport_retries_observed'],
               model_calls_with_transport_trace=execution['model_calls_with_transport_trace'],
               **_token_counts(run, outcome['attempt_count']))
    return row


def _ratio(numerator, denominator):
    return {'numerator': numerator, 'denominator': denominator}


def _summary(rows):
    counts = Counter(row['status'] for row in rows)
    valid = [row for row in rows if row['status'] in VALID]
    revised = [row for row in valid if row['revision_count'] > 0]
    identical = sum(row['stop_reason'] == 'identical_code' for row in valid)
    hashes = [row['initial_hash'] for row in valid if row['initial_hash']]
    durations = [row['attempt_seconds'] for row in rows if row.get('attempt_seconds') is not None]
    token_fields = ('prompt_tokens_observed', 'completion_tokens_observed',
                    'responses_with_counts', 'model_calls_with_history')
    traces = sum(row.get('model_calls_with_transport_trace', 0) for row in rows)
    return {
        'counts': {status: counts[status] for status in STATUSES},
        'stop_reasons': dict(Counter(row['stop_reason'] or 'unspecified' for row in rows
                                     if row['status'] in (*VALID, 'ERROR'))),
        'initial_failed_among_valid': _ratio(sum(row['initial_failed'] for row in valid), len(valid)),
        'initial_extracted_among_valid': _ratio(len(hashes), len(valid)),
        'unique_initial_hashes': len(set(hashes)),
        'duplicate_initial_hashes': len(hashes) - len(set(hashes)),
        'identical_among_valid': _ratio(identical, len(valid)),
        'identical_among_revised': _ratio(identical, len(revised)),
        'mean_revisions': sum(row['revision_count'] for row in valid) / len(valid) if valid else None,
        'attempt_duration': {'seconds_observed': round(sum(durations), 6), 'jobs_observed': len(durations)},
        'token_usage': {field: sum(row.get(field, 0) for row in rows) for field in token_fields},
        'transport': {
            'model_calls_with_trace': traces,
            'model_calls_with_history': sum(row.get('model_calls_with_history', 0) for row in rows),
            'http_attempts_observed': sum(row.get('transport_attempts_observed') or 0 for row in rows) if traces else None,
            'http_retries_observed': sum(row.get('transport_retries_observed') or 0 for row in rows) if traces else None,
        },
        'image_ids': sorted({row['image_id'] for row in rows if row.get('image_id')}),
    }


def pilot_report(manifests, *, evaluations=None):
    paths = [Path(path).resolve() for path in manifests]
    if not paths or len(paths) != len(set(paths)) or len(paths) != len({path.parent for path in paths}):
        raise ValueError('Gunakan manifest yang berbeda dan satu direktori eksekusi per manifest.')
    rows = [_job_row(path, job) for path in paths for job in validate_pilot_manifest(path)['jobs']]
    if evaluations is not None:
        attach_evaluations(rows, evaluations)
    groups = defaultdict(list)
    for row in rows:
        key = tuple(row[field] for field in ('spec_sha256', 'model', 'temperature', 'max_revisions'))
        groups[key].append(row)
    result = {'schema_version': '1.0', 'stage': 'development', 'planned_jobs': len(rows),
              'counts': {status: sum(row['status'] == status for row in rows) for status in STATUSES},
              'groups': [], 'jobs': rows}
    if evaluations is not None:
        result['reference'] = reference_summary(rows, require_consistent=False)
    for key, members in groups.items():
        group = dict(spec_sha256=key[0], model=key[1], temperature=key[2],
                     max_revisions=key[3], spec=members[0]['spec'], **_summary(members))
        if evaluations is not None:
            group['reference'] = reference_summary(members)
        result['groups'].append(group)
    return result
