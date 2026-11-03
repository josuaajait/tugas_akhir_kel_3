import json
import shutil
from pathlib import Path
import subprocess
import sys
import unittest
from test_foundation import SPEC, temporary_directory
from test_static import GOOD


class CliTests(unittest.TestCase):
    def command(self, *args):
        return subprocess.run([sys.executable, '-m', 'critic_agent', *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8')

    def test_help(self):
        result = self.command('--help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('generate', result.stdout)

    def test_validate_and_prompt(self):
        with temporary_directory() as folder:
            path = Path(folder)/'spec.json'
            path.write_text(json.dumps(SPEC), encoding='utf-8')
            self.assertEqual(self.command('validate', path).returncode, 0)
            prompt = self.command('prompt', path)
            self.assertEqual(prompt.returncode, 0)
            self.assertIn('ProductController', prompt.stdout)

    def test_invalid_json_has_friendly_error(self):
        with temporary_directory() as folder:
            path = Path(folder)/'spec.json'
            path.write_text('{oops')
            result = self.command('validate', path)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)

    @unittest.skipUnless(shutil.which('php'), 'PHP not available')
    def test_analyze(self):
        with temporary_directory() as folder:
            path = Path(folder)/'spec.json'
            code = Path(folder)/'code.php'
            path.write_text(json.dumps(SPEC))
            code.write_text(GOOD)
            result = self.command('analyze', path, code)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'AWAITING_DYNAMIC_TESTS')


if __name__ == '__main__':
    unittest.main()
