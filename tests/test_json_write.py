import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from critic_agent.orchestrator import _write_json


class AtomicJsonWriteTests(unittest.TestCase):
    def test_transient_windows_replace_denial_retries_same_complete_bytes(self):
        denied=PermissionError(13,'temporarily locked');denied.winerror=5
        original=Path.replace
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'history.json';path.write_text('{"old":true}')
            calls=[]
            def replace(source,target):
                calls.append(source.read_bytes())
                if len(calls)<3:raise denied
                return original(source,target)
            with patch.object(Path,'replace',replace),patch('critic_agent.orchestrator.time.sleep') as sleep:
                _write_json(path,{'new':True})
            self.assertEqual(json.loads(path.read_bytes()),{'new':True})
            self.assertEqual(len(calls),3)
            self.assertEqual(len(set(calls)),1)
            self.assertEqual(sleep.call_count,2)

    def test_persistent_windows_denial_preserves_old_and_pending_bytes(self):
        denied=PermissionError(13,'locked');denied.winerror=32
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'history.json';old=b'{"old":true}';path.write_bytes(old)
            with patch.object(Path,'replace',side_effect=denied) as replace,patch('critic_agent.orchestrator.time.sleep'):
                with self.assertRaises(PermissionError):_write_json(path,{'new':True})
            self.assertEqual(replace.call_count,6)
            self.assertEqual(path.read_bytes(),old)
            self.assertEqual(json.loads(path.with_suffix('.json.tmp').read_bytes()),{'new':True})

    def test_other_permission_failure_is_not_retried(self):
        denied=PermissionError(13,'access denied')
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(Path,'replace',side_effect=denied) as replace,patch('critic_agent.orchestrator.time.sleep') as sleep:
                with self.assertRaises(PermissionError):_write_json(Path(folder)/'history.json',{})
            self.assertEqual(replace.call_count,1);sleep.assert_not_called()
