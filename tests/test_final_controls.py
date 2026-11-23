import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from critic_agent.final_package import PACKAGE, RESOURCES, package_manifest, suite_cases, traceability
from critic_agent.final_controls import control_catalog, materialize_controls

ROOT = Path(__file__).resolve().parents[1]


class FinalControlTests(unittest.TestCase):
    def test_wrong_update_target_matches_observed_identity_assertion_phase(self):
        control=next(c for c in control_catalog('categories') if c['control_id']=='update_wrong_target')
        self.assertEqual(control['failure_evidence']['update'],{'phase':'state','http_status':200})

    def test_targets_have_explicit_evidence_and_internal_mappings(self):
        for resource in RESOURCES:
            controls=control_catalog(resource)
            self.assertIn('index_cross_field',{c['control_id'] for c in controls}) if resource=='categories' else None
            for c in controls:
                if c['expected']=='fail':
                    self.assertEqual(set(c['target_case_ids']),set(c['failure_evidence']))
                    self.assertTrue(c['internal_target_case_ids'] or c['expected_internal']=='pass')
                    self.assertTrue(all(e['phase'] and e['http_status']!=500 for e in c['failure_evidence'].values()))

    @unittest.skipUnless(shutil.which('php'),'PHP required')
    def test_actual_phpunit_discovery_and_no_reference_logic_in_internal(self):
        from critic_agent.final_sandbox import render_final
        for role,cls in [('internal','FinalInternalTest'),('reference','FinalReferenceTest')]:
            files=render_final('categories',role)
            path='final/'+cls+'.php'
            self.assertIn(path,files)
            if role=='internal':
                self.assertNotIn('function sequence',files[path])
                self.assertNotIn("$kind==='empty'",files[path])
            with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                folder=Path(tmp)
                for name in (path,'final/Assertions.php','final/profile.json'):
                    dest=folder/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(files[name])
                code="require $argv[1]; $c=(new PHPUnit\\Runner\\TestSuiteLoader)->load($argv[2]); echo $c->getShortName();"
                p=subprocess.run(['php','-r',code,str(ROOT/'harness/laravel/vendor/autoload.php'),str(folder/path)],capture_output=True,text=True,timeout=30)
                self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertEqual(p.stdout,cls)

    def test_controls_single_mutations_and_every_vector_bound(self):
        for resource in RESOURCES:
            catalog = control_catalog(resource)
            self.assertEqual([c['control_id'] for c in catalog if c['expected']=='pass'], ['eloquent','explicit'])
            mutants = [c for c in catalog if c['expected']=='fail']
            self.assertTrue(all(c['diff'] and c['target_case_ids'] for c in mutants))
            rows = traceability(resource)
            covered = {target for c in mutants for target in c['target_case_ids']}
            self.assertEqual(covered, {r['case_id'] for r in rows})
            self.assertTrue(all(c['source'] != catalog[0]['source'] for c in mutants))
            with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                saved = materialize_controls(resource, Path(tmp))
                self.assertEqual(len(saved['controls']), len(catalog))
                self.assertTrue(all((Path(tmp)/c['path']).is_file() for c in saved['controls']))
                with self.assertRaises(FileExistsError):
                    materialize_controls(resource, Path(tmp))

    @unittest.skipUnless(shutil.which('php'), 'PHP required')
    def test_trusted_assertions_preserve_original_json_shapes(self):
        for role in ('internal','reference'):
            source = PACKAGE/role/'Assertions.php'
            script = r'''<?php
require 'harness/laravel/vendor/autoload.php';
require $argv[1];
(new PHPUnit\TextUI\Configuration\Builder)->build(['probe','--no-configuration']);
$good='{"data":[{"id":11,"name":"one"},{"id":12,"name":"two"}]}';
$expected=[11=>['name'=>'one'],12=>['name'=>'two']];
$valid=[$good,'{"data":[{"id":12,"name":"two","extra":1},{"id":11,"name":"one"}]}'];
$bad=['{"data":{"0":{"id":11,"name":"one"},"1":{"id":12,"name":"two"}}}',
 '{"data":[{"id":11,"name":"two"},{"id":12,"name":"one"}]}',
 '{"data":[{"id":11,"name":"one"},{"id":11,"name":"one"}]}',
 '{"data":[{"id":"11","name":"one"},{"id":12,"name":"two"}]}',
 '{"data":[{"id":11},{"id":12,"name":"two"}]}',
 '{"data":[{"id":13,"name":"one"},{"id":12,"name":"two"}]}',
 '{"data":[[11,"one"],[12,"two"]]}','[]'];
foreach($valid as $raw) FinalEvaluation\Assertions::collection($raw,$expected);
foreach($bad as $raw) {
 try {FinalEvaluation\Assertions::collection($raw,$expected);exit(4);}
 catch(PHPUnit\Framework\AssertionFailedError $e) {}
}
FinalEvaluation\Assertions::record('{"data":{"id":11,"name":"one"}}',11,['name'=>'one']);
try {FinalEvaluation\Assertions::object('[]');exit(5);} catch(PHPUnit\Framework\AssertionFailedError $e) {}
echo 'accepted 2 valid; rejected 8 invalid';
'''
            with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                path = Path(tmp)/'probe.php'
                path.write_text(script)
                result = subprocess.run(['php', str(path), str(source)], cwd=ROOT, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    @unittest.skipUnless(shutil.which('php'), 'PHP required')
    def test_all_authored_php_lints_and_provider_counts(self):
        for resource in RESOURCES:
            meta = package_manifest(resource)
            for control in control_catalog(resource):
                result=subprocess.run(['php','-n','-l'],input=control['source'],text=True,capture_output=True,timeout=15)
                self.assertEqual(result.returncode,0,control['control_id']+result.stdout+result.stderr)
            for role in ('internal','reference'):
                cases=suite_cases(meta['spec'],meta['profile'],role=='internal')
                self.assertEqual(len(cases),meta[role+'_tests'])
                script="<?php require 'harness/laravel/vendor/autoload.php'; require $argv[1]; echo count(FinalEvaluation\\"+('FinalInternalTest' if role=='internal' else 'FinalReferenceTest')+"::cases());"
                with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                    folder=Path(tmp)
                    (folder/'profile.json').write_text(json.dumps({'spec':meta['spec'],'fixtures':meta['internal_fixtures'] if role=='internal' else meta['profile']['fixtures'],'cases':cases}))
                    for name in ('Assertions.php','Suite.php'):
                        shutil.copyfile(PACKAGE/role/name,folder/name)
                    result=subprocess.run(['php','-r',script.removeprefix('<?php '),str(folder/'Suite.php')],cwd=ROOT,text=True,capture_output=True,timeout=30)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    self.assertEqual(int(result.stdout),len(cases))
