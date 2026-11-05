import copy
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from critic_agent.component_corpus import prepare_development_corpus, load_corpus
from critic_agent.component_evaluation import run_components, collect_component_evidence
from critic_agent.component_report import summarize_components, component_report
from critic_agent.cli import main
from test_resources import BOOKS
from test_foundation import temporary_directory
from critic_agent.resource_reference import resource_reference_manifest


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(data, indent=2)+'\n').encode())


def fixture(root, definitions):
    cases = []
    for index, definition in enumerate(definitions):
        case_id = definition.get('case_id', 'case_'+str(index))
        folder = root/'cases'/case_id
        folder.mkdir(parents=True)
        code = definition.get('code', '<?php\n// fixture '+case_id+'\n').encode()
        (folder/'controller.php').write_bytes(code)
        write_json(folder/'spec.json', BOOKS)
        code_hash = hashlib.sha256(code).hexdigest()
        spec_hash = hashlib.sha256((folder/'spec.json').read_bytes()).hexdigest()
        value = definition.get('truth', 'problematic')
        review = {'status': 'draft', 'author': None, 'reviewer': None,
                  'reviewed_at': None, 'blinded_to_prediction': False}
        evidence = [{'kind': 'code_inspection', 'detail': 'Controlled test fixture, not research data.'}]
        if definition.get('reviewed', True):
            review.update(status='reviewed', author='Author fixture', reviewer='Reviewer fixture',
                          reviewed_at='2026-11-01T00:00:00+00:00', blinded_to_prediction=True)
            n=35
            passed=n if value=='correct' else n-1
            ev = {'evidence_type': 'independent_reference', 'code_sha256': code_hash, 'spec_sha256': spec_hash,
                  'expected_tests':n,'suite_sha256':resource_reference_manifest(BOOKS)['suite_sha256'],
                  'result': {'status': 'PASSED_REFERENCE' if value == 'correct' else 'FAILED_REFERENCE',
                    'candidate_sha256':code_hash,'image_id':'sha256:'+'b'*64,'cleanup_exit_code':0,
                    'summary':{'total':n,'passed':passed,'failure':n-passed,'error':0,'skipped':0,
                               'cases':[{'name':'t'+str(i),'class':'fixture','outcome':'passed' if i<passed else 'failure'} for i in range(n)]}}}
            write_json(folder/'reference.json', ev)
            evidence.append({'kind': 'independent_reference', 'path': f'cases/{case_id}/reference.json',
                             'sha256': hashlib.sha256((folder/'reference.json').read_bytes()).hexdigest()})
        case = {'case_id': case_id, 'corpus': definition.get('corpus', 'synthetic'),
                'used_for_development': True, 'origin': {'kind': 'unit_fixture', 'artifacts': []},
                'code_path': f'cases/{case_id}/controller.php', 'code_sha256': code_hash,
                'spec_path': f'cases/{case_id}/spec.json', 'spec_sha256': spec_hash,
                'label': {'value': value, 'violations': [] if value != 'problematic' else [
                    {'category': 'fixture', 'coverage': definition.get('coverage', 'internal_covered'), 'detail': 'Test-only label'}],
                          'evidence': evidence, 'review': review}}
        cases.append(case)
    manifest = {'schema_version': '1.0', 'corpus_id': 'unit_fixture', 'stage': 'development',
                'selection': {'description': 'Unit fixtures only'}, 'cases': cases}
    write_json(root/'corpus.json', manifest)
    return root/'corpus.json'


def observation(case, prediction):
    return {**copy.deepcopy(case), 'prediction': prediction,
            'findings': [{'explanation': 'observed'}]*7 if prediction == 'problematic' else [],
            'status': 'ERROR' if prediction == 'unknown' else 'PREDICTED'}


