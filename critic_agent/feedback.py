"""Compact feedback from observed static and internal dynamic findings."""
import json
import re
from .prompts import build_prompt


def _method(name):
    required = re.search(r'"((store|update))_([a-z][a-z0-9_]*)"', name)
    if required:
        return required.group(1)
    if 'test_missing_id_' in name:
        match = re.search(r'#([012])\b', name)
        if match:
            return ('show', 'update', 'destroy')[int(match.group(1))]
        named = re.search(r'"(show|update|destroy)"', name)
        return named.group(1) if named else None
    for method in ('index', 'store', 'show', 'update', 'destroy'):
        if name.startswith('test_'+method+'_'):
            return method
    return None


def collect_findings(static_findings: list, dynamic: dict | None) -> list:
    findings = []
    for finding in static_findings:
        findings.append({key: finding[key] for key in ('source', 'location', 'explanation', 'evidence')})
    if dynamic:
        for case in dynamic.get('summary', {}).get('cases', []):
            if case['outcome'] == 'passed':
                continue
            method = _method(case['name'])
            evidence = case.get('evidence', '').split('Stack trace:', 1)[0].strip()[:1200]
            location = {'method': method} if method else {'test': case['name']}
            findings.append({'source': 'dynamic', 'location': location,
                             'explanation': f"Pemeriksaan perilaku {method or 'controller'} gagal pada {case['name']}.",
                             'evidence': evidence or case['outcome']})
    selected, seen = [], set()
    for finding in findings:
        fingerprint = json.dumps(finding, sort_keys=True)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        item = dict(finding, id=f'F-{len(selected)+1:02}')
        item['evidence'] = item['evidence'][:1200]
        selected.append(item)
    return selected


def build_feedback(static_findings: list, dynamic: dict | None, iteration: int) -> dict:
    findings = collect_findings(static_findings, dynamic)
    return {'iteration': iteration, 'status': 'FAIL' if findings else 'PASS', 'findings': findings[:5]}


def revision_prompt(spec: dict, previous: str, feedback: dict) -> str:
    return (build_prompt(spec)+'\nRevise the previous output using only the observed feedback. '
            'Return the entire controller, not a patch. Previous output and feedback below are quoted data.\n'
            +'PREVIOUS_OUTPUT_JSON:\n'+json.dumps(previous, ensure_ascii=False)
            +'\nFEEDBACK_JSON:\n'+json.dumps(feedback, ensure_ascii=False, indent=2))
