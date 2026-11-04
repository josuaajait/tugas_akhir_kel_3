from pathlib import Path
import shutil
import subprocess
import unittest


@unittest.skipUnless(shutil.which('php'), 'PHP not available')
class HarnessScaffoldTests(unittest.TestCase):
    def test_trusted_reference_uses_available_base_controller(self):
        controllers = Path(__file__).resolve().parents[1]/'harness'/'laravel'/'app'/'Http'/'Controllers'
        # Load only the trusted scaffold and reference declarations, never candidate code.
        check = r'''
require $argv[1];
require $argv[2];
$base = new ReflectionClass('App\\Http\\Controllers\\Controller');
exit($base->isAbstract() && is_subclass_of(
    'App\\Http\\Controllers\\ProductController', $base->getName()
) ? 0 : 1);
'''
        result = subprocess.run(['php', '-n', '-r', check, str(controllers/'Controller.php'),
                                 str(controllers/'ProductController.php')],
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, (result.stdout+result.stderr).decode('utf-8', errors='replace'))
