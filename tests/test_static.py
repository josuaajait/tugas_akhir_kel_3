import shutil
import unittest
from critic_agent.static import analyze, StaticEnvironmentError
from test_foundation import SPEC

GOOD = r'''<?php
namespace App\Http\Controllers;
use Illuminate\Http\Request;
class ProductController {
 public function index() {}
 public function store(Request $request) {}
 public function show($id) {}
 public function update(Request $request, $id) {}
 public function destroy($id) {}
}
'''


@unittest.skipUnless(shutil.which('php'), 'PHP not available')
class StaticTests(unittest.TestCase):
    def test_correct_structure_waits_for_dynamic(self):
        result = analyze(GOOD, SPEC)
        self.assertEqual(result['findings'], [])
        self.assertEqual(result['status'], 'AWAITING_DYNAMIC_TESTS')

    def test_syntax_error(self):
        result = analyze(GOOD.replace('index() {}', 'index( {}'), SPEC)
        self.assertEqual(result['findings'][0]['check'], 'syntax')

    def test_method_text_in_comment_or_string_does_not_count(self):
        for fake in ['/* public function show($id) {} */',
                     "public $example = 'public function show($id) {}';"]:
            result = analyze(GOOD.replace('public function show($id) {}', fake), SPEC)
            self.assertTrue(any(f['check'] == 'method' for f in result['findings']))

    def test_wrong_namespace_class_visibility_and_signature(self):
        for old, new, check in [('App\\Http\\Controllers', 'Other', 'namespace'),
                                ('ProductController', 'WrongController', 'class'),
                                ('public function show', 'private function show', 'visibility'),
                                ('show($id)', 'show(Product $product)', 'signature'),
                                ('show($id)', 'show($id = 1)', 'signature')]:
            with self.subTest(check=check):
                result = analyze(GOOD.replace(old, new), SPEC)
                self.assertTrue(any(f['check'] == check for f in result['findings']), result)

    def test_candidate_is_tokenized_not_executed(self):
        result = analyze(GOOD+'\nexit("EXECUTED");', SPEC)
        self.assertEqual(result['status'], 'AWAITING_DYNAMIC_TESTS')

    def test_missing_php_is_environment_error(self):
        with self.assertRaises(StaticEnvironmentError):
            analyze(GOOD, SPEC, php='missing-php-executable-critic')

    def test_unimported_or_wrong_request_type_rejected(self):
        for code in [GOOD.replace('use Illuminate\\Http\\Request;', ''),
                     GOOD.replace('use Illuminate\\Http\\Request;', 'use Other\\Request;')]:
            self.assertTrue(any(f['check'] == 'signature' for f in analyze(code, SPEC)['findings']))

    def test_request_import_alias_is_accepted(self):
        code = GOOD.replace('use Illuminate\\Http\\Request;', 'use Illuminate\\Http\\Request as Input;')
        code = code.replace('(Request ', '(Input ')
        self.assertEqual(analyze(code, SPEC)['findings'], [])

    def test_interpolated_strings_do_not_break_class_depth(self):
        code = GOOD.replace('index() {}', 'index() { $x = "{$this->value}"; }')
        self.assertEqual(analyze(code, SPEC)['findings'], [])

    def test_later_namespace_cannot_hide_wrong_controller_namespace(self):
        code = GOOD.replace('namespace App\\Http\\Controllers;', 'namespace Wrong;')
        code += '\nnamespace App\\Http\\Controllers;'
        self.assertTrue(analyze(code, SPEC)['findings'])

    def test_abstract_or_duplicate_methods_rejected(self):
        for code in [GOOD.replace('class ProductController', 'abstract class ProductController'),
                     GOOD.replace('public function show($id) {}', 'public function show($id) {} public function show($id) {}')]:
            self.assertTrue(analyze(code, SPEC)['findings'])


if __name__ == '__main__':
    unittest.main()
