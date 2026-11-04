<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\Support\ResourceFixtures;
use Tests\TestCase;

// Trusted reference readiness only; never selected for candidate execution.
class ResourceReadinessTest extends TestCase
{
    use RefreshDatabase, ResourceFixtures;

    public static function invalidBodies(): array
    {
        $cases = [];
        foreach (['store', 'update'] as $operation) {
            foreach (self::contract()['readiness_invalid'] as $case) {
                $cases[$operation.'_'.$case['name']] = [$operation, $case['field'], $case['payload']];
            }
        }
        return $cases;
    }

    #[DataProvider('invalidBodies')]
    public function test_invalid_values_preserve_database(string $operation, string $field, array $body): void
    {
        $id = $this->insert('target');
        $this->insert('other');
        $before = $this->rows();
        $response = $operation === 'store' ? $this->postJson($this->uri(), $body)
            : $this->putJson($this->uri($id), $body);
        $response->assertUnprocessable()->assertJsonValidationErrors([$field]);
        $this->assertSame($before, $this->rows());
    }

    public static function boundaries(): array
    {
        return array_map(fn ($case) => [$case['payload']], self::contract()['readiness_valid']);
    }

    #[DataProvider('boundaries')]
    public function test_valid_boundaries_are_persisted(array $body): void
    {
        $response = $this->postJson($this->uri(), $body)->assertCreated();
        $id = $response->json('data.id');
        $this->assertIsInt($id);
        $this->assertRecord($response, $id, $body);
        $this->assertDatabaseHas($this->table(), ['id' => $id] + $body);
        $this->assertDatabaseCount($this->table(), 1);
    }

    public function test_update_accepts_own_values_and_preserves_other(): void
    {
        $id = $this->insert('target');
        $this->insert('other');
        $before = $this->rows();
        $body = $this->body('target');
        $this->assertRecord($this->putJson($this->uri($id), $body)->assertOk(), $id, $body);
        $this->assertDatabaseHas($this->table(), ['id' => $id] + $body);
        $this->assertSame($before[1], $this->rows()[1]);
        $this->assertDatabaseCount($this->table(), 2);
    }
}
