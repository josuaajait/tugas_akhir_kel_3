import hashlib
import json
from pathlib import Path
import unittest

from test_foundation import temporary_directory


class PilotReferenceTests(unittest.TestCase):
    def write_report(self, root, name, run_id, status='EVALUATED', before=1, after=2):
        folder = root / name
        folder.mkdir()
        report = {'source_run_id': run_id, 'source_status': 'LOLOS', 'status': status,
                  'reason': 'pair_evaluated' if status == 'EVALUATED' else 'environment_error'}
        if status == 'EVALUATED':
            report.update(expected_tests=2, image_id='sha256:'+'a'*64, suite_sha256='b'*64)
            for position, passed in (('initial', before), ('final', after)):
                report[position] = {'passed': passed, 'total': 2, 'code_sha256': self.code_hash,
                                    'status': 'PASSED_REFERENCE' if passed == 2 else 'FAILED_REFERENCE'}
        path = folder / 'evaluation_result.json'
        path.write_text(json.dumps(report), encoding='utf-8')
        return path

    def row(self, root, name, status='LOLOS'):
        folder = root / name
        folder.mkdir()
        for position in ('initial', 'final'):
            (folder / f'{position}_controller.php').write_bytes(b'controller')
        self.code_hash = hashlib.sha256(b'controller').hexdigest()
        return {'run_id': name, 'run_directory': str(folder), 'status': status, 'revision_count': 0,
                'initial_hash': self.code_hash, 'final_hash': self.code_hash}

    def test_repair_regression_retry_error_and_missing_have_separate_denominators(self):
        from critic_agent.pilot_reference_report import attach_evaluations, reference_summary

        with temporary_directory() as tmp:
            root = Path(tmp)
            evaluations = root / 'evaluations'
            evaluations.mkdir()
            rows = [self.row(root, name, status) for name, status in
                    [('repair', 'LOLOS'), ('regression', 'LOLOS'), ('failed_eval', 'LOLOS'),
                     ('missing', 'LOLOS'), ('failed_loop', 'ERROR')]]
            self.write_report(evaluations, 'retry-error', 'repair', status='ERROR')
            self.write_report(evaluations, 'repaired', 'repair')
            self.write_report(evaluations, 'regressed', 'regression', before=2, after=1)
            self.write_report(evaluations, 'only-error', 'failed_eval', status='ERROR')
            rows[0].update(revision_count=2, stop_reason='all_checks_passed')
            rows[4].update(revision_count=3, stop_reason='model_error')

            attach_evaluations(rows, evaluations)
            summary = reference_summary(rows)
            self.assertEqual(summary['n_valid'], 4)
            self.assertEqual(summary['n_pair'], 2)
            self.assertEqual(summary['loop_errors'], 1)
            self.assertEqual(summary['evaluator_errors'], 2)
            self.assertEqual(summary['valid_without_evaluation'], 1)
            self.assertEqual(summary['repair']['percent'], 100)
            self.assertEqual(summary['regression']['percent'], 100)
            self.assertEqual(summary['mean_uplift_pp'], 0)
            self.assertEqual(summary['mean_revisions'], 0.5)
            self.assertEqual(summary['stop_reasons']['model_error'], 1)
            self.assertEqual(summary['initial_pass_rate']['numerator'], 3)
            self.assertEqual(summary['final_pass_rate']['denominator'], 4)
            self.assertEqual(rows[2]['evaluation']['status'], 'ERROR')
            self.assertEqual(rows[3]['evaluation']['status'], 'MISSING')
            self.assertEqual(rows[4]['evaluation']['status'], 'NOT_ELIGIBLE')
            self.assertIsNone(reference_summary([rows[3]])['repair']['percent'])

    def test_rejects_tampered_candidate_and_duplicate_success(self):
        from critic_agent.pilot_reference_report import attach_evaluations

        with temporary_directory() as tmp:
            root = Path(tmp)
            evaluations = root / 'eval'
            evaluations.mkdir()
            row = self.row(root, 'run')
            self.write_report(evaluations, 'one', 'run')
            self.write_report(evaluations, 'two', 'run')
            with self.assertRaisesRegex(ValueError, 'lebih dari satu'):
                attach_evaluations([row], evaluations)
            (evaluations / 'two' / 'evaluation_result.json').unlink()
            (root / 'run' / 'final_controller.php').write_bytes(b'other')
            with self.assertRaisesRegex(ValueError, 'Hash kandidat'):
                attach_evaluations([row], evaluations)
