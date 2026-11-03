<?php

namespace Tests\Feature;

use App\Models\Product;
use Illuminate\Foundation\Testing\RefreshDatabase;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\TestCase;

class ProductsContractTest extends TestCase
{
    use RefreshDatabase;

    private function payload(array $overrides = []): array
    {
        return array_replace(['name' => 'Book', 'price' => 120, 'sku' => 'BOOK-1'], $overrides);
    }

    private function record(array $overrides = []): Product
    {
        return Product::create($this->payload($overrides));
    }

    private function snapshot(): array
    {
        return Product::orderBy('id')->get()->toArray();
    }

    public function test_index_returns_records_without_changing_data(): void
    {
        $first = $this->record();
        $second = $this->record(['sku' => 'OTHER']);
        $before = $this->snapshot();
        $this->getJson('/api/products')->assertOk()->assertJsonCount(2, 'data')
            ->assertJsonFragment(['id' => $first->id, 'name' => 'Book', 'price' => 120, 'sku' => 'BOOK-1'])
            ->assertJsonFragment(['id' => $second->id, 'sku' => 'OTHER']);
        $this->assertSame($before, $this->snapshot());
    }

    public function test_store_persists_one_record_and_preserves_other_records(): void
    {
        $other = $this->record(['sku' => 'OTHER']);
        $before = $other->toArray();
        $response = $this->postJson('/api/products', $this->payload())
            ->assertCreated()->assertJsonPath('data.name', 'Book')->assertJsonPath('data.price', 120)
            ->assertJsonPath('data.sku', 'BOOK-1');
        $id = $response->json('data.id');
        $this->assertIsInt($id);
        $this->assertDatabaseHas('products', ['id' => $id, 'sku' => 'BOOK-1', 'price' => 120, 'name' => 'Book']);
        $this->assertDatabaseCount('products', 2);
        $this->assertSame($before, $other->fresh()->toArray());
    }

    public function test_show_returns_target_without_changing_data(): void
    {
        $target = $this->record();
        $this->record(['sku' => 'OTHER']);
        $before = $this->snapshot();
        $this->getJson('/api/products/'.$target->id)->assertOk()
            ->assertJsonPath('data.id', $target->id)->assertJsonPath('data.sku', 'BOOK-1')
            ->assertJsonPath('data.name', 'Book')->assertJsonPath('data.price', 120);
        $this->assertSame($before, $this->snapshot());
    }

    public function test_update_changes_only_target(): void
    {
        $target = $this->record();
        $other = $this->record(['sku' => 'OTHER']);
        $before = $other->toArray();
        $payload = $this->payload(['name' => 'Updated', 'price' => 200, 'sku' => 'NEW']);
        $this->putJson('/api/products/'.$target->id, $payload)->assertOk()
            ->assertJsonPath('data.id', $target->id)->assertJsonPath('data.name', 'Updated')
            ->assertJsonPath('data.price', 200)->assertJsonPath('data.sku', 'NEW');
        $this->assertDatabaseHas('products', ['id' => $target->id] + $payload);
        $this->assertDatabaseCount('products', 2);
        $this->assertSame($before, $other->fresh()->toArray());
    }

    public function test_destroy_removes_only_target_and_returns_empty_body(): void
    {
        $target = $this->record();
        $other = $this->record(['sku' => 'OTHER']);
        $before = $other->toArray();
        $this->deleteJson('/api/products/'.$target->id)->assertNoContent();
        $this->assertDatabaseMissing('products', ['id' => $target->id]);
        $this->assertDatabaseCount('products', 1);
        $this->assertSame($before, $other->fresh()->toArray());
    }

    public static function missingFields(): array
    {
        $cases = [];
        foreach (['store', 'update'] as $operation) {
            foreach (['name', 'price', 'sku'] as $field) {
                $cases[$operation.'_'.$field] = [$operation, $field];
            }
        }
        return $cases;
    }

    #[DataProvider('missingFields')]
    public function test_required_field_rejection_preserves_data(string $operation, string $field): void
    {
        $target = $this->record(['sku' => 'OLD']);
        $this->record(['sku' => 'OTHER']);
        $before = $this->snapshot();
        $payload = $this->payload();
        unset($payload[$field]);
        $response = $operation === 'store'
            ? $this->postJson('/api/products', $payload)
            : $this->putJson('/api/products/'.$target->id, $payload);
        $response->assertUnprocessable()->assertJsonValidationErrors([$field]);
        $this->assertSame($before, $this->snapshot());
    }

    public static function missingOperations(): array
    {
        return [['show'], ['update'], ['destroy']];
    }

    #[DataProvider('missingOperations')]
    public function test_missing_id_returns_json_404_without_changing_data(string $operation): void
    {
        $this->record();
        $before = $this->snapshot();
        $url = '/api/products/999999';
        $response = match ($operation) {
            'show' => $this->getJson($url),
            'update' => $this->putJson($url, $this->payload(['sku' => 'NEW'])),
            'destroy' => $this->deleteJson($url),
        };
        $response->assertNotFound()->assertHeader('Content-Type', 'application/json');
        $this->assertIsArray($response->json());
        $this->assertSame($before, $this->snapshot());
    }
}
