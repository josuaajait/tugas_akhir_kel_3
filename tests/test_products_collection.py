"""Exercise trusted assertions against response fixtures without booting Laravel."""
from pathlib import Path
import shutil
import subprocess
import unittest

from test_foundation import temporary_directory


ROOT = Path(__file__).resolve().parents[1]
LARAVEL = ROOT / 'harness' / 'laravel'


class ProductsCollectionTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('php'), 'PHP needed for assertion probe')
    def test_index_requires_complete_records_bound_to_integer_ids(self):
        autoload = LARAVEL / 'vendor' / 'autoload.php'
        if not autoload.is_file():
            self.skipTest('Harness vendor not installed')
        script = r'''<?php
require $argv[1];
require $argv[2];
(new PHPUnit\TextUI\Configuration\Builder)->build(['assertion-probe', '--no-configuration']);
$class = new ReflectionClass(Tests\Feature\ProductsContractTest::class);
$instance = $class->newInstanceWithoutConstructor();
$method = $class->getMethod('assertIndexRecords');
$first = ['id' => 1, 'name' => 'Book', 'price' => 120, 'sku' => 'BOOK-1'];
$second = ['id' => 2, 'name' => 'Other', 'price' => 250, 'sku' => 'OTHER'];
$expected = [1 => $first, 2 => $second];
$invoke = function ($records) use ($method, $instance, $expected) {
    $response = Illuminate\Testing\TestResponse::fromBaseResponse(
        new Illuminate\Http\JsonResponse(['data' => $records])
    );
    $method->invoke($instance, $response, $expected);
};
$invoke([$first, $second]);
$invoke([$second + ['created_at' => '2026-01-01'], $first]);
$bad = [
    'swapped SKU' => [array_replace($first, ['sku' => 'OTHER']), array_replace($second, ['sku' => 'BOOK-1'])],
    'missing fields' => [$first, ['id' => 2, 'sku' => 'OTHER']],
    'wrong fields' => [$first, array_replace($second, ['name' => 'Wrong', 'price' => -1])],
    'split fields' => [['id' => 1, 'name' => 'Book', 'sku' => 'BOOK-1'], $second],
    'duplicate ID' => [$first, $first],
    'unknown ID' => [$first, array_replace($second, ['id' => 3])],
    'string ID' => [$first, array_replace($second, ['id' => '2'])],
    'object instead of list' => (object) [$first, $second],
];
foreach ($bad as $name => $records) {
    try {
        $invoke($records);
    } catch (PHPUnit\Framework\AssertionFailedError $error) {
        continue;
    }
    fwrite(STDERR, "Accepted invalid response: $name\n");
    exit(1);
}
'''
        with temporary_directory() as tmp:
            probe = Path(tmp) / 'probe.php'
            probe.write_text(script, encoding='utf-8')
            result = subprocess.run(
                ['php', str(probe), str(autoload),
                 str(LARAVEL / 'tests' / 'Feature' / 'ProductsContractTest.php')],
                capture_output=True, text=True, timeout=15,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
