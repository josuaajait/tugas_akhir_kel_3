import json
from pathlib import Path
import unittest

from test_foundation import temporary_directory


class FreezeDraftTests(unittest.TestCase):
    def test_draft_pins_bytes_and_never_authorizes_final_run(self):
        from critic_agent.freeze_draft import create_draft, check_draft

        with temporary_directory() as temp:
            root = Path(temp)
            evidence = root / 'pilot.json'
            evidence.write_bytes(b'pilot')
            manifest = root / 'draft.json'
            create_draft(manifest, root, {'pilot_evidence': [evidence]})
            result = check_draft(manifest, root)
            self.assertEqual(result['integrity'], 'VERIFIED')
            self.assertFalse(result['ready_for_final'])
            self.assertIn('held_out_package', result['pending'])
            with self.assertRaises(FileExistsError):
                create_draft(manifest, root, {'pilot_evidence': [evidence]})
            evidence.write_bytes(b'changed')
            self.assertEqual(check_draft(manifest, root)['integrity'], 'FAILED')

    def test_rejects_escaping_paths_and_forged_final_status(self):
        from critic_agent.freeze_draft import create_draft, check_draft

        with temporary_directory() as temp:
            root = Path(temp)
            evidence = root / 'pilot.json'
            evidence.touch()
            manifest = root / 'draft.json'
            create_draft(manifest, root, {'pilot_evidence': [evidence]})
            draft = json.loads(manifest.read_bytes())
            draft['status'] = 'FROZEN'
            manifest.write_text(json.dumps(draft))
            with self.assertRaises(ValueError):
                check_draft(manifest, root)
            draft['status'] = 'DRAFT'
            draft['artifacts'][0]['path'] = '../outside.json'
            manifest.write_text(json.dumps(draft))
            with self.assertRaisesRegex(ValueError, 'Path artefak'):
                check_draft(manifest, root)
