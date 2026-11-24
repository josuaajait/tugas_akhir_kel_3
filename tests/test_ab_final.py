import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from critic_agent.ab import run_ab
from critic_agent.ab_final import SyntheticClient, FinalReference, run_synthetic_pair
from critic_agent.final_package import ROOT, package_manifest, suite_cases, test_id
from critic_agent.feedback import build_feedback

META=package_manifest('categories')
INTERNAL='sha256:'+'a'*64
REFERENCE='sha256:'+'b'*64


def static_ok(code,spec):
    return {'findings':[], 'status':'AWAITING_DYNAMIC_TESTS'}


class BoundRunner:
    def __init__(self,role='internal',*,error=False):
        self.meta=copy.deepcopy(META);self.role=role;self.resource='categories'
        self.image=INTERNAL if role=='internal' else REFERENCE
        self.candidate_tests=META[role+'_tests'];self.output_root=ROOT/'work'
        self.calls=[];self.error=error
    def check_reference(self):
        return {'status':'READY','image_id':self.image,'suite_sha256':META[self.role+'_sha256'],
                'package_sha256':META['package_sha256']}
    def check_candidate(self,path):
        code=Path(path).read_bytes();self.calls.append(code)
        if self.error:return {'status':'ERROR','reason':'fixture_environment_failure'}
        if b'BROKEN_SYNTAX' in code and self.role=='reference':
            return {'status':'UNLOADABLE_CODE','reason':'invalid_syntax','executed':False,'image_id':self.image}
        bad=b'202); // store response' in code
        cases=[test_id(self.role,c['case_id'])|{'outcome':'failure' if bad and c['case_id']=='store' else 'passed',
                   'evidence':'FINAL_ASSERTION:store:status:HTTP202 Expected201 got202' if bad and c['case_id']=='store' else ''}
               for c in suite_cases(META['spec'],META['profile'],self.role=='internal')]
        return {'status':('FAILED_' if bad else 'PASSED_')+('INTERNAL' if self.role=='internal' else 'REFERENCE'),
                'image_id':self.image,'cleanup_exit_code':0,'exit_code':int(bad),
                'package_sha256':META['package_sha256'],'suite_sha256':META[self.role+'_sha256'],
                'candidate_sha256':hashlib.sha256(code).hexdigest(),
                'summary':{'total':len(cases),'passed':len(cases)-int(bad),'failure':int(bad),'error':0,'skipped':0,'cases':cases}}


def make_pair(root,scenario='repair',*,reference_error=False,order_seed=7):
    client=SyntheticClient('categories',scenario=scenario,seed=101)
    internal,reference=BoundRunner(),BoundRunner('reference',error=reference_error)
    path=run_ab(META['spec'],root,client,internal,reference,kind='final',order_seed=order_seed,
                revision_seeds=[102,103,104],static_analyzer=static_ok,
                final_context={'stage':'synthetic_validation','origin':'synthetic_validation'})
    return path,client,internal,reference


