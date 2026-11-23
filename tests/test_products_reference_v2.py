from pathlib import Path
import shutil
import subprocess
import unittest

from test_foundation import temporary_directory


ROOT = Path(__file__).resolve().parents[1]


class ProductsReferenceV2Tests(unittest.TestCase):
    def test_v1_fingerprint_is_preserved_and_v2_is_distinct(self):
        from critic_agent.reference import reference_suite_hash

        self.assertEqual(reference_suite_hash(),
                         'd59c4d7c5a1311a5020b2f15d9cec203b64a3e83e57ea287caaab4731a6f0778')
        self.assertNotEqual(reference_suite_hash('v2'), reference_suite_hash())

    @unittest.skipUnless(shutil.which('php'), 'PHP needed for trusted assertion probe')
    def test_reference_collection_binds_values_to_id_and_rejects_non_array(self):
        autoload = ROOT/'harness/laravel/vendor/autoload.php'
        if not autoload.is_file():
            self.skipTest('Harness vendor not installed')
        probe = r'''<?php
require $argv[1];
require $argv[2];
require $argv[3];
(new PHPUnit\TextUI\Configuration\Builder)->build(['probe', '--no-configuration']);
$class = new ReflectionClass(Evaluation\ProductsReferenceV2Test::class);
$instance = $class->newInstanceWithoutConstructor();
$method = $class->getMethod('assertStoredCollection');
$one = ['id' => 1, 'name' => 'First', 'price' => 81, 'sku' => 'A'];
$two = ['id' => 2, 'name' => 'Second', 'price' => 167, 'sku' => 'B'];
$invoke = function ($records) use ($instance, $method, $one, $two) {
    $response = Illuminate\Testing\TestResponse::fromBaseResponse(
        new Illuminate\Http\JsonResponse(['data' => $records]));
    $method->invoke($instance, $response, [$one, $two]);
};
$invoke([$one, $two]);
$invoke([$two + ['extra' => 'allowed'], $one]);
foreach ([
    [array_replace($one, ['sku' => 'B']), array_replace($two, ['sku' => 'A'])],
    [array_replace($one, ['price' => 167]), array_replace($two, ['price' => 81])],
    [$one, ['id' => 2, 'sku' => 'B']],
    [$one, $one],
    [$one, array_replace($two, ['id' => '2'])],
    (object) [$one, $two],
] as $records) {
    try { $invoke($records); exit(2); }
    catch (PHPUnit\Framework\AssertionFailedError $error) { }
}
'''
        with temporary_directory() as tmp:
            path = Path(tmp)/'probe.php'
            path.write_text(probe, encoding='utf-8')
            result = subprocess.run(['php', str(path), str(autoload),
                                     str(ROOT/'evaluation/reference-tests/ProductsReferenceTest.php'),
                                     str(ROOT/'evaluation/products-v2/ProductsReferenceV2Test.php')],
                                    text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
