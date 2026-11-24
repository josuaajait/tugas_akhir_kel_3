import json
from pathlib import Path
import shutil
import tempfile
import unittest

from critic_agent.ab_report import ab_report, summarize_spec, macro_summary
from critic_agent.ab_archive import ROOT,sha
from test_ab_final import make_pair


class ABReportTests(unittest.TestCase):
    def test_error_before_pair_creation_is_not_reported_as_unstarted(self):
        plan=ROOT/'docs/evidence/final-ab-plan-2026-11-23.draft.json'
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            root=Path(tmp);claim=root/'claim';claim.mkdir()
            (claim/'execution.json').write_text(json.dumps({'status':'ERROR','pair_slot':'P01',
                'protocol_sha256':sha(plan),'reason':'fixture_preflight_failure'}))
            result=ab_report(root,plan=plan)
            self.assertEqual(result['planned_slots'][0]['status'],'ERROR')
            self.assertEqual(len(result['execution_records']),1)

    def test_recomputes_real_controlled_pair_and_shared_initial_cost_once(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            root=Path(tmp);folder,_,_,_=make_pair(root)
            result=ab_report(root)
            self.assertEqual(result['counts']['EVALUATED'],1)
            group=result['cohorts'][0];spec=group['specifications'][0]
            self.assertEqual(spec['n_ab'],1)
            self.assertEqual(spec['conditions']['A']['n_valid'],1)
            self.assertEqual(spec['conditions']['A']['repair']['denominator'],1)
            self.assertEqual(spec['conditions']['A']['repair']['numerator'],1)
            self.assertEqual(spec['conditions']['B']['identical_among_revised']['numerator'],1)
            self.assertEqual(spec['cost']['logical_generation_calls'],3)
            self.assertEqual(spec['cost']['qwen_calls'],0)
            self.assertEqual(spec['initial_codes']['unique'],1)

    def test_tampered_score_or_candidate_is_invalid_not_a_success(self):
        for change in ('score','code'):
            with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
                root=Path(tmp);folder,_,_,_=make_pair(root)
                r=json.loads((folder/'pair.json').read_bytes())
                if change=='score':
                    r['branches']['A']['evaluation']['final_pass_rate']=0
                    (folder/'pair.json').write_text(json.dumps(r))
                else:(folder/r['branches']['A']['run_path']/'final_controller.php').write_text('<?php changed')
                report=ab_report(root)
                self.assertEqual(report['counts']['INVALID'],1,change)
                self.assertFalse(report['cohorts'])

    def test_duplicates_and_missing_planned_slots_remain_visible(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            root=Path(tmp);folder,_,_,_=make_pair(root)
            shutil.copytree(folder,root/'copied_pair')
            result=ab_report(root,plan=ROOT/'docs/evidence/final-ab-plan-2026-11-23.draft.json')
            self.assertEqual(result['counts']['AMBIGUOUS'],2)
            self.assertEqual(len(result['planned_slots']),20)
            self.assertTrue(all(r['status']=='NOT_STARTED' for r in result['planned_slots']))
            self.assertEqual(result['plan_summary']['n_ab'],0)

    def test_branch_error_and_zero_denominators_not_silently_lost(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            folder,_,_,_=make_pair(Path(tmp),reference_error=True)
            result=ab_report(Path(tmp));spec=result['cohorts'][0]['specifications'][0]
            self.assertEqual(spec['n_ab'],0)
            self.assertEqual(spec['conditions']['A']['n_valid'],1)
            self.assertEqual(spec['conditions']['A']['n_pair'],0)
            self.assertIsNone(spec['conditions']['A']['repair']['percent'])
            self.assertGreater(spec['conditions']['A']['evaluator_errors'],0)

    def test_macro_uses_equal_spec_weights_and_origins_separate(self):
        macro=macro_summary([{'n_ab':10,'mean_delta_final_pp':10,'conditions':{}},
                             {'n_ab':1,'mean_delta_final_pp':-30,'conditions':{}}])
        self.assertEqual(macro['mean_delta_final_pp'],-10)
        self.assertEqual(macro['specifications_with_ab'],2)
        self.assertIsNone(macro_summary([])['mean_delta_final_pp'])

    def test_different_scenarios_separate_and_error_does_not_split_a_spec(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
            root=Path(tmp)
            make_pair(root)
            make_pair(root,reference_error=True)
            make_pair(root,scenario='already_valid')
            result=ab_report(root)
            self.assertEqual(len(result['cohorts']),2)
            repair=next(g for g in result['cohorts'] if g['scenario']=='repair')
            self.assertEqual(len(repair['specifications']),1)
            self.assertEqual(repair['specifications'][0]['conditions']['A']['n_valid'],2)

    def test_cli_report_missing_root_with_plan_has_all_rows(self):
        from critic_agent.cli import main
        from contextlib import redirect_stdout
        import io
        with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp,redirect_stdout(io.StringIO()) as out:
            code=main(['ab-report',str(Path(tmp)/'not_started'),'--plan',str(ROOT/'docs/evidence/final-ab-plan-2026-11-23.draft.json'),'--json'])
        self.assertEqual(code,0);self.assertEqual(len(json.loads(out.getvalue())['planned_slots']),20)
