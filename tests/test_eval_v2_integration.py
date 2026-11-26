import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from critic_agent.eval_registry import get_package_api,get_sandbox_api
from critic_agent.eval_validation_v2 import assess_observation
from critic_agent.eval_controls_v2 import control_catalog
from critic_agent.ab_archive import ROOT,sha

class EvalV2IntegrationTests(unittest.TestCase):
    def test_version_registry_is_explicit_and_v1_is_not_replaced(self):
        self.assertEqual(get_package_api('final-v1').PACKAGE.name,'final-v1')
        api=get_package_api('final-v2');self.assertEqual(api.PACKAGE.name,'final-v2')
        runner=get_sandbox_api('final-v2').FinalRunner('categories','reference')
        self.assertEqual(runner.meta['package'],'final-v2');self.assertEqual(runner.candidate_tests,53)
        self.assertIn('critic-final-v2-',runner.image)
        with self.assertRaises(ValueError):get_package_api('../../work')

    def test_controlled_json_failure_is_assessable_but_environment_error_stays_unknown(self):
        api=get_package_api('final-v2');meta=api.package_manifest('categories')
        control=next(c for c in control_catalog('categories') if c['control_id']=='index_invalid_json')
        cases=[]
        for case in api.suite_cases(meta['spec'],meta['profile']):
            cid=case['case_id'];failed=cid in control['target_case_ids']
            evidence=control['failure_evidence'].get(cid,{})
            cases.append(api.test_id('reference',cid)|{'outcome':'failure' if failed else 'passed',
                'evidence':f"FINAL_ASSERTION:{cid}:{evidence.get('phase')}:HTTP{evidence.get('http_status')} Response must contain valid JSON" if failed else ''})
        raw={'status':'FAILED_REFERENCE','candidate_sha256':control['sha256'],'package_sha256':meta['package_sha256'],
             'suite_sha256':meta['reference_sha256'],'image_id':'sha256:'+'b'*64,'cleanup_exit_code':0,
             'summary':{'total':53,'passed':50,'failure':3,'error':0,'skipped':0,'cases':cases}}
        self.assertEqual(assess_observation(meta,'reference',control,raw,raw['image_id'])['status'],'PASS')
        for mutation in ('environment','cleanup','missing'):
            bad=copy.deepcopy(raw)
            if mutation=='environment':bad.update(status='ERROR',reason='docker_unavailable')
            elif mutation=='cleanup':bad['cleanup_exit_code']=1
            else:bad['summary']['cases'].pop()
            self.assertEqual(assess_observation(meta,'reference',control,bad,raw['image_id'])['status'],'UNKNOWN')

    def test_cli_v2_local_routing_never_constructs_model_or_docker(self):
        from critic_agent.cli import main
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp,patch('critic_agent.eval_validation_v2.local_checks',return_value={'status':'LOCAL_VALIDATED'}),patch('critic_agent.ollama.OllamaClient') as client,redirect_stdout(io.StringIO()) as out:
            code=main(['final-validate','--package','final-v2','--resource','categories','--local-only','--output',tmp,'--json'])
        self.assertEqual(code,0);self.assertEqual(json.loads(out.getvalue())['package'],'final-v2');client.assert_not_called()

    def test_v2_draft_protocol_integrity_and_pending_human_gate(self):
        from critic_agent.ab_protocol import check_protocol
        plan=json.loads((ROOT/'docs/evidence/final-ab-plan-2026-11-23.draft.json').read_bytes());plan['package']='final-v2'
        api=get_package_api('final-v2')
        for item,resource in zip(plan['specifications'],api.RESOURCES):
            meta=api.package_manifest(resource);plan['package_sha256']=meta['package_sha256']
            item.update(spec_path='evaluation/final-v2/specs/'+resource+'.json',spec_sha256=meta['spec_sha256'],
                        internal_suite_sha256=meta['internal_sha256'],reference_suite_sha256=meta['reference_sha256'])
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            file=Path(tmp)/'draft.json';file.write_text(json.dumps(plan))
            result=check_protocol(file)
        self.assertEqual(result['integrity'],'VERIFIED',result);self.assertEqual(result['status'],'BLOCKED')
        self.assertEqual(result['planned_pairs'],20)

    def test_v2_feedback_dataset_locations(self):
        from critic_agent.feedback import _method
        for cid,method in [('show_second','show'),('update_second','update'),('destroy_second','destroy'),('POST_short1_name','store'),('PUT_short2_name','update')]:
            self.assertEqual(_method('test_contract with data set '+chr(34)+cid+chr(34)),method)

    def test_v2_synthetic_pair_is_reported_with_v2_case_inventory(self):
        import hashlib
        from critic_agent.ab import run_ab
        from critic_agent.ab_final import SyntheticClient
        from critic_agent.ab_report import ab_report
        api=get_package_api('final-v2');meta=api.package_manifest('categories')
        class Runner:
            def __init__(self,role):
                self.role=role;self.resource='categories';self.meta=meta;self.candidate_tests=meta[role+'_tests']
                self.image='sha256:'+('a' if role=='internal' else 'b')*64;self.output_root=ROOT/'work';self.timeout=120
            def check_reference(self):return {'status':'READY','image_id':self.image,'suite_sha256':meta[self.role+'_sha256']}
            def check_candidate(self,path):
                content=Path(path).read_bytes();bad=b'202); // store response' in content
                cases=[]
                for case in api.suite_cases(meta['spec'],meta['profile'],self.role=='internal'):
                    failed=bad and case['case_id']=='store'
                    cases.append(api.test_id(self.role,case['case_id'])|{'outcome':'failure' if failed else 'passed',
                        'evidence':'FINAL_ASSERTION:store:status:HTTP202 Expected201 got202' if failed else ''})
                return {'status':('FAILED_' if bad else 'PASSED_')+self.role.upper(),'image_id':self.image,
                    'suite_sha256':meta[self.role+'_sha256'],'package_sha256':meta['package_sha256'],
                    'candidate_sha256':hashlib.sha256(content).hexdigest(),'cleanup_exit_code':0,
                    'summary':{'total':len(cases),'passed':len(cases)-int(bad),'failure':int(bad),'error':0,'skipped':0,'cases':cases}}
        def static(code,spec):return {'findings':[],'status':'AWAITING_DYNAMIC_TESTS'}
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            folder=run_ab(meta['spec'],tmp,SyntheticClient('categories',package='final-v2'),Runner('internal'),Runner('reference'),
                kind='final',order_seed=7,revision_seeds=[102,103,104],static_analyzer=static,
                final_context={'package':'final-v2','stage':'synthetic_validation','origin':'synthetic_validation'})
            pair=json.loads((folder/'pair.json').read_bytes());self.assertEqual(pair['status'],'EVALUATED')
            report=ab_report(tmp);self.assertEqual(report['counts']['EVALUATED'],1,report)
            self.assertEqual(report['pairs'][0]['model'],'synthetic-fixture-final-v2')
            self.assertEqual(report['pairs'][0]['branches']['A']['evaluation']['total'],53)

    def test_cross_version_synthetic_binding_is_rejected(self):
        from critic_agent.ab_final import FinalABAdapter,SyntheticClient
        api=get_package_api('final-v2');meta=api.package_manifest('categories');sandbox=get_sandbox_api('final-v2')
        with self.assertRaisesRegex(ValueError,'Synthetic package binding'):
            FinalABAdapter(meta['spec'],SyntheticClient('categories'),sandbox.FinalRunner('categories','internal'),
                sandbox.FinalRunner('categories','reference'),{'package':'final-v2','stage':'synthetic_validation','origin':'synthetic_validation'})

    def test_same_count_wrong_resource_runner_is_rejected_before_any_work(self):
        from critic_agent.ab_final import FinalABAdapter,SyntheticClient
        api=get_package_api('final-v2');sandbox=get_sandbox_api('final-v2');meta=api.package_manifest('courses')
        with self.assertRaises(ValueError):
            FinalABAdapter(meta['spec'],SyntheticClient('courses',package='final-v2'),sandbox.FinalRunner('assets','internal'),
                sandbox.FinalRunner('courses','reference'),{'package':'final-v2','stage':'synthetic_validation','origin':'synthetic_validation'})

    def test_v2_control_materialization_has_no_unhashed_v1_asset_dependency(self):
        with patch('critic_agent.final_controls.package_manifest',side_effect=AssertionError('unbound v1 asset read')):
            controls=control_catalog('categories')
        self.assertEqual(len([c for c in controls if c['expected']=='pass']),2)

    def test_protocol_rejects_equivalent_spec_with_non_registered_bytes(self):
        from critic_agent.ab_protocol import check_protocol
        api=get_package_api('final-v2')
        plan=json.loads((ROOT/'docs/evidence/final-ab-plan-2026-11-23.draft.json').read_bytes());plan['package']='final-v2'
        for item,resource in zip(plan['specifications'],api.RESOURCES):
            meta=api.package_manifest(resource);plan['package_sha256']=meta['package_sha256']
            item.update(spec_path='evaluation/final-v2/specs/'+resource+'.json',spec_sha256=meta['spec_sha256'],
                        internal_suite_sha256=meta['internal_sha256'],reference_suite_sha256=meta['reference_sha256'])
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            folder=Path(tmp);copyfile=folder/'equivalent.json'
            copyfile.write_text(json.dumps(api.package_manifest('categories')['spec'],separators=(',',':')))
            plan['specifications'][0].update(spec_path=copyfile.relative_to(ROOT).as_posix(),spec_sha256=sha(copyfile))
            file=folder/'draft.json';file.write_text(json.dumps(plan));result=check_protocol(file)
        self.assertEqual(result['integrity'],'FAILED',result)

    def test_internal_readiness_suite_is_checked_before_reference_or_model(self):
        from critic_agent.ab import run_ab
        from critic_agent.ab_final import SyntheticClient,reference_runner
        api=get_package_api('final-v2');sandbox=get_sandbox_api('final-v2');meta=api.package_manifest('categories')
        client=SyntheticClient('categories',package='final-v2')
        internal=sandbox.FinalRunner('categories','internal',image='sha256:'+'a'*64)
        reference=reference_runner('final-v2','categories',image='sha256:'+'b'*64)
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp,patch.object(internal,'check_reference',return_value={'status':'READY','image_id':internal.image,'suite_sha256':'0'*64}),patch.object(reference,'check_reference',side_effect=AssertionError('reference must not be reached')):
            folder=run_ab(meta['spec'],tmp,client,internal,reference,kind='final',order_seed=7,revision_seeds=[102,103,104],
                final_context={'package':'final-v2','stage':'synthetic_validation','origin':'synthetic_validation'})
            report=json.loads((folder/'pair.json').read_bytes())
        self.assertEqual(report['status'],'ERROR');self.assertIn('suite',report['reason'].lower())
        self.assertEqual(client.requests,[])

    def test_v2_source_inventory_includes_scaffold_template_reads(self):
        meta=get_package_api('final-v2').package_manifest('categories')
        for file in (ROOT/'resource_templates').glob('*.php'):
            self.assertEqual(meta['source_hashes'].get(file.relative_to(ROOT).as_posix()),sha(file))
