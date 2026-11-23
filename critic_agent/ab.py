"""Development A/B pairs with one shared initial candidate."""
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess
import time
from uuid import uuid4

from .generation import generate
from .orchestrator import _initial_archive, _write_json, run_products, run_resource
from .reference import _evaluate_pair, _json, evaluate_products
from .resource_reference import resource_reference_manifest
from .sandbox import SandboxError, validate_products_contract
from .static import analyze


def _cost(requests, response_paths, seconds):
    tokens = []
    for path in response_paths:
        if path.is_file():
            response = json.loads(path.read_bytes())
            if not isinstance(response, dict):
                continue
            counts = response.get('prompt_eval_count'), response.get('eval_count')
            if all(type(count) is int and count >= 0 for count in counts):
                tokens.append(counts)
    traces = [request['transport_attempts'] for request in requests if request and request.get('transport_attempts')]
    return {'model_calls': len(requests), 'model_calls_with_transport_trace': len(traces),
            'http_attempts_observed': sum(map(len, traces)) if traces else None,
            'http_retries_observed': sum(len(trace)-1 for trace in traces) if traces else None,
            'responses_with_token_counts': len(tokens),
            'prompt_tokens_observed': sum(count[0] for count in tokens) if tokens else None,
            'output_tokens_observed': sum(count[1] for count in tokens) if tokens else None,
            'attempt_seconds': seconds}


def run_ab(spec, output_root, client, runner, reference, *, kind, order_seed, revision_seeds,
           initial_run=None, repetition=1, static_analyzer=analyze):
    seeds = list(revision_seeds)
    if len(seeds) > 3 or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError('Jadwal revisi memerlukan 0–3 seed bilangan bulat nonnegatif.')
    if type(repetition) is not int or repetition < 1:
        raise ValueError('Indeks pengulangan harus positif.')
    if kind == 'products':
        validate_products_contract(spec)
        loop, evaluate = run_products, evaluate_products
    elif kind == 'resource':
        meta = resource_reference_manifest(spec)
        if (reference.spec != spec or reference.candidate_tests != meta['expected_tests']
                or reference.expected_suite_sha256 != meta['suite_sha256']):
            raise ValueError('Evaluator resource tidak sesuai kontrak pasangan.')
        loop = run_resource

        def evaluate(source, output, evaluator, *, shared_initial):
            def validate(current):
                if current != spec:
                    raise ValueError('Spesifikasi arsip cabang berubah.')
            return _evaluate_pair(source, output, evaluator, expected_tests=meta['expected_tests'],
                                  suite_sha256=meta['suite_sha256'], validate_contract=validate,
                                  shared_initial=shared_initial)
    else:
        raise ValueError('Runner A/B tidak dikenal.')
    pair_id = 'ab_'+uuid4().hex
    folder = (Path(output_root)/pair_id).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    order = ['A', 'B']
    random.Random(order_seed).shuffle(order)
    report = {'pair_id': pair_id, 'stage': 'development', 'status': 'RUNNING', 'spec_id': spec['spec_id'],
              'kind': kind, 'repetition': repetition, 'order': order, 'order_seed': order_seed,
              'model': client.model, 'options': dict(client.options), 'revision_seeds': seeds,
              'max_revisions': len(seeds), 'branches': {}, 'delta_final_pp': None, 'n_ab': 0}
    _write_json(folder/'spec.json', spec)
    report['spec_sha256'] = hashlib.sha256((folder/'spec.json').read_bytes()).hexdigest()
    _write_json(folder/'pair.json', report)
    errors = (OSError, ValueError, SandboxError, subprocess.TimeoutExpired)
    try:
        ready = runner.check_reference()
        report['internal_readiness'] = ready
        if ready['status'] != 'READY' or not re.fullmatch(r'sha256:[a-f0-9]{64}', ready.get('image_id', '')):
            raise SandboxError('Harness internal belum READY.')
        pinned = runner.image = ready['image_id']
        report['internal_image_id'] = pinned
        started = time.monotonic()
        source = Path(initial_run).resolve() if initial_run else generate(spec, folder/'initial', client)
        initial = _json(source/'run_manifest.json')
        report['initial_generation'] = str(source)
        report['initial_cost'] = (_cost([initial.get('model_request')], [source/'response.json'],
                                         round(time.monotonic()-started, 6))
                                  if initial_run is None else None)
        if initial['status'] == 'ERROR':
            raise SandboxError('Generasi awal gagal. Baca arsip generasi awal.')
        _, _, identical_input = _initial_archive(source, spec, client, allow_format_failure=True)
        report['initial_input_sha256'] = hashlib.sha256(identical_input.encode('utf-8')).hexdigest()
        report['initial_code_sha256'] = initial.get('code_sha256')
        for condition in order:
            branch = report['branches'][condition] = {'status': 'ERROR'}
            runner.image = pinned
            try:
                run = loop(spec, folder/condition, client, runner, initial_run=source,
                           max_revisions=len(seeds), static_analyzer=static_analyzer,
                           ab={'pair_id': pair_id, 'condition': condition, 'revision_seeds': seeds,
                               'internal_image_id': pinned})
                history = _json(run/'history.json')
                attempts = history['attempts']
                if attempts[0].get('code_sha256') != report['initial_code_sha256']:
                    raise ValueError('Hash awal cabang berbeda dari kandidat bersama.')
                calls = [entry for entry in attempts if entry.get('model_called')]
                branch.update(run_directory=str(run), status=history['status'], reason=history['stop_reason'],
                              revision_count=history['revision_count'],
                              initial_dynamic_status=attempts[0]['dynamic_status'],
                              cost=_cost([entry.get('model_request') for entry in calls],
                                         [run/'attempts'/str(entry['iteration'])/'response.json' for entry in calls],
                                         round(sum(entry['elapsed_seconds'] for entry in attempts), 6)))
            except errors as exc:
                branch['reason'] = str(exc)
            _write_json(folder/'pair.json', report)
        shared = None
        for condition in order:
            branch = report['branches'][condition]
            if branch['status'] not in ('LOLOS', 'BELUM LOLOS'):
                continue
            try:
                path = evaluate(Path(branch['run_directory']), folder/'evaluations', reference,
                                shared_initial=shared)/'evaluation_result.json'
                evaluation = _json(path)
                branch['evaluation'] = {'status': evaluation['status'], 'reason': evaluation['reason'],
                                        'report': str(path)}
                if (evaluation.get('initial') or {}).get('total') is not None:
                    shared = shared or path
                if evaluation['status'] == 'EVALUATED':
                    branch['evaluation'].update(initial_pass_rate=evaluation['initial']['pass_rate'],
                                                final_pass_rate=evaluation['final']['pass_rate'],
                                                uplift_pp=evaluation['uplift_pp'])
            except errors as exc:
                branch['evaluation'] = {'status': 'ERROR', 'reason': str(exc)}
        a, b = (report['branches'][key].get('evaluation', {}) for key in ('A', 'B'))
        if a.get('status') == b.get('status') == 'EVALUATED':
            report.update(status='EVALUATED', n_ab=1, delta_final_pp=a['final_pass_rate']-b['final_pass_rate'])
        else:
            report.update(status='ERROR', reason='incomplete_pair')
    except errors as exc:
        report.update(status='ERROR', reason=str(exc))
    except KeyboardInterrupt:
        report.update(status='ERROR', reason='user_cancelled')
        raise
    finally:
        _write_json(folder/'pair.json', report)
    return folder
