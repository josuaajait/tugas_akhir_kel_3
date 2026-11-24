"""Regressions for fresh review findings. All attestation names are UNIT FIXTURES."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from critic_agent.ab import run_ab
from critic_agent.ab_archive import ROOT,artifact_index,engine_manifest,relative,sha
from critic_agent.ab_final import SyntheticClient
from critic_agent.ab_protocol import check_protocol
from critic_agent.ab_report import ab_report,read_pair
from critic_agent.final_package import PACKAGE,RESOURCES,package_manifest
from test_ab_final import META,BoundRunner,make_pair,static_ok


def reseal(folder,report):
    report['artifacts']=artifact_index(folder)
    (folder/'pair.json').write_text(json.dumps(report))


def reviewed_fixture(folder):
    """Synthetic unit attestations in disposable work/, never actual human review."""
    plan=json.loads((ROOT/'docs/evidence/final-ab-plan-2026-11-23.draft.json').read_bytes())
    plan.update(status='FROZEN',ready_for_final=True,frozen_at='2001-01-01T00:00:00+00:00',engine_source_sha256=engine_manifest()[0])
    plan['configuration']={'model':'qwen2.5:7b-instruct','model_digest':'a'*64,'endpoint':'http://127.0.0.1:11434',
        'options':{'temperature':0.2,'num_ctx':8192,'num_predict':4096},'max_revisions':3,
        'model_timeout_seconds':300,'test_timeout_seconds':120}
    plan['review_attestations']=[];plan['artifacts']=[]
    for resource in RESOURCES:
        original=PACKAGE/'review'/(resource+'.json');meta=package_manifest(resource)
        record=json.loads(original.read_bytes())
        record.update(status='reviewed',human_author='UNIT FIXTURE Author',reviewer='UNIT FIXTURE Reviewer',
                      reviewed_at='2000-01-01T00:00:00+00:00',package_sha256=meta['package_sha256'],
                      spec_sha256=meta['spec_sha256'],blank_form_sha256=sha(original))
        for decision in record['decisions']:
            decision.update(decision='approved',rationale='UNIT TEST ONLY; not an actual human attestation.')
        path=folder/(resource+'-unit-review.json');path.write_text(json.dumps(record))
        binding={'resource':resource,'path':relative(ROOT,path),'sha256':sha(path)}
        plan['review_attestations'].append(binding);plan['artifacts'].append({k:binding[k] for k in ('path','sha256')})
    decisions={'status':'approved','human_author':'UNIT FIXTURE Author','reviewer':'UNIT FIXTURE Reviewer',
               'reviewed_at':'2000-01-01T00:00:00+00:00','fr20':'execute','component_review':'reviewed',
               'k2':{'precision_min_percent':80,'recall_min_percent':75,'fpr_max_percent':20}}
    path=folder/'unit-decisions.json';path.write_text(json.dumps(decisions))
    plan['decisions']={**decisions,'evidence_path':relative(ROOT,path)}
    plan['artifacts'].append({'path':relative(ROOT,path),'sha256':sha(path)})
    evidence=ROOT/'docs/evidence/final-v1-validation-2026-11-23.json'
    plan['validation_evidence']={'path':relative(ROOT,evidence),'sha256':sha(evidence)}
    plan['artifacts'].append(plan['validation_evidence'])
    path=folder/'UNIT-ONLY-protocol.json';path.write_text(json.dumps(plan))
    return path,plan


class ABReviewRegressions(unittest.TestCase):
    def test_external_review_fixture_passes_without_editing_packet_or_mocking_reviews(self):
        before=package_manifest('categories')['package_sha256']
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            path,_=reviewed_fixture(Path(tmp))
            checked=check_protocol(path)
            self.assertEqual(checked['status'],'READY',checked)
        self.assertEqual(package_manifest('categories')['package_sha256'],before)

    def test_final_absolute_fallback_and_pair_stop_reason_tampering_are_invalid(self):
        for change in ('outside','reason','response','candidate_binding','case_ids','iteration_receipt','budget'):
            with self.subTest(change=change),tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                root=Path(tmp);folder,_,_,_=make_pair(root)
                report=json.loads((folder/'pair.json').read_bytes());branch=report['branches']['B']
                if change=='outside':
                    copied=root/'copied';shutil.copytree(folder,copied);folder=copied
                    del branch['run_path'];del branch['evaluation']['report_path']
                elif change=='reason':branch['reason']='max_revisions'
                elif change=='response':
                    attempt=folder/branch['run_path']/'attempts/0'
                    (attempt/'response.txt').write_text('<?php // changed initial response')
                elif change in ('candidate_binding','case_ids'):
                    file=folder/branch['evaluation']['report_path'];evaluation=json.loads(file.read_bytes())
                    raw=evaluation['final']['runner_result']
                    if change=='candidate_binding':raw['candidate_sha256']='0'*64
                    else:raw['summary']['cases'][0]['name']='wrong_test'
                    file.write_text(json.dumps(evaluation))
                elif change=='iteration_receipt':
                    file=folder/branch['run_path']/'attempts/1/result.json';data=json.loads(file.read_bytes())
                    data['model_called']=False;file.write_text(json.dumps(data))
                else:
                    report.update(revision_seeds=[],max_revisions=0)
                    for item in report['branches'].values():
                        file=folder/item['run_path']/'run_manifest.json';data=json.loads(file.read_bytes())
                        data['max_revisions']=0;data['ab']['revision_seeds']=[];file.write_text(json.dumps(data))
                reseal(folder,report)
                row=ab_report(folder)['pairs'][0]
                self.assertEqual(row['status'],'INVALID',change)

    def test_claim_only_retry_and_synthetic_descendant_never_credit_a_slot(self):
        plan=ROOT/'docs/evidence/final-ab-plan-2026-11-23.draft.json'
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            root=Path(tmp);claim=root/'P01';claim.mkdir()
            (claim/'execution.json').write_text(json.dumps({'status':'ERROR','pair_slot':'P01','protocol_sha256':sha(plan)}))
            make_pair(claim)
            result=ab_report(root,plan=plan)
            self.assertNotEqual(result['planned_slots'][0]['status'],'EVALUATED')
            self.assertEqual(result['plan_summary']['n_ab'],0)

    def test_early_interrupt_always_propagates_even_without_loop_json_files(self):
        from critic_agent.ab_final import FinalABAdapter
        client=SyntheticClient('categories');adapter=FinalABAdapter(META['spec'],client,BoundRunner(),BoundRunner('reference'),
                {'stage':'synthetic_validation','origin':'synthetic_validation'})
        def interrupted(spec,root,*args,**kwargs):
            (Path(root)/'new_loop_fixture').mkdir(parents=True)
            raise KeyboardInterrupt()
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp,patch('critic_agent.ab_final._run_loop',side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):adapter.loop(META['spec'],Path(tmp),client,BoundRunner())

    def test_running_pair_keeps_completed_branch_details_but_no_complete_ab(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            folder,_,_,_=make_pair(Path(tmp));r=json.loads((folder/'pair.json').read_bytes())
            r.update(status='RUNNING',n_ab=0,delta_final_pp=None);r.pop('artifacts')
            (folder/'pair.json').write_text(json.dumps(r))
            result=ab_report(Path(tmp));row=result['pairs'][0]
            self.assertEqual(row['status'],'INCOMPLETE');self.assertEqual(row['n_ab'],0)
            self.assertEqual(row['branches']['A']['status'],'LOLOS')

    def test_branch_cost_and_output_failure_counts_are_available(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            make_pair(Path(tmp),scenario='format_fail')
            spec=ab_report(Path(tmp))['cohorts'][0]['specifications'][0]
            self.assertIn('cost',spec['conditions']['A'])
            self.assertEqual(spec['conditions']['B']['outputs']['initial']['UNAVAILABLE_CODE'],1)

    def test_final_execution_refuses_direct_calls_imports_and_custom_analysis(self):
        from critic_agent.ab_final import FinalABAdapter
        from critic_agent.ab_protocol import FrozenClient
        client=FrozenClient(SyntheticClient('categories'),'a'*64)
        with self.assertRaisesRegex(ValueError,'claimed'):
            FinalABAdapter(META['spec'],client,BoundRunner(),BoundRunner('reference'),
                           {'protocol_path':str(ROOT/'docs/evidence/final-ab-plan-2026-11-23.draft.json'),'pair_slot':'P01'})
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            for extra in ({'initial_run':'anything'},{'static_analyzer':static_ok}):
                with self.subTest(extra=extra),self.assertRaisesRegex(ValueError,'fresh initial'):
                    run_ab(META['spec'],tmp,client,BoundRunner(),BoundRunner('reference'),kind='final',
                           order_seed=7,revision_seeds=[102,103,104],final_context={},**extra)
            self.assertFalse(list(Path(tmp).iterdir()))

    def test_exclusive_executor_rejects_digest_endpoint_or_runner_timeout_drift(self):
        from critic_agent.ab_protocol import execute_protocol_pair,validate_final_context
        from critic_agent.ollama import ModelError
        class Client:
            def __init__(self,**kwargs):
                self.model=kwargs['model'];self.base_url=kwargs['base_url'];self.timeout=kwargs['timeout']
                self.options={'seed':kwargs['seed']};self.last_transport_attempts=[]
            def model_identity(self):return {'status':'observed','digest':'a'*64}
            def generate(self,prompt):raise AssertionError('UNIT fixture must never generate')
        for change in ('digest','endpoint','timeout','source','protocol'):
            with self.subTest(change=change),tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                folder=Path(tmp);path,_=reviewed_fixture(folder)
                def checked(spec,output,client,runner,reference,**kwargs):
                    if change=='digest':client.digest='b'*64
                    elif change=='endpoint':client.client.base_url='http://localhost:11435'
                    elif change=='timeout':reference.timeout=1
                    elif change=='protocol':path.write_text('{}') # original is no longer authoritative
                    if change in ('digest','endpoint','timeout'):
                        with self.assertRaises(ValueError):
                            validate_final_context(kwargs['final_context'],spec,client,runner,reference)
                    else:
                        validate_final_context(kwargs['final_context'],spec,client,runner,reference)
                        if change=='source':
                            with patch('critic_agent.ab_protocol.engine_manifest',return_value=('changed',{})),self.assertRaises(ModelError):
                                client.generate('UNIT fixture')
                        else:
                            # Changing the original after the exclusive copy cannot change the active protocol.
                            self.assertNotEqual(Path(kwargs['final_context']['protocol_path']),path)
                    result=Path(output)/'UNIT-only-pair';result.mkdir();(result/'pair.json').write_text('{"status":"ERROR"}')
                    return result
                with patch('critic_agent.ab_protocol.OllamaClient',side_effect=Client),patch('critic_agent.ab.run_ab',side_effect=checked):
                    execute_protocol_pair(path,'P01',folder/'claims')

    def test_claim_only_retry_blocks_complete_slot_even_without_plan_argument(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            root=Path(tmp);row_folder=root/'first/pair';row_folder.mkdir(parents=True)
            pair=row_folder/'pair.json';pair.write_text('{}')
            second=root/'second';second.mkdir()
            for claim_root,status in ((row_folder.parent,'EVALUATED'),(second,'ERROR')):
                (claim_root/'execution.json').write_text(json.dumps({'status':status,'pair_slot':'P01','protocol_sha256':'a'*64}))
            row={'status':'EVALUATED','pair_id':'UNIT-pair','report':str(pair),'kind':'final','origin':'qwen_final',
                 'pair_slot':'P01','protocol_sha256':'a'*64,'branches':{},'n_ab':1,'delta_final_pp':1}
            with patch('critic_agent.ab_report.read_pair',return_value=row):
                result=ab_report(root)
            self.assertEqual(result['counts']['AMBIGUOUS'],1)
            self.assertEqual(result['pairs'][0]['n_ab'],0)

    def test_malformed_archive_exception_does_not_abort_other_pairs(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            root=Path(tmp)
            for name in ('broken','valid'):
                (root/name).mkdir();(root/name/'pair.json').write_text('{}')
            def fixture(path):
                if path.parent.name=='broken':raise IndexError('UNIT malformed seed lookup')
                return {'status':'INCOMPLETE','pair_id':'UNIT-valid','report':str(path),'branches':{},'n_ab':0}
            with patch('critic_agent.ab_report.read_pair',side_effect=fixture):result=ab_report(root)
            self.assertEqual(result['counts']['INVALID'],1)
            self.assertEqual(result['counts']['INCOMPLETE'],1)
