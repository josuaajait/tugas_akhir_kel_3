<?php

namespace Evaluation;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\TestCase;

// Authored from the products contract, without importing internal test classes.
// Development suite: separate execution does not establish blind final evaluation.
class ProductsReferenceTest extends TestCase
{
    use RefreshDatabase;

    private function body(array $changes = []): array
    {
        return array_replace(['name' => 'Desk lamp', 'price' => 375, 'sku' => 'REF-NEW'], $changes);
    }

    private function insert(string $sku): int
    {
        return DB::table('products')->insertGetId([
            'name' => 'Stored '.$sku, 'price' => 81, 'sku' => $sku,
            'created_at' => '2026-01-01 00:00:00', 'updated_at' => '2026-01-01 00:00:00',
        ]);
    }

    private function rows(): array
    {
        return DB::table('products')->orderBy('id')->get()->map(fn ($row) => (array) $row)->all();
    }

    public function test_empty_collection(): void
    {
        $this->getJson('/api/products')->assertOk()->assertExactJson(['data' => []]);
        $this->assertSame([], $this->rows());
    }

    public function test_list_exposes_persisted_values_without_mutation(): void
    {
        $first = $this->insert('REF-A');
        $second = $this->insert('REF-B');
        $before = $this->rows();
        $this->getJson('/api/products')->assertOk()->assertJsonCount(2, 'data')
            ->assertJsonFragment(['id' => $first, 'name' => 'Stored REF-A', 'price' => 81, 'sku' => 'REF-A'])
            ->assertJsonFragment(['id' => $second, 'name' => 'Stored REF-B', 'price' => 81, 'sku' => 'REF-B']);
        $this->assertSame($before, $this->rows());
    }

    public function test_create_returns_and_persists_new_values(): void
    {
        $this->insert('REF-KEEP');
        $before = $this->rows();
        $response = $this->postJson('/api/products', $this->body())->assertCreated()
            ->assertJsonPath('data.name', 'Desk lamp')->assertJsonPath('data.price', 375)
            ->assertJsonPath('data.sku', 'REF-NEW');
        $id = $response->json('data.id');
        $this->assertIsInt($id);
        $this->assertDatabaseHas('products', ['id' => $id] + $this->body());
        $after = $this->rows();
        $this->assertCount(2, $after);
        $this->assertSame($before[0], $after[0]);
    }

    public function test_read_selects_requested_record_without_mutation(): void
    {
        $this->insert('REF-OTHER');
        $target = $this->insert('REF-TARGET');
        $before = $this->rows();
        $this->getJson('/api/products/'.$target)->assertOk()->assertJsonPath('data.id', $target)
            ->assertJsonPath('data.name', 'Stored REF-TARGET')->assertJsonPath('data.price', 81)
            ->assertJsonPath('data.sku', 'REF-TARGET');
        $this->assertSame($before, $this->rows());
    }

    public function test_update_replaces_target_and_preserves_neighbour(): void
    {
        $this->insert('REF-KEEP');
        $target = $this->insert('REF-OLD');
        $before = $this->rows();
        $this->putJson('/api/products/'.$target, $this->body())->assertOk()
            ->assertJsonPath('data.id', $target)->assertJsonPath('data.name', 'Desk lamp')
            ->assertJsonPath('data.price', 375)->assertJsonPath('data.sku', 'REF-NEW');
        $this->assertDatabaseHas('products', ['id' => $target] + $this->body());
        $after = $this->rows();
        $this->assertCount(2, $after);
        $this->assertSame($before[0], $after[0]);
    }

    public function test_delete_is_empty_204_and_preserves_neighbour(): void
    {
        $this->insert('REF-KEEP');
        $target = $this->insert('REF-DELETE');
        $before = $this->rows();
        $this->deleteJson('/api/products/'.$target)->assertNoContent();
        $this->assertSame([$before[0]], $this->rows());
    }

    public static function missingOperations(): array
    {
        return ['show' => ['GET'], 'update' => ['PUT'], 'destroy' => ['DELETE']];
    }

