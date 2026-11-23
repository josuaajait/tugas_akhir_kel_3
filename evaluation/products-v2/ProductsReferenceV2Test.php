<?php

namespace Evaluation;

use Illuminate\Support\Facades\DB;
use Illuminate\Testing\TestResponse;

if (!class_exists(ProductsReferenceTest::class, false)) {
    require_once __DIR__.'/ProductsReferenceTest.php';
}

class ProductsReferenceV2Test extends ProductsReferenceTest
{
    public function test_empty_collection(): void
    {
        $this->assertStoredCollection($this->getJson('/api/products'), []);
        $this->assertSame(0, DB::table('products')->count());
    }

    public function test_list_exposes_persisted_values_without_mutation(): void
    {
        foreach ([['Desk lamp', 81, 'REF-A'], ['Shelf', 167, 'REF-B']] as [$name, $price, $sku]) {
            DB::table('products')->insert(['name' => $name, 'price' => $price, 'sku' => $sku,
                'created_at' => '2026-01-01 00:00:00', 'updated_at' => '2026-01-01 00:00:00']);
        }
        $before = $this->snapshotRows();
        $this->assertStoredCollection($this->getJson('/api/products'), $before);
        $this->assertSame($before, $this->snapshotRows());
    }

    private function snapshotRows(): array
    {
        return DB::table('products')->orderBy('id')->get()->map(static fn ($row) => (array) $row)->all();
    }

    private function assertStoredCollection(TestResponse $response, array $expected): void
    {
        $response->assertOk();
        $body = json_decode($response->getContent());
        $this->assertIsObject($body);
        $records = $body->data ?? null;
        $this->assertIsArray($records);
        $this->assertCount(count($expected), $records);

        $expectedById = array_column($expected, null, 'id');
        foreach ($records as $record) {
            $this->assertIsObject($record);
            $id = $record->id ?? null;
            $this->assertIsInt($id);
            $this->assertArrayHasKey($id, $expectedById, "Unexpected or duplicate product ID $id.");
            foreach (['name', 'price', 'sku'] as $field) {
                $this->assertSame($expectedById[$id][$field], $record->$field ?? null,
                    "Product $id has an incorrect $field.");
            }
            unset($expectedById[$id]);
        }
    }
}
