import copy
import hashlib
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from critic_agent.final_controls import control_catalog
from critic_agent.final_package import package_manifest, suite_cases, test_id
from critic_agent.final_validation import validate_final, assess_observation

ROOT=Path(__file__).resolve().parents[1]


def observation(resource,role,control,meta=None):
    meta=package_manifest(resource) if meta is None else meta
    cases=[]
    planned=suite_cases(meta['spec'],meta['profile'],role=='internal')
    mapped={c['case_id'] for c in planned}.intersection(control['target_case_ids'])
    for case in planned:
        failed=(control['expected']=='fail' and (role=='reference' and case['case_id'] in control['target_case_ids']
                or role=='internal' and control['expected_internal']=='fail' and
                (case['case_id'] in mapped or not mapped and case['case_id']=='index')))
        evidence=control.get('failure_evidence',{}).get(case['case_id'],{'phase':'status','http_status':200})
        marker='FINAL_ASSERTION:'+case['case_id']+':'+evidence['phase']+':HTTP'+str(evidence['http_status'])+' '
        cases.append(test_id(role,case['case_id'])|{'outcome':'failure' if failed else 'passed','evidence':marker+'Expected contract response; got incorrect status/value' if failed else ''})
    fail=sum(c['outcome']=='failure' for c in cases)
    return {'status':('FAILED_' if fail else 'PASSED_')+('INTERNAL' if role=='internal' else 'REFERENCE'),
            'package_sha256':meta['package_sha256'],'suite_sha256':meta[role+'_sha256'],
            'candidate_sha256':control['sha256'],'image_id':'sha256:'+('a' if role=='internal' else 'b')*64,
            'cleanup_exit_code':0,'summary':{'total':len(cases),'passed':len(cases)-fail,'failure':fail,'error':0,'skipped':0,'cases':cases}}


class FinalValidationTests(unittest.TestCase):
    def test_invalid_timeouts_are_rejected_before_work(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            for value in (float('nan'),float('inf'),0,-1):
                with self.assertRaises(ValueError):
                    validate_final(Path(tmp),resources=['categories'],local_only=True,timeout=value)

    def test_interruption_cannot_finalize_unexecuted_plan_as_validated(self):
        class Runner:
            def __init__(self,*args,**kwargs):pass
            def check_reference(self):raise KeyboardInterrupt()
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp,patch('critic_agent.final_validation.local_checks',return_value={'status':'LOCAL_VALIDATED'}):
            with self.assertRaises(KeyboardInterrupt):
                validate_final(Path(tmp),resources=['categories'],runner_factory=Runner)
            report=json.loads(next(Path(tmp).glob('*/validation.json')).read_text())
            self.assertEqual(report['status'],'ERROR')
            self.assertGreater(report['unexecuted'],0)

    def test_targeted_failure_required_and_partial_cleanup_errors_unknown(self):
        meta=package_manifest('categories');control=control_catalog('categories')[2]
        raw=observation('categories','reference',control)
        self.assertEqual(assess_observation(meta,'reference',control,raw,raw['image_id'])['status'],'PASS')
        for change in ('wrong_target','wrong_phase','unexpected_500','cleanup','partial','image','hash','unknown_outcome'):
            bad=copy.deepcopy(raw)
            if change=='wrong_target':
                for c in bad['summary']['cases']:c['outcome']='passed';c['evidence']=''
                bad['summary']['cases'][1]['outcome']='failure'
            elif change in ('wrong_phase','unexpected_500'):
                for c in bad['summary']['cases']:
                    if c['outcome']=='failure':c['evidence']='unrelated exception' if change=='wrong_phase' else 'FINAL_ASSERTION:index:body:HTTP500 SQL exception'
            elif change=='unknown_outcome':
                bad['summary']['cases'][1]['outcome']='unknown';bad['summary']['passed']-=1
            elif change=='cleanup':bad['cleanup_exit_code']=1
            elif change=='partial':bad['summary']['cases'].pop()
            elif change=='image':bad['image_id']='sha256:'+'c'*64
            else:bad['candidate_sha256']='wrong'
            self.assertNotEqual(assess_observation(meta,'reference',control,bad,raw['image_id'])['status'],'PASS',change)

    def test_local_mode_never_claims_functional_or_calls_model_or_docker(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp, patch('critic_agent.final_validation.local_checks',return_value={'status':'LOCAL_VALIDATED'}), patch('critic_agent.ollama.OllamaClient') as model, patch('critic_agent.final_validation.FinalRunner') as runner:
            folder=validate_final(Path(tmp),resources=['categories'],local_only=True)
            result=json.loads((folder/'validation.json').read_text())
            self.assertEqual(result['status'],'LOCAL_VALIDATED')
            self.assertEqual(result['functional_validation'],'NOT_RUN')
            self.assertFalse(result['ready_for_final']);model.assert_not_called();runner.assert_not_called()
            self.assertTrue((folder/'categories/traceability.json').exists())
            meta=package_manifest('categories')
            self.assertEqual(hashlib.sha256((folder/'sources/evaluation/final-v1/specs/categories.json').read_bytes()).hexdigest(),meta['spec_sha256'])
            self.assertEqual(result['planned'],2*(result['resources'][0]['planned_controls']+3))
            self.assertEqual(result['unexecuted'],result['planned'])

    def test_materialization_failure_is_archived_and_plans_reconcile(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp,patch('critic_agent.final_validation.materialize_controls',side_effect=OSError('disk denied')):
            folder=validate_final(Path(tmp),resources=['categories'],local_only=True)
            report=json.loads((folder/'validation.json').read_text())
            self.assertEqual(report['status'],'ERROR')
            self.assertEqual(report['executed'],0)
            self.assertEqual(report['unexecuted'],report['planned'])
            self.assertIn('disk denied',report['resources'][0]['reason'])

    def test_full_plan_and_repeats_and_no_false_success_on_instability(self):
        for unstable in (False,True):
            class Runner:
                def __init__(self,resource,role,**kw):
                    self.resource,self.role=resource,role
                    self.image='sha256:'+('a' if role=='internal' else 'b')*64
                    self.counts={}
                    self.meta=package_manifest(resource)
                    self.catalog={c['control_id']:c for c in control_catalog(resource)}
                def check_reference(self):return {'status':'READY','image_id':self.image}
                def check_candidate(self,path):
                    cid=Path(path).stem
                    control=self.catalog[cid]
                    self.counts[cid]=self.counts.get(cid,0)+1
                    raw=observation(self.resource,self.role,control,self.meta)
                    if unstable and cid=='eloquent' and self.counts[cid]>1:raw['status']='ERROR'
                    return raw
            with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp, patch('critic_agent.final_validation.local_checks',return_value={'status':'LOCAL_VALIDATED'}):
                folder=validate_final(Path(tmp),resources=['categories'],runner_factory=Runner)
                result=json.loads((folder/'validation.json').read_text())
                self.assertEqual(result['status'],'ERROR' if unstable else 'VALIDATED')
                self.assertFalse(result['ready_for_final'])
                records=result['resources'][0]['observations']
                self.assertEqual(sum(r['control_id']=='eloquent' for r in records),4)
                self.assertTrue(all(r['repeat_consistent'] for r in records if r['repetition']==2) if not unstable else True)

    def test_cli_explicit_package_and_no_model_options(self):
        from critic_agent.cli import main
        with redirect_stdout(io.StringIO()) as out,self.assertRaises(SystemExit) as exc:
            main(['final-validate','--help'])
        self.assertEqual(exc.exception.code,0)
        self.assertIn('--package',out.getvalue());self.assertNotIn('--model',out.getvalue())