class FinalAblationTests(unittest.TestCase):
    def test_preflight_output_limit_is_archived_as_environment_error(self):
        from critic_agent.process import OutputLimitError
        def execute(args,**kwargs):
            if 'run' in args:raise OutputLimitError(b'bounded stdout',b'bounded stderr')
            return subprocess.CompletedProcess(args,0,b'',b'')
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            runner=FinalReference('categories','reference',image=REFERENCE,output_root=Path(tmp),execute=execute)
            runner._readiness={'status':'READY','image_id':REFERENCE,'run_directory':tmp}
            code=Path(tmp)/'input.php';code.write_text('<?php // fixture')
            result=runner.check_candidate(code)
            self.assertEqual(result['status'],'ERROR');self.assertEqual(result['reason'],'output_limit')
            self.assertEqual((Path(result['run_directory'])/'stdout.log').read_bytes(),b'bounded stdout')

    def test_interruption_preserves_completed_arm_and_finalizes_active_loop(self):
        class Interrupted(SyntheticClient):
            def generate(self,prompt):
                if '"message": "Keluaran ini belum lolos pemeriksaan.' in prompt:raise KeyboardInterrupt()
                return super().generate(prompt)
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            with self.assertRaises(KeyboardInterrupt):
                run_ab(META['spec'],Path(tmp),Interrupted('categories'),BoundRunner(),BoundRunner('reference'),
                       kind='final',order_seed=7,revision_seeds=[102],static_analyzer=static_ok,
                       final_context={'stage':'synthetic_validation','origin':'synthetic_validation'})
            path=next(Path(tmp).glob('ab_*/pair.json'));report=json.loads(path.read_bytes())
            self.assertEqual(report['status'],'ERROR');self.assertEqual(report['n_ab'],0)
            self.assertEqual(report['branches']['A']['status'],'LOLOS')
            b=report['branches']['B'];self.assertEqual(b['status'],'ERROR')
            self.assertEqual(json.loads((path.parent/b['run_path']/'run_manifest.json').read_bytes())['status'],'ERROR')

    def test_shared_initial_fairness_generic_isolation_and_artifacts(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            folder,client,internal,reference=make_pair(Path(tmp))
            report=json.loads((folder/'pair.json').read_bytes())
            self.assertEqual(report['status'],'EVALUATED');self.assertEqual(report['n_ab'],1)
            self.assertEqual(report['origin'],'synthetic_validation');self.assertEqual(report['qwen_calls'],0)
            self.assertEqual(report['package_sha256'],META['package_sha256'])
            a,b=(report['branches'][key] for key in ('A','B'))
            self.assertEqual(a['status'],'LOLOS');self.assertEqual(b['reason'],'identical_code')
            for branch in (a,b):
                run=folder/branch['run_path']
                history=json.loads((run/'history.json').read_bytes())
                self.assertEqual(history['attempts'][0]['code_sha256'],report['initial_code_sha256'])
                self.assertEqual(history['attempts'][1]['model_request']['options']['seed'],102)
            bprompt=(folder/b['run_path']/'attempts/0/feedback.json').read_text()
            self.assertIn('"message"',bprompt);self.assertNotIn('findings',bprompt)
            self.assertEqual(len(reference.calls),3)
            self.assertIn('artifacts',report)
            for relative,digest in report['artifacts'].items():
                self.assertEqual(hashlib.sha256((folder/relative).read_bytes()).hexdigest(),digest)
            for request in client.requests:
                self.assertNotIn('FinalReferenceTest',request['prompt']);self.assertNotIn('Stationery',request['prompt'])

    def test_format_failure_zero_and_already_valid_zero_revisions(self):
        for scenario in ('format_fail','already_valid'):
            with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                folder,client,_,_=make_pair(Path(tmp),scenario)
                report=json.loads((folder/'pair.json').read_bytes())
                self.assertEqual(report['n_ab'],1)
                a=report['branches']['A']
                e=json.loads((folder/a['evaluation']['report_path']).read_bytes())
                self.assertEqual(e['initial']['passed'],0 if scenario=='format_fail' else META['reference_tests'])
                if scenario=='already_valid':
                    self.assertEqual(a['revision_count'],0);self.assertEqual(len(client.requests),1)

    def test_reference_error_preserves_both_loops_but_no_complete_pair(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            folder,_,_,_=make_pair(Path(tmp),reference_error=True)
            r=json.loads((folder/'pair.json').read_bytes())
            self.assertEqual(r['status'],'ERROR');self.assertEqual(r['n_ab'],0);self.assertIsNone(r['delta_final_pp'])
            self.assertTrue(all((folder/b['run_path']/'history.json').exists() for b in r['branches'].values()))

    def test_final_feedback_maps_dataset_to_method(self):
        for cid,method in [('store','store'),('update','update'),('missing_GET','show'),
                           ('POST_missing_name','store'),('PUT_missing_name','update')]:
            raw={'summary':{'cases':[test_id('internal',cid)|{'outcome':'failure','evidence':'failed'}]}}
            self.assertEqual(build_feedback([],raw,0)['findings'][0]['location'],{'method':method})

    def test_syntax_preflight_is_docker_only_and_cleanup_failure_not_zero(self):
        for cleanup in (0,1):
            calls=[]
            def execute(args,**kwargs):
                calls.append(args)
                if 'run' in args:
                    return subprocess.CompletedProcess(args,255,b'Errors parsing /input/controller.php\n',b'parse error')
                return subprocess.CompletedProcess(args,cleanup,b'',b'')
            with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                runner=FinalReference('categories','reference',image=REFERENCE,output_root=Path(tmp),execute=execute)
                runner._readiness={'status':'READY','image_id':REFERENCE,'run_directory':tmp}
                code=Path(tmp)/'syntax.php';code.write_text('<?php BROKEN_SYNTAX')
                raw=runner.check_candidate(code)
                self.assertEqual(raw['status'],'UNLOADABLE_CODE' if cleanup==0 else 'ERROR')
                command=next(c for c in calls if 'run' in c)
                self.assertIn('--network=none',command);self.assertIn('-l',command)
                self.assertEqual(sum(arg=='--mount' for arg in command),1)

    def test_packet_fingerprint_preserved(self):
        self.assertEqual(package_manifest('categories')['package_sha256'],
                         'f2b648aeb042f4edcbb46b1b0160c87f93c326d084009cbc6de2f0f121e4a9b7')
