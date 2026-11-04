<?php

namespace Evaluation;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\TestCase;

// Separate hand-authored development oracle. Does not load internal fixture/test classes.
class ResourceReferenceTest extends TestCase
{
    use RefreshDatabase;

    private static function profile(): array
    {
        return json_decode(file_get_contents(dirname(__DIR__).'/reference-profile.json'), true, 512, JSON_THROW_ON_ERROR);
    }

    private function table(): string { return self::profile()['spec']['resource']; }
    private function url(?int $id = null): string { return '/api/'.$this->table().($id === null ? '' : '/'.$id); }
    private function body(string $role = 'new'): array { return self::profile()['fixtures'][$role]; }

    private function insertFixture(string $role): int
    {
        return DB::table($this->table())->insertGetId($this->body($role) + [
            'created_at' => '2026-02-03 04:05:06', 'updated_at' => '2026-02-03 04:05:06',
        ]);
    }

    private function state(): array
    {
        return DB::table($this->table())->orderBy('id')->get()->map(fn ($record) => (array) $record)->all();
    }

    private function assertBody($response, int $id, array $expected): void
    {
        $response->assertJsonPath('data.id', $id);
        foreach ($expected as $field => $value) $response->assertJsonPath('data.'.$field, $value);
    }

    private function assertCollectionRecords(array $records, array $expectedById): void
    {
        $this->assertTrue(array_is_list($records));
        $this->assertCount(count($expectedById), $records);
        $seen = [];
        foreach ($records as $record) {
            $this->assertIsArray($record);
            $this->assertArrayHasKey('id', $record);
            $this->assertIsInt($record['id']);
            $id = $record['id'];
            $this->assertArrayHasKey($id, $expectedById);
            $this->assertArrayNotHasKey($id, $seen);
            $seen[$id] = true;
            foreach ($expectedById[$id] as $field => $value) {
                $this->assertArrayHasKey($field, $record);
                $this->assertSame($value, $record[$field]);
            }
        }
    }

    public function test_empty_collection_is_json_and_preserves_empty_database(): void
    {
        $this->getJson($this->url())->assertOk()->assertExactJson(['data' => []]);
        $this->assertSame([], $this->state());
    }

    public function test_collection_contains_both_persisted_records_without_changes(): void
    {
        $first = $this->insertFixture('other');
        $second = $this->insertFixture('target');
        $before = $this->state();
        $response = $this->getJson($this->url())->assertOk();
        $records = $response->json('data');
        $this->assertIsArray($records);
        $this->assertCollectionRecords($records, [$first => $this->body('other'), $second => $this->body('target')]);
        $this->assertSame($before, $this->state());
    }

    public function test_create_exposes_inserted_values_and_keeps_existing_record(): void
    {
        $this->insertFixture('other');
        $before = $this->state();
        $response = $this->postJson($this->url(), $this->body())->assertCreated();
        $id = $response->json('data.id');
        $this->assertIsInt($id);
        $this->assertBody($response, $id, $this->body());
        $this->assertDatabaseHas($this->table(), ['id' => $id] + $this->body());
        $after = $this->state();
        $this->assertCount(2, $after);
        $this->assertSame($before[0], $after[0]);
    }

    public function test_read_uses_requested_identifier_and_does_not_write(): void
    {
        $this->insertFixture('other');
        $id = $this->insertFixture('target');
        $before = $this->state();
        $this->assertBody($this->getJson($this->url($id))->assertOk(), $id, $this->body('target'));
        $this->assertSame($before, $this->state());
    }

    public function test_replacement_returns_and_persists_all_values_only_on_target(): void
    {
        $id = $this->insertFixture('target');
        $this->insertFixture('other');
        $before = $this->state();
        $body = $this->body('updated');
        $this->assertBody($this->putJson($this->url($id), $body)->assertOk(), $id, $body);
        $this->assertDatabaseHas($this->table(), ['id' => $id] + $body);
        $after = $this->state();
        $this->assertCount(2, $after);
        $this->assertSame($before[1], $after[1]);
    }

    public function test_deletion_is_empty_204_and_removes_only_requested_record(): void
    {
        $id = $this->insertFixture('target');
        $this->insertFixture('other');
        $before = $this->state();
        $this->deleteJson($this->url($id))->assertNoContent();
        $this->assertSame([$before[1]], $this->state());
    }

