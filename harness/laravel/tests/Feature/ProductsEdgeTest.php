<?php

namespace Tests\Feature;

use App\Models\Product;
use Illuminate\Foundation\Testing\RefreshDatabase;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\TestCase;

// Readiness of the trusted reference controller, not the independent final evaluator.
class ProductsEdgeTest extends TestCase
{
    use RefreshDatabase;

    private function payload(array $overrides = []): array
    {
        return array_replace(['name' => 'Book', 'price' => 120, 'sku' => 'BOOK-1'], $overrides);
    }

    public function test_update_keeps_own_unique_value(): void
    {
        $record = Product::create($this->payload());
        $this->putJson('/api/products/'.$record->id, $this->payload(['name' => 'New']))
            ->assertOk()->assertJsonPath('data.sku', 'BOOK-1');
        $this->assertDatabaseHas('products', ['id' => $record->id, 'name' => 'New']);
    }

    public static function invalidPayloads(): array
    {
        return [
            'name_over_limit' => [['name' => str_repeat('x', 101)], 'name'],
            'negative_price' => [['price' => -1], 'price'],
            'bad_integer' => [['price' => 'oops'], 'price'],
            'bad_string' => [['name' => ['x']], 'name'],
            'duplicate_sku' => [['sku' => 'TAKEN'], 'sku'],
        ];
    }

    #[DataProvider('invalidPayloads')]
    public function test_invalid_values_preserve_all_records(array $overrides, string $field): void
    {
        $target = Product::create($this->payload(['sku' => 'OLD']));
        Product::create($this->payload(['sku' => 'TAKEN']));
        $before = Product::orderBy('id')->get()->toArray();
        $payload = $this->payload($overrides);
        $this->postJson('/api/products', $payload)->assertUnprocessable()->assertJsonValidationErrors([$field]);
        $this->putJson('/api/products/'.$target->id, $payload)->assertUnprocessable()->assertJsonValidationErrors([$field]);
        $this->assertSame($before, Product::orderBy('id')->get()->toArray());
    }

    public function test_boundary_values_are_accepted(): void
    {
        $this->postJson('/api/products', $this->payload(['name' => str_repeat('x', 100), 'price' => 0]))
            ->assertCreated()->assertJsonPath('data.price', 0);
    }
}
