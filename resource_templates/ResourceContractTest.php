<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\Support\ResourceFixtures;
use Tests\TestCase;

class ResourceContractTest extends TestCase
{
    use RefreshDatabase, ResourceFixtures;

    public function test_index_returns_records_without_mutation(): void
    {
        $first = $this->insert('target');
        $second = $this->insert('other');
        $before = $this->rows();
        $response = $this->getJson($this->uri())->assertOk()->assertJsonCount(2, 'data');
        $response->assertJsonFragment(['id' => $first] + $this->body('target'));
        $response->assertJsonFragment(['id' => $second] + $this->body('other'));
        $this->assertSame($before, $this->rows());
    }

    public function test_store_persists_payload_and_preserves_other(): void
    {
        $this->insert('other');
        $before = $this->rows();
        $response = $this->postJson($this->uri(), $this->body())->assertCreated();
        $id = $response->json('data.id');
        $this->assertIsInt($id);
        $this->assertRecord($response, $id, $this->body());
        $this->assertDatabaseHas($this->table(), ['id' => $id] + $this->body());
        $this->assertDatabaseCount($this->table(), 2);
        $this->assertSame($before[0], $this->rows()[0]);
    }

    public function test_show_returns_requested_record_without_mutation(): void
    {
        $this->insert('other');
        $id = $this->insert('target');
        $before = $this->rows();
        $this->assertRecord($this->getJson($this->uri($id))->assertOk(), $id, $this->body('target'));
        $this->assertSame($before, $this->rows());
    }

    public function test_update_changes_only_target(): void
    {
        $id = $this->insert('target');
        $this->insert('other');
        $before = $this->rows();
        $body = $this->body('updated');
        $this->assertRecord($this->putJson($this->uri($id), $body)->assertOk(), $id, $body);
        $this->assertDatabaseHas($this->table(), ['id' => $id] + $body);
        $this->assertDatabaseCount($this->table(), 2);
        $this->assertSame($before[1], $this->rows()[1]);
    }

    public function test_destroy_removes_only_target_and_returns_empty_204(): void
    {
        $id = $this->insert('target');
        $this->insert('other');
        $before = $this->rows();
        $this->deleteJson($this->uri($id))->assertNoContent();
        $this->assertSame([$before[1]], $this->rows());
    }

    public static function missingFields(): array
    {
        $cases = [];
        foreach (['store', 'update'] as $operation) {
            foreach (self::contract()['spec']['fields'] as $field) {
                $cases[$operation.'_'.$field['name']] = [$operation, $field['name']];
            }
        }
        return $cases;
    }

    #[DataProvider('missingFields')]
    public function test_required_field_rejection_preserves_data(string $operation, string $field): void
    {
        $id = $this->insert('target');
        $this->insert('other');
        $before = $this->rows();
        $body = $this->body();
        unset($body[$field]);
        $response = $operation === 'store' ? $this->postJson($this->uri(), $body)
            : $this->putJson($this->uri($id), $body);
        $response->assertUnprocessable()->assertJsonValidationErrors([$field]);
        $this->assertSame($before, $this->rows());
    }

    public static function missingOperations(): array
    {
        return ['show' => ['show'], 'update' => ['update'], 'destroy' => ['destroy']];
    }

    #[DataProvider('missingOperations')]
    public function test_missing_id_returns_json_404_without_mutation(string $operation): void
    {
        $this->insert('other');
        $before = $this->rows();
        $url = $this->uri(999999);
        $response = match ($operation) {
            'show' => $this->getJson($url),
            'update' => $this->putJson($url, $this->body('missing')),
            'destroy' => $this->deleteJson($url),
        };
        $response->assertNotFound()->assertHeader('Content-Type', 'application/json');
        $this->assertIsArray($response->json());
        $this->assertSame($before, $this->rows());
    }
}