    public static function missingOperations(): array
    {
        return ['read' => ['GET'], 'replace' => ['PUT'], 'delete' => ['DELETE']];
    }

    #[DataProvider('missingOperations')]
    public function test_unknown_identifier_is_json_404_and_keeps_all_rows(string $verb): void
    {
        $this->insertFixture('target');
        $this->insertFixture('other');
        $before = $this->state();
        $response = $this->json($verb, $this->url(987654), $this->body())->assertNotFound()
            ->assertHeader('Content-Type', 'application/json');
        $this->assertIsArray($response->json());
        $this->assertSame($before, $this->state());
    }

    public static function invalidRequests(): array
    {
        $cases = [];
        foreach (['POST', 'PUT'] as $verb) {
            foreach (self::profile()['invalid'] as $case) {
                $cases[$verb.'_'.$case['name']] = [$verb, $case['field'], $case['payload']];
            }
        }
        return $cases;
    }

    #[DataProvider('invalidRequests')]
    public function test_invalid_payload_reports_named_field_without_database_changes(string $verb, string $field, array $payload): void
    {
        $id = $this->insertFixture('target');
        $this->insertFixture('other');
        $before = $this->state();
        $this->json($verb, $verb === 'POST' ? $this->url() : $this->url($id), $payload)
            ->assertUnprocessable()->assertJsonValidationErrors([$field]);
        $this->assertSame($before, $this->state());
    }

    public static function validRequests(): array
    {
        $cases = [];
        foreach (['POST', 'PUT'] as $verb) {
            foreach (self::profile()['valid'] as $case) {
                $cases[$verb.'_'.$case['name']] = [$verb, $case['payload']];
            }
        }
        return $cases;
    }

    #[DataProvider('validRequests')]
    public function test_boundary_payload_is_accepted_and_persisted(string $verb, array $payload): void
    {
        $id = $this->insertFixture('target');
        $this->insertFixture('other');
        $before = $this->state();
        $response = $this->json($verb, $verb === 'POST' ? $this->url() : $this->url($id), $payload)
            ->assertStatus($verb === 'POST' ? 201 : 200);
        $returned = $response->json('data.id');
        $this->assertIsInt($returned);
        $this->assertBody($response, $returned, $payload);
        $this->assertDatabaseHas($this->table(), ['id' => $returned] + $payload);
        $after = $this->state();
        if ($verb === 'POST') {
            $this->assertCount(3, $after);
            $this->assertNotContains($returned, array_column($before, 'id'));
            $this->assertSame($before, array_slice($after, 0, 2));
        } else {
            $this->assertSame($id, $returned);
            $this->assertCount(2, $after);
            $this->assertSame($before[1], $after[1]);
        }
    }

    public function test_update_accepts_own_unique_values_and_preserves_neighbour(): void
    {
        $id = $this->insertFixture('target');
        $this->insertFixture('other');
        $before = $this->state();
        $body = $this->body('target');
        $this->assertBody($this->putJson($this->url($id), $body)->assertOk(), $id, $body);
        $this->assertDatabaseHas($this->table(), ['id' => $id] + $body);
        $this->assertCount(2, $this->state());
        $this->assertSame($before[1], $this->state()[1]);
    }

    public function test_sequential_crud_reads_back_persisted_replacement_and_deletion(): void
    {
        $response = $this->postJson($this->url(), $this->body())->assertCreated();
        $id = $response->json('data.id');
        $this->assertIsInt($id);
        $this->assertBody($this->getJson($this->url($id))->assertOk(), $id, $this->body());
        $body = $this->body('updated');
        $this->putJson($this->url($id), $body)->assertOk();
        $this->assertBody($this->getJson($this->url($id))->assertOk(), $id, $body);
        $collection = $this->getJson($this->url())->assertOk()->json('data');
        $this->assertIsArray($collection);
        $this->assertCollectionRecords($collection, [$id => $body]);
        $this->deleteJson($this->url($id))->assertNoContent();
        $missing = $this->getJson($this->url($id))->assertNotFound();
        $this->assertIsArray($missing->json());
        $this->assertSame([], $this->state());
    }
}
