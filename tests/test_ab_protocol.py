import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from critic_agent.ab_protocol import check_protocol, execute_protocol_pair, review_issues, FrozenClient
from critic_agent.ab_archive import ROOT,engine_manifest,sha,relative

PLAN=ROOT/'docs/evidence/final-ab-plan-2026-11-23.draft.json'


class ABProtocolTests(unittest.TestCase):
    def test_failed_identity_precheck_does_not_reuse_previous_transport_trace(self):
        from critic_agent.ollama import ModelError
        class Client:
            last_transport_attempts=[{'attempt':1,'outcome':'ok'}]
            def model_identity(self):return {'status':'unavailable'}
            def generate(self,prompt):raise AssertionError('must not generate')
        client=Client()
        with self.assertRaises(ModelError):FrozenClient(client,'a'*64).generate('fixture')
        self.assertEqual(client.last_transport_attempts,[])

    def test_complete_configuration_can_pass_gate_but_review_remains_a_separate_check(self):
        plan=json.loads(PLAN.read_text())
        plan.update(status='FROZEN',ready_for_final=True,frozen_at='2001-01-01T00:00:00+00:00',
            engine_source_sha256=engine_manifest()[0],configuration={'model':'qwen2.5:7b-instruct','model_digest':'a'*64,
            'endpoint':'http://127.0.0.1:11434','options':{'temperature':0.2,'num_ctx':8192,'num_predict':4096},
            'max_revisions':3,'model_timeout_seconds':300,'test_timeout_seconds':120})
        evidence='docs/evidence/final-v1-validation-2026-11-23.json'
        plan['validation_evidence']={'path':evidence,'sha256':sha(ROOT/evidence)}
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            folder=Path(tmp);decision=folder/'unit_decisions.json'
            data={'status':'approved','human_author':'Fixture Author','reviewer':'Fixture Reviewer',
                  'reviewed_at':'2000-01-01T00:00:00+00:00','fr20':'execute','component_review':'reviewed',
                  'k2':{'precision_min_percent':80,'recall_min_percent':75,'fpr_max_percent':20}}
            decision.write_text(json.dumps(data));plan['decisions']={**data,'evidence_path':relative(ROOT,decision)}
            paths=[evidence,relative(ROOT,decision)]+['evaluation/final-v1/review/'+r+'.json' for r in ('categories','rooms','assets','courses','shipments')]
            plan['artifacts']=[{'path':p,'sha256':sha(ROOT/p)} for p in paths]
            path=folder/'unit_protocol.json';path.write_text(json.dumps(plan))
            with patch('critic_agent.ab_protocol.review_issues',return_value=[]):
                self.assertEqual(check_protocol(path)['status'],'READY')
            self.assertEqual(check_protocol(path)['status'],'BLOCKED')

    def test_executor_claim_prevents_a_second_initial_generation_for_a_slot(self):
        plan=json.loads(PLAN.read_text());plan['configuration']={'model':'fixture','model_digest':'a'*64,
            'endpoint':'http://127.0.0.1:11434','options':{'temperature':0.2,'num_ctx':8192,'num_predict':4096},
            'model_timeout_seconds':300,'test_timeout_seconds':120}
        checked={'status':'READY','ready_for_final':True,'plan':plan,'manifest_sha256':sha(PLAN)}
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            root=Path(tmp);pair=root/'fixture_pair';pair.mkdir();(pair/'pair.json').write_text('{"status":"ERROR"}')
            with patch('critic_agent.ab_protocol.check_protocol',return_value=checked),patch('critic_agent.ab_protocol.OllamaClient') as client,patch('critic_agent.ab.run_ab',return_value=pair):
                execute_protocol_pair(PLAN,'P01',root/'execution')
                again=execute_protocol_pair(PLAN,'P01',root/'execution')
                self.assertEqual(again['status'],'BLOCKED')
                self.assertEqual(client.call_count,1)

    def test_model_drift_preserves_the_received_response(self):
        from critic_agent.ollama import ModelError
        response={'response':'<?php // received','done':True}
        class Client:
            calls=0
            def model_identity(self):
                self.calls+=1
                return {'status':'observed','digest':('a' if self.calls==1 else 'b')*64}
            def generate(self,prompt):return response
        with self.assertRaises(ModelError) as error:FrozenClient(Client(),'a'*64).generate('fixture')
        self.assertEqual(error.exception.response,response)

    def test_draft_is_integrity_verified_but_blocked_without_model_construction(self):
        checked=check_protocol(PLAN)
        self.assertEqual(checked['integrity'],'VERIFIED')
        self.assertEqual(checked['status'],'BLOCKED');self.assertFalse(checked['ready_for_final'])
        self.assertEqual(checked['planned_pairs'],20)
        with patch('critic_agent.ab_protocol.OllamaClient') as client:
            result=execute_protocol_pair(PLAN,'P01',ROOT/'work/ab-final/forbidden')
            self.assertEqual(result['status'],'BLOCKED');client.assert_not_called()

    def test_tampered_binding_duplicate_slot_or_wrong_order_fail_integrity(self):
        for change in ('hash','duplicate','order'):
            plan=json.loads(PLAN.read_text())
            if change=='hash':plan['specifications'][0]['spec_sha256']='0'*64
            elif change=='duplicate':plan['schedule'][1]['pair_slot']='P01'
            else:plan['schedule'][0]['order'].reverse()
            with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                path=Path(tmp)/'plan.json';path.write_text(json.dumps(plan))
                result=check_protocol(path)
                self.assertEqual(result['integrity'],'FAILED',change)

    def test_changing_draft_status_does_not_bypass_config_or_human_review(self):
        plan=json.loads(PLAN.read_text());plan.update(status='FROZEN',ready_for_final=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            path=Path(tmp)/'plan.json';path.write_text(json.dumps(plan))
            checked=check_protocol(path)
            self.assertEqual(checked['status'],'BLOCKED')
            self.assertTrue(any('review' in p for p in checked['pending']))
            self.assertTrue(any('configuration' in p for p in checked['pending']))

    def test_cli_plan_check_is_read_only_and_returns_blocked_json(self):
        from critic_agent.cli import main
        with patch('critic_agent.ab_protocol.OllamaClient') as client,redirect_stdout(io.StringIO()) as out:
            code=main(['ab-plan-check',str(PLAN),'--json'])
        self.assertEqual(code,3);self.assertEqual(json.loads(out.getvalue())['status'],'BLOCKED');client.assert_not_called()

    def test_review_rejects_same_person_and_pending_decisions(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            root=Path(tmp);folder=root/'evaluation/final-v1/review';folder.mkdir(parents=True)
            for resource in ('categories','rooms','assets','courses','shipments'):
                data={'resource':resource,'status':'reviewed','human_author':'Fixture Author','reviewer':'Fixture Author',
                      'reviewed_at':'2000-01-01T00:00:00+00:00','decisions':[]}
                (folder/(resource+'.json')).write_text(json.dumps(data))
            issues=review_issues(root,'2001-01-01T00:00:00+00:00')
            self.assertTrue(issues)