class ComponentCorpusTests(unittest.TestCase):
    def test_malformed_nested_objects_are_input_errors(self):
        for field in ('label','origin'):
            with temporary_directory() as tmp:
                path=fixture(Path(tmp),[{}])
                data=json.loads(path.read_text());data['cases'][0][field]=[]
                write_json(path,data)
                with self.assertRaises(ValueError): load_corpus(path)
    def test_status_only_or_wrong_candidate_reference_cannot_qualify_review(self):
        for wrong in ('status_only','candidate_hash','partial'):
            with temporary_directory() as tmp:
                root=Path(tmp);path=fixture(root,[{}])
                manifest=json.loads(path.read_text())
                evidence_path=root/'cases/case_0/reference.json'
                raw=json.loads(evidence_path.read_text())
                if wrong=='status_only': raw['result']={'status':'PASSED_REFERENCE'}
                elif wrong=='candidate_hash': raw['result']['candidate_sha256']='c'*64
                else: raw['result']['summary']['total']=1
                write_json(evidence_path,raw)
                manifest['cases'][0]['label']['evidence'][-1]['sha256']=hashlib.sha256(evidence_path.read_bytes()).hexdigest()
                write_json(path,manifest)
                with self.assertRaises(ValueError): load_corpus(path)

    def test_changed_archived_prompt_is_rejected_during_import(self):
        from critic_agent import component_corpus
        with temporary_directory() as tmp:
            root=Path(tmp);source=root/'runs'/'selected_loop'
            attempt=source/'attempts/0';attempt.mkdir(parents=True)
            code=b'<?php\n// controlled source\n'
            (attempt/'controller.php').write_bytes(code)
            (attempt/'prompt.txt').write_text('tampered')
            write_json(source/'spec.json',BOOKS)
            write_json(source/'run_manifest.json',{'spec_sha256':hashlib.sha256((source/'spec.json').read_bytes()).hexdigest(),
                      'model':'qwen-fixture','options':{},'prototype_version':'fixture'})
            write_json(source/'history.json',{'attempts':[{'iteration':0,'code_sha256':hashlib.sha256(code).hexdigest(),
                       'prompt_sha256':hashlib.sha256(b'original').hexdigest()}]})
            with patch.object(component_corpus,'SOURCE_RUNS',('selected_loop',)),self.assertRaises(ValueError):
                prepare_development_corpus(root/'prepared',runs_root=root/'runs')

    def test_imported_generation_spec_is_bound_to_its_own_bytes_and_same_semantics(self):
        from critic_agent import component_corpus
        with temporary_directory() as tmp:
            root=Path(tmp);runs=root/'runs';source=runs/'selected_loop';generation=runs/'generation'
            attempt=source/'attempts/0';attempt.mkdir(parents=True);generation.mkdir()
            code=b'<?php\n// controlled source\n'
            (attempt/'controller.php').write_bytes(code)
            (attempt/'response.txt').write_bytes(code)
            write_json(attempt/'response.json',{'response':code.decode()})
            write_json(source/'spec.json',BOOKS)
            # Generation and loop serialize identical JSON with different whitespace.
            (generation/'spec.json').write_bytes(json.dumps(BOOKS,separators=(',',':')).encode())
            (generation/'prompt.txt').write_bytes(b'original prompt')
            write_json(source/'initial_source_manifest.json',{'code_sha256':hashlib.sha256(code).hexdigest(),
                       'spec_sha256':hashlib.sha256((generation/'spec.json').read_bytes()).hexdigest(),
                       'prompt_sha256':hashlib.sha256(b'original prompt').hexdigest()})
            write_json(source/'run_manifest.json',{'initial_source':str(generation),
                       'spec_sha256':hashlib.sha256((source/'spec.json').read_bytes()).hexdigest(),
                       'model':'qwen-fixture','options':{},'prototype_version':'fixture'})
            write_json(source/'history.json',{'attempts':[{'iteration':0,'code_sha256':hashlib.sha256(code).hexdigest()}]})
            with patch.object(component_corpus,'SOURCE_RUNS',('selected_loop',)):
                folder=prepare_development_corpus(root/'prepared',runs_root=runs)
            self.assertEqual(len(load_corpus(folder/'corpus.json')['records']),11)
    def test_hash_and_traversal_rejected_before_execution(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            path = fixture(root, [{}])
            (root/'cases/case_0/controller.php').write_text('changed')
            with self.assertRaises(ValueError): load_corpus(path)
        with temporary_directory() as tmp:
            root = Path(tmp)
            path = fixture(root, [{}])
            manifest = json.loads(path.read_text())
            manifest['cases'][0]['code_path'] = '../outside.php'
            write_json(path, manifest)
            with self.assertRaises(ValueError): load_corpus(path)

    def test_review_requires_distinct_names_and_matching_reference_evidence(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            path = fixture(root, [{}])
            manifest = json.loads(path.read_text())
            manifest['cases'][0]['label']['review']['reviewer'] = 'Author fixture'
            write_json(path, manifest)
            with self.assertRaises(ValueError): load_corpus(path)

    def test_synthetic_corpus_has_two_valid_styles_and_reference_only_cases(self):
        with temporary_directory() as tmp:
            folder = prepare_development_corpus(Path(tmp), synthetic_only=True)
            loaded = load_corpus(folder/'corpus.json')
            cases = loaded['manifest']['cases']
            self.assertEqual(len(cases), 10)
            self.assertEqual(sum(c['label']['value'] == 'correct' for c in cases), 2)
            self.assertEqual(sum(any(v['coverage'] == 'reference_only' for v in c['label']['violations']) for c in cases), 2)
            self.assertTrue(all(c['label']['review']['status'] == 'draft' for c in cases))
            self.assertTrue(all(c['corpus'] == 'synthetic' for c in cases))


class ComponentMetricsTests(unittest.TestCase):
    def test_code_level_confusion_and_reference_only_false_negative(self):
        with temporary_directory() as tmp:
            path = fixture(Path(tmp), [{'truth': 'problematic'}, {'truth': 'problematic', 'coverage': 'reference_only'},
                                       {'truth': 'correct'}, {'truth': 'correct'}])
            cases = load_corpus(path)['manifest']['cases']
            rows = [observation(c,p) for c,p in zip(cases, ('problematic','correct','problematic','correct'))]
            report = summarize_components(rows, started_at='2026-11-04T00:00:00+00:00')
            group = report['groups']['synthetic']
            self.assertEqual(group['matrix'], {'TP': 1, 'FP': 1, 'TN': 1, 'FN': 1})
            self.assertEqual(group['precision'], {'numerator': 1, 'denominator': 2, 'percent': 50.0})
            self.assertEqual(group['recall']['percent'], 50)
            self.assertEqual(group['fpr']['percent'], 50)
            self.assertEqual(group['by_coverage']['reference_only']['FN'], 1)

    def test_drafts_excluded_and_provisional_is_explicit(self):
        with temporary_directory() as tmp:
            cases = load_corpus(fixture(Path(tmp), [{'reviewed': False}]))['manifest']['cases']
            rows = [observation(cases[0], 'problematic')]
            official = summarize_components(rows, started_at='2026-11-04T00:00:00+00:00')
            self.assertIsNone(official['groups']['synthetic']['precision']['percent'])
            self.assertEqual(official['groups']['synthetic']['eligible'], 0)
            provisional = summarize_components(rows, provisional=True, started_at='2026-11-04T00:00:00+00:00')
            self.assertEqual(provisional['label_mode'], 'provisional_unreviewed')
            self.assertEqual(provisional['groups']['synthetic']['matrix']['TP'], 1)

    def test_duplicates_deduplicated_per_origin_and_errors_not_false_negative(self):
        with temporary_directory() as tmp:
            cases = load_corpus(fixture(Path(tmp), [{'code': '<?php\n// same\n'}, {'code': '<?php\n// same\n'},
                {'code': '<?php\n// same\n', 'corpus': 'qwen_formative'}, {}]))['manifest']['cases']
            rows = [observation(c,p) for c,p in zip(cases, ('problematic','problematic','problematic','unknown'))]
            report = summarize_components(rows, started_at='2026-11-04T00:00:00+00:00')
            self.assertEqual(report['groups']['synthetic']['matrix']['TP'], 1)
            self.assertEqual(report['groups']['synthetic']['excluded']['duplicate'], 1)
            self.assertEqual(report['groups']['synthetic']['excluded']['prediction_error'], 1)
            self.assertEqual(report['groups']['qwen_formative']['matrix']['TP'], 1)
            self.assertIsNone(report['groups']['qwen_held_out']['recall']['percent'])

    def test_conflicting_labels_and_late_review_excluded(self):
        with temporary_directory() as tmp:
            cases = load_corpus(fixture(Path(tmp), [{'code': '<?php\n// same\n'}, {'code': '<?php\n// same\n','truth':'correct'}]))['manifest']['cases']
            report = summarize_components([observation(c,'problematic') for c in cases], started_at='2026-11-04T00:00:00+00:00')
            self.assertEqual(report['groups']['synthetic']['eligible'], 0)
            self.assertEqual(report['groups']['synthetic']['excluded']['conflicting_labels'], 2)
            report = summarize_components([observation(cases[0],'problematic')], started_at='2026-10-01T00:00:00+00:00')
            self.assertEqual(report['groups']['synthetic']['excluded']['review_after_prediction'], 1)


class ComponentExecutionTests(unittest.TestCase):
    def test_original_manifest_bytes_are_preserved(self):
        with temporary_directory() as tmp:
            root=Path(tmp);path=fixture(root/'corpus',[{}])
            data=json.loads(path.read_text());path.write_bytes(json.dumps(data,indent=4).encode())
            original=path.read_bytes()
            static=lambda c,s:{'findings':[{'source':'static','location':{'method':'show'},'explanation':'fixture','evidence':'fixture'}]}
            folder=run_components(path,root/'runs',static_analyzer=static)
            self.assertEqual((folder/'source_manifest.json').read_bytes(),original)
            (folder/'source_manifest.json').write_bytes(b'{}')
            with self.assertRaises(ValueError): component_report(folder)
    def test_static_findings_skip_docker_and_multiple_findings_still_one_positive(self):
        with temporary_directory() as tmp:
            root = Path(tmp)
            path = fixture(root/'corpus', [{}])
            static = lambda code,spec: {'findings':[{'source':'static','location':{'method':'show'},'explanation':'missing','evidence':'x'}]*4}
            def no_docker(*args): self.fail('Static finding must skip dynamic execution')
            folder = run_components(path, root/'runs', static_analyzer=static, runner_factory=no_docker)
            data = json.loads((folder/'predictions.json').read_text())
            self.assertEqual(data['cases'][0]['prediction'], 'problematic')
            result = component_report(folder)
            self.assertEqual(result['groups']['synthetic']['matrix']['TP'], 1)

    def test_complete_pass_negative_partial_unknown_and_reuse(self):
        class Runner:
            candidate_tests = 12
            image = 'test'
            calls = 0
            def check_candidate(self, path):
                self.calls += 1
                return {'status':'PASSED_INTERNAL','image_id':'sha256:'+'a'*64,'candidate_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                        'cleanup_exit_code':0,
                        'summary':{'total':12,'passed':12,'failure':0,'error':0,'skipped':0,'cases':[]}}
        with temporary_directory() as tmp:
            root=Path(tmp)
            path=fixture(root/'corpus',[{'code':'<?php\n// same\n','truth':'correct'}, {'code':'<?php\n// same\n','truth':'correct'}])
            runner=Runner()
            folder=run_components(path,root/'runs',static_analyzer=lambda c,s:{'findings':[]}, runner_factory=lambda s,o:runner)
            result=json.loads((folder/'predictions.json').read_text())
            self.assertEqual(runner.calls,1)
            self.assertEqual([c['prediction'] for c in result['cases']],['correct','correct'])
            self.assertEqual(result['cases'][1]['reused_from'],'case_0')
            (root/'corpus/cases/case_0/controller.php').write_text('changed after snapshot')
            self.assertEqual(component_report(folder)['groups']['synthetic']['matrix']['TN'],1)

    def test_reference_evidence_does_not_promote_labels(self):
        class Runner:
            candidate_tests=35
            def check_candidate(self,path):
                return {'status':'PASSED_REFERENCE','image_id':'sha256:'+'b'*64,'candidate_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                        'cleanup_exit_code':0,'summary':{'total':35,'passed':35,'failure':0,'error':0,'skipped':0,
                         'cases':[{'name':'t'+str(i),'class':'fixture','outcome':'passed'} for i in range(35)]}}
        with temporary_directory() as tmp:
            root=Path(tmp)
            path=fixture(root/'corpus',[{'reviewed':False,'truth':'correct'}])
            folder=collect_component_evidence(path,root/'evidence',runner_factory=lambda s,o:Runner())
            loaded=load_corpus(folder/'corpus.json')
            case=loaded['manifest']['cases'][0]
            self.assertEqual(case['label']['review']['status'],'draft')
            self.assertTrue(any(e['kind']=='independent_reference' for e in case['label']['evidence']))
            self.assertTrue((folder/'review/decisions.json').exists())
            decisions=json.loads((folder/'review/decisions.json').read_text())
            self.assertIsNone(decisions['cases'][0]['value'])
            self.assertFalse((folder/'review/predictions.json').exists())

    def test_partial_dynamic_result_is_unknown_and_snapshot_report_tampering_rejected(self):
        class Runner:
            candidate_tests=12
            def check_candidate(self,path):
                return {'status':'PASSED_INTERNAL','image_id':'sha256:'+'a'*64,
                        'candidate_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                        'summary':{'total':1,'passed':1,'failure':0,'error':0,'skipped':0,'cases':[]}}
        with temporary_directory() as tmp:
            root=Path(tmp)
            path=fixture(root/'corpus',[{}])
            folder=run_components(path,root/'runs',static_analyzer=lambda c,s:{'findings':[]},runner_factory=lambda s,o:Runner())
            predictions=json.loads((folder/'predictions.json').read_text())
            self.assertEqual(predictions['cases'][0]['prediction'],'unknown')
            self.assertEqual(component_report(folder)['groups']['synthetic']['excluded']['prediction_error'],1)
            predictions['cases'][0]['prediction']='correct'
            write_json(folder/'predictions.json',predictions)
            with self.assertRaises(ValueError): component_report(folder)

    def test_failed_candidate_with_failed_cleanup_is_unknown(self):
        class Runner:
            candidate_tests=12
            def check_candidate(self,path):
                return {'status':'FAILED_INTERNAL','image_id':'sha256:'+'a'*64,
                        'candidate_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'cleanup_exit_code':1,
                        'summary':{'total':12,'passed':11,'failure':1,'error':0,'skipped':0,
                                  'cases':[{'name':'bad','outcome':'failure','evidence':'wrong status'}]}}
        with temporary_directory() as tmp:
            root=Path(tmp);path=fixture(root/'corpus',[{}])
            folder=run_components(path,root/'runs',static_analyzer=lambda c,s:{'findings':[]},runner_factory=lambda s,o:Runner())
            data=json.loads((folder/'predictions.json').read_text())
            self.assertEqual(data['cases'][0]['prediction'],'unknown')

    def test_cli_help_and_no_model_call(self):
        for command in ('component-corpus-init','component-evidence','component-run','component-report'):
            with redirect_stdout(io.StringIO()),self.assertRaises(SystemExit) as error: main([command,'--help'])
            self.assertEqual(error.exception.code,0)
        with temporary_directory() as tmp,patch('critic_agent.cli.OllamaClient') as model,redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['component-corpus-init','--synthetic-only','--output',tmp]),0)
            self.assertEqual(json.loads(output.getvalue())['case_count'],10)
            model.assert_not_called()
