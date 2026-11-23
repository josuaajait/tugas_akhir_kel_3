import json
from pathlib import Path
import unittest

from critic_agent.pilot import create_pilot_manifest
from test_foundation import temporary_directory


class PilotReportTests(unittest.TestCase):
    def test_partial_grid_keeps_errors_and_missing_jobs_out_of_valid_rates(self):
        from critic_agent.pilot_report import pilot_report

        with temporary_directory() as tmp:
            root = Path(tmp)
            manifest = root / 'manifest.json'
            create_pilot_manifest([Path('examples/books.json')], [42, 43, 44, 45, 46], [0], manifest)
            jobs = json.loads(manifest.read_text())['jobs']
            for index, status in enumerate(('LOLOS', 'BELUM LOLOS', 'ERROR', 'STARTED')):
                job = jobs[index]
                folder = root / 'executions' / job['job_id']
                folder.mkdir(parents=True)
                if status == 'STARTED':
                    continue
                stop = ('all_checks_passed', 'identical_code', 'model_error')[index]
                result = dict(job, status=status, kind='resource', revision_count=int(index == 1), stop_reason=stop)
                if status != 'ERROR':
                    run = folder / 'runs' / 'sample'
                    run.mkdir(parents=True)
                    result['run_directory'] = str(run)
                    attempts = [{'iteration': 0, 'dynamic_status': 'PASSED_INTERNAL' if index == 0 else 'FAILED_INTERNAL',
                                 'code_sha256': 'same', 'elapsed_seconds': 2.5, 'model_called': True}]
                    if index == 1:
                        attempts.append(dict(attempts[0], iteration=1, dynamic_status='reused'))
                    common = {'status': status, 'run_id': 'sample', 'revision_count': result['revision_count'],
                              'stop_reason': stop}
                    (run / 'history.json').write_text(json.dumps(dict(common, attempts=attempts)))
                    (run / 'run_manifest.json').write_text(json.dumps(dict(
                        common, model=job['model'], options={'seed': job['seed'], 'temperature': 0}, max_revisions=3)))
                    response = run / 'attempts' / '0' / 'response.json'
                    response.parent.mkdir(parents=True)
                    response.write_text('{"prompt_eval_count": 10, "eval_count": 5}')
                (folder / 'pilot_result.json').write_text(json.dumps(result))

            report = pilot_report([manifest])
            group = report['groups'][0]
            self.assertEqual(group['counts'], {'LOLOS': 1, 'BELUM LOLOS': 1, 'ERROR': 1,
                                               'INCOMPLETE': 1, 'PLANNED': 1})
            self.assertEqual(group['identical_among_valid'], {'numerator': 1, 'denominator': 2})
            self.assertEqual(group['identical_among_revised'], {'numerator': 1, 'denominator': 1})
            self.assertEqual(group['initial_failed_among_valid'], {'numerator': 1, 'denominator': 2})
            self.assertEqual(group['unique_initial_hashes'], 1)
            self.assertEqual(group['duplicate_initial_hashes'], 1)
            self.assertEqual(group['token_usage'], {'prompt_tokens_observed': 20, 'completion_tokens_observed': 10,
                                                    'responses_with_counts': 2, 'model_calls_with_history': 3})
            self.assertEqual(group['transport'], {'model_calls_with_trace': 0, 'model_calls_with_history': 3,
                                                  'http_attempts_observed': None, 'http_retries_observed': None})
            self.assertFalse(list(root.rglob('metadata.json')))
