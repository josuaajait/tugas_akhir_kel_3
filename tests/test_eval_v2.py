"""Regressions for F1/F2/F3; original final-v1 stays immutable."""
import json
import re
from pathlib import Path
import subprocess
import tempfile
import unittest

from critic_agent.eval_package_v2 import PACKAGE,RESOURCES,package_manifest,suite_cases
from critic_agent.eval_controls_v2 import control_catalog

ROOT=Path(__file__).resolve().parents[1]

class EvalV2Tests(unittest.TestCase):
    def test_index_expectation_uses_both_seeded_ids_without_unbound_variables(self):
        for role in ('internal','reference'):
            source=(PACKAGE/role/'Suite.php').read_text(encoding='utf-8')
            index_body=source[source.index("if ($kind==='index')"):]
            expression=re.search(r'Assertions::collection\(\$r->getContent\(\),(\[.*?\])\);',index_body).group(1)
            # Execute only the trusted expected-record expression and assertion, never a controller.
            script=r'''<?php
require 'harness/laravel/vendor/autoload.php'; require $argv[1];
(new PHPUnit\TextUI\Configuration\Builder)->build(['probe','--no-configuration']);
set_error_handler(function($level,$message){throw new ErrorException($message);});
$probe=new class {
 function body($role) {return ['name'=>$role==='target'?'one':'two'];}
 function expected($first,$second,$target) { return EXPRESSION; }
};
$raw='{"data":[{"id":11,"name":"one"},{"id":12,"name":"two"}]}';
foreach([11,12] as $target) FinalEvaluation\Assertions::collection($raw,$probe->expected(11,12,$target));
echo 'both seeded records bound correctly';
'''.replace('EXPRESSION',expression)
            with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                file=Path(tmp)/'trusted-index.php';file.write_text(script)
                observed=subprocess.run(['php',str(file),str(PACKAGE/role/'Assertions.php')],cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(observed.returncode,0,observed.stdout+observed.stderr)
                self.assertEqual(observed.stdout,'both seeded records bound correctly')

    def test_original_fingerprint_and_new_counts(self):
        from critic_agent.final_package import package_manifest as old
        self.assertEqual(old('categories')['package_sha256'],'f2b648aeb042f4edcbb46b1b0160c87f93c326d084009cbc6de2f0f121e4a9b7')
        metas=[package_manifest(r) for r in RESOURCES]
        self.assertEqual([m['internal_tests'] for m in metas],[23,19,21,21,29])
        self.assertEqual([m['reference_tests'] for m in metas],[53,57,80,84,127])
        self.assertTrue(all(m['package']=='final-v2' and not m['ready_for_final'] for m in metas))

    def test_second_id_and_short_valid_cases_in_both_roles(self):
        for resource in RESOURCES:
            meta=package_manifest(resource)
            for internal in (False,True):
                cases={c['case_id']:c for c in suite_cases(meta['spec'],meta['profile'],internal)}
                for operation in ('show','update','destroy'):
                    self.assertEqual(cases[operation+'_second']['target_position'],2)
                for field in meta['spec']['fields']:
                    if field['type']=='string' and not any(r.startswith('min:') for r in field['rules']):
                        for verb in ('POST','PUT'):
                            for length in (1,2):
                                case=cases[f'{verb}_short{length}_{field["name"]}']
                                self.assertEqual(len(case['payload'][field['name']]),length)
            self.assertNotEqual(meta['internal_fixtures'],meta['profile']['fixtures'])

    def test_new_fault_controls_have_targets_and_body_error_is_not_environment(self):
        catalogs=[control_catalog(resource) for resource in RESOURCES]
        self.assertEqual(sum(c['expected']=='fail' for cs in catalogs for c in cs),331)
        for catalog in catalogs:
            by_id={c['control_id']:c for c in catalog}
            wrong=by_id['lookup_first_after_exists'];bad_json=by_id['index_invalid_json']
            self.assertEqual(set(wrong['target_case_ids']),{'show_second','update_second','destroy_second'})
            self.assertEqual(wrong['failure_evidence']['update_second'],{'phase':'state','http_status':200})
            self.assertEqual(bad_json['expected_internal'],'fail')
            self.assertEqual(set(bad_json['target_case_ids']),{'index','empty','sequence'})
            self.assertTrue(all(c['internal_target_case_ids'] for c in catalog if c['control_id'].startswith('reject_short_')))

    def test_raw_json_is_asserted_before_laravel_decoders_can_rethrow_response_exception(self):
        for role in ('internal','reference'):
            source=(PACKAGE/role/'Suite.php').read_text(encoding='utf-8')
            start=source.index('$r->assertStatus($post ? 201 : 200);')
            fragments=[(source[start:source.index('$expected=',start)],201,True),
                       (source[start:source.index('$expected=',start)],200,False)]
            start=source.index('$r->assertUnprocessable();')
            fragments.append((source[start:source.index("$this->phase='state';",start)],422,True))
            if role=='reference':
                start=source.index("$r=$this->requestCase('POST',null,$new)->assertCreated();")+len("$r=$this->requestCase('POST',null,$new)->assertCreated();")
                fragments.append((source[start:source.index('Assertions::record($r->getContent(),$id,$new);',start)],201,True))
            for fragment,status,post in fragments:
                script=r'''<?php
require 'harness/laravel/vendor/autoload.php'; require $argv[1];
(new PHPUnit\TextUI\Configuration\Builder)->build(['probe','--no-configuration']);
class_alias(FinalEvaluation\Assertions::class,'Assertions');
$base=new Illuminate\Http\Response('not-json',STATUS,['Content-Type'=>'application/json']);
$base->withException(new Illuminate\Http\Exceptions\HttpResponseException($base));
$r=Illuminate\Testing\TestResponse::fromBaseResponse($base);
$probe=new class extends PHPUnit\Framework\Assert {
 public $phase; public function check($r,$post,$case) { FRAGMENT }
};
try { $probe->check($r,POST,['field'=>'name']); exit(8); }
catch(PHPUnit\Framework\AssertionFailedError $e) { echo 'candidate contract failure'; }
'''.replace('STATUS',str(status)).replace('FRAGMENT',fragment).replace('POST','true' if post else 'false')
                with self.subTest(role=role,status=status),tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                    file=Path(tmp)/'trusted-response.php';file.write_text(script)
                    result=subprocess.run(['php',str(file),str(PACKAGE/role/'Assertions.php')],cwd=ROOT,capture_output=True,text=True,timeout=30)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    self.assertEqual(result.stdout,'candidate contract failure')

    def test_malformed_response_is_phpunit_assertion_failure(self):
        script=r'''<?php
require 'harness/laravel/vendor/autoload.php'; require $argv[1];
(new PHPUnit\TextUI\Configuration\Builder)->build(['probe','--no-configuration']);
foreach(['not-json','{',''] as $raw) {
 try { FinalEvaluation\Assertions::object($raw); exit(7); }
 catch(PHPUnit\Framework\AssertionFailedError $e) {}
}
echo 'three contract failures';
'''
        for role in ('internal','reference'):
            with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                file=Path(tmp)/'trusted.php';file.write_text(script)
                observed=subprocess.run(['php',str(file),str(PACKAGE/role/'Assertions.php')],cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(observed.returncode,0,observed.stdout+observed.stderr)
                self.assertEqual(observed.stdout,'three contract failures')
