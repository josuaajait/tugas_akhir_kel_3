import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from critic_agent.final_package import package_manifest
from critic_agent.final_sandbox import FinalRunner, build_final, render_final, LABEL_PACKAGE, LABEL_ROLE, LABEL_SUITE

ROOT=Path(__file__).resolve().parents[1]
IMAGE='sha256:'+'a'*64

def build_reply(args,resource='rooms',role='reference',wrong_runtime=False):
    from critic_agent.final_sandbox import LABEL_SPEC, runtime_expectations
    if 'inspect' in args:
        if args[-1].startswith('critic-final-v1-'):
            meta=package_manifest(resource)
            return {'Id':'sha256:'+'b'*64,'Config':{'Entrypoint':['php','/opt/critic-final-entrypoint.php'],'Labels':{LABEL_PACKAGE:meta['package_sha256'],LABEL_ROLE:role,LABEL_SUITE:meta[role+'_sha256'],LABEL_SPEC:meta['spec_sha256']}}}
        return {'Id':IMAGE,'Config':{'Entrypoint':['php','/opt/critic-entrypoint.php'],'Labels':{}}}
    if 'run' in args:
        data=runtime_expectations()|{'php_version':'8.3.30'}
        if wrong_runtime:data['packages']['laravel/framework']='0.0.0'
        return data
    return None


class FinalSandboxTests(unittest.TestCase):
    def test_candidate_reuses_verified_readiness_with_pinned_image(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            runner=FinalRunner('rooms','internal',output_root=Path(tmp))
            ready={'status':'READY','image_id':IMAGE,'run_directory':tmp}
            candidate={'status':'PASSED_INTERNAL','image_id':IMAGE,'run_directory':tmp}
            path=Path(tmp)/'candidate.php';path.write_text('<?php // trusted fixture')
            with patch.object(runner,'_run',side_effect=[ready,candidate.copy(),candidate.copy()]) as run:
                runner.check_candidate(path);runner.check_candidate(path)
                self.assertEqual(run.call_count,3)
                self.assertEqual(runner.image,IMAGE)

    def test_internal_context_has_no_reference_assets(self):
        files=render_final('assets','internal')
        self.assertFalse(any('reference' in p for p in files))
        self.assertNotIn('AS-101','\n'.join(files.values()))
        self.assertNotIn('boundary_max',files['final/profile.json'])
        self.assertIn('RUN rm -rf',files['Dockerfile'])
        self.assertIn('network',str(FinalRunner('assets','internal').command('owned',ROOT/'work')))
        self.assertEqual(FinalRunner('assets','internal').candidate_tests,14)

    def test_build_pins_base_and_cleans_owned_tag(self):
        calls=[]
        def execute(args,**kw):
            calls.append(args)
            data=build_reply(args)
            return subprocess.CompletedProcess(args,0,json.dumps(data).encode() if data else b'',b'')
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            folder=build_final('rooms','reference',Path(tmp),execute=execute,timeout=45)
            report=json.loads((folder/'build_result.json').read_text())
            self.assertEqual(report['status'],'BUILT')
            self.assertEqual(report['image_id'],'sha256:'+'b'*64)
            pin=next(c for c in calls if 'tag' in c)
            self.assertEqual(pin[-2],IMAGE)
            self.assertIn('BASE_IMAGE='+pin[-1],next(c for c in calls if 'build' in c))
            self.assertIn(['docker','image','rm',pin[-1]],calls)

    def test_build_rejects_evaluator_base_and_preserves_tag_timeout(self):
        for bad in (True,False):
            calls=[]
            def execute(args,**kw):
                calls.append(args)
                if 'inspect' in args:
                    return subprocess.CompletedProcess(args,0,json.dumps({'Id':IMAGE,'Config':{'Entrypoint':['php','/opt/critic-entrypoint.php'],'Labels':{'org.critic.reference-suite-sha256':'bad'} if bad else {}}}).encode(),b'')
                if 'run' in args:return subprocess.CompletedProcess(args,0,json.dumps(build_reply(args)).encode(),b'')
                if 'tag' in args:raise subprocess.TimeoutExpired(args,45)
                return subprocess.CompletedProcess(args,0,b'',b'')
            with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                folder=build_final('rooms','internal',Path(tmp),execute=execute,timeout=45)
                report=json.loads((folder/'build_result.json').read_text())
                self.assertEqual(report['status'],'ERROR')
                self.assertFalse(any('build' in c for c in calls))
                if not bad:
                    self.assertEqual(report['reason'],'timeout')
                    self.assertTrue(any('rm' in c for c in calls))

    def test_wrong_runtime_is_rejected_before_build(self):
        calls=[]
        def execute(args,**kw):
            calls.append(args);data=build_reply(args,wrong_runtime=True)
            return subprocess.CompletedProcess(args,0,json.dumps(data).encode() if data else b'',b'')
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            report=json.loads((build_final('rooms','reference',Path(tmp),execute=execute)/'build_result.json').read_text())
        self.assertEqual(report['status'],'ERROR')
        self.assertIn('runtime',report['detail'].lower())
        self.assertFalse(any('build' in c for c in calls))

    def test_runner_rejects_wrong_labels_before_execution(self):
        def execute(args,**kw):
            return subprocess.CompletedProcess(args,0,json.dumps({'Id':IMAGE,'Config':{'Entrypoint':['php','/opt/critic-final-entrypoint.php'],'Labels':{LABEL_PACKAGE:'wrong',LABEL_ROLE:'internal',LABEL_SUITE:'wrong'}}}).encode(),b'')
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            runner=FinalRunner('rooms','internal',output_root=Path(tmp),execute=execute)
            with patch('critic_agent.sandbox.DockerRunner._run') as run:
                result=runner.check_reference()
            self.assertEqual(result['status'],'ERROR')
            run.assert_not_called()

    def test_cleanup_failure_and_wrong_case_ids_are_errors(self):
        meta=package_manifest('rooms')
        def execute(args,**kw):
            labels={LABEL_PACKAGE:meta['package_sha256'],LABEL_ROLE:'internal',LABEL_SUITE:meta['internal_sha256'],'org.critic.final-spec-sha256':meta['spec_sha256']}
            return subprocess.CompletedProcess(args,0,json.dumps({'Id':IMAGE,'Config':{'Entrypoint':['php','/opt/critic-final-entrypoint.php'],'Labels':labels}}).encode(),b'')
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            runner=FinalRunner('rooms','internal',output_root=Path(tmp),execute=execute)
            for cleanup in (0,1):
                folder=Path(tmp)/str(cleanup);folder.mkdir()
                raw={'status':'FAILED_INTERNAL','image_id':IMAGE,'run_directory':str(folder),'cleanup_exit_code':cleanup,'summary':{'total':12,'passed':11,'failure':1,'error':0,'skipped':0,'cases':[]}}
                with patch('critic_agent.sandbox.DockerRunner._run',return_value=raw):
                    result=runner._run(ROOT/'examples/NoOpBookController.php')
                self.assertEqual(result['status'],'ERROR')