    #[DataProvider('missingOperations')]
    public function test_missing_identifier_is_json_404_without_mutation(string $method): void
    {
        $this->insert('REF-KEEP');
        $before = $this->rows();
        $response = $this->json($method, '/api/products/999999', $this->body())->assertNotFound()
            ->assertHeader('Content-Type', 'application/json');
        $this->assertIsArray($response->json());
        $this->assertSame($before, $this->rows());
    }

    public static function invalidBodies(): array
    {
        $changes = [
            'missing_name' => ['name', null, true], 'missing_price' => ['price', null, true],
            'missing_sku' => ['sku', null, true], 'empty_name' => ['name', '', false],
            'empty_sku' => ['sku', '', false], 'long_name' => ['name', str_repeat('n', 101), false],
            'negative_price' => ['price', -2, false], 'invalid_integer' => ['price', 'abc', false],
            'array_name' => ['name', ['nested'], false], 'duplicate_sku' => ['sku', 'REF-TAKEN', false],
        ];
        $cases = [];
        foreach (['store', 'update'] as $operation) {
            foreach ($changes as $label => $parameters) $cases[$operation.'_'.$label] = [$operation, ...$parameters];
        }
        return $cases;
    }

    #[DataProvider('invalidBodies')]
    public function test_invalid_input_reports_field_and_preserves_database(string $operation, string $field, mixed $value, bool $remove): void
    {
        $target = $this->insert('REF-OLD');
        $this->insert('REF-TAKEN');
        $before = $this->rows();
        $body = $this->body([$field => $value]);
        if ($remove) unset($body[$field]);
        $response = $operation === 'store'
            ? $this->postJson('/api/products', $body)
            : $this->putJson('/api/products/'.$target, $body);
        $response->assertUnprocessable()->assertJsonValidationErrors([$field]);
        $this->assertSame($before, $this->rows());
    }

    public static function acceptedBoundaries(): array
    {
        return ['maximum_name_and_zero_price' => [str_repeat('z', 100)], 'zero_price' => ['Budget item']];
    }

    #[DataProvider('acceptedBoundaries')]
    public function test_valid_boundary_is_persisted(string $name): void
    {
        $body = $this->body(['name' => $name, 'price' => 0]);
        $this->postJson('/api/products', $body)->assertCreated()->assertJsonPath('data.name', $name)
            ->assertJsonPath('data.price', 0)->assertJsonPath('data.sku', 'REF-NEW');
        $this->assertDatabaseHas('products', $body);
        $this->assertDatabaseCount('products', 1);
    }

    public function test_update_retains_own_unique_sku(): void
    {
        $id = $this->insert('REF-OWN');
        $this->insert('REF-OTHER');
        $before = $this->rows();
        $this->putJson('/api/products/'.$id, $this->body(['sku' => 'REF-OWN']))->assertOk()
            ->assertJsonPath('data.id', $id)->assertJsonPath('data.sku', 'REF-OWN');
        $after = $this->rows();
        $this->assertCount(2, $after);
        $this->assertSame($before[1], $after[1]);
        $this->assertDatabaseHas('products', ['id' => $id] + $this->body(['sku' => 'REF-OWN']));
    }

    public function test_crud_sequence_reads_back_changes(): void
    {
        $id = $this->postJson('/api/products', $this->body())->assertCreated()->json('data.id');
        $this->assertIsInt($id);
        $this->getJson('/api/products/'.$id)->assertOk()->assertJsonPath('data.name', 'Desk lamp');
        $this->putJson('/api/products/'.$id, $this->body(['name' => 'Changed']))->assertOk();
        $this->getJson('/api/products')->assertOk()->assertJsonCount(1, 'data')->assertJsonPath('data.0.name', 'Changed');
        $this->deleteJson('/api/products/'.$id)->assertNoContent();
        $response = $this->getJson('/api/products/'.$id)->assertNotFound();
        $this->assertIsArray($response->json());
        $this->assertSame([], $this->rows());
    }
}
