<?php

namespace Tests\Support;

use Illuminate\Support\Facades\DB;

trait ResourceFixtures
{
    private static function contract(): array
    {
        return json_decode(file_get_contents(dirname(__DIR__, 2).'/critic/contract.json'), true, 512, JSON_THROW_ON_ERROR);
    }

    private function body(string $role = 'new'): array
    {
        return self::contract()['fixtures'][$role];
    }

    private function uri(?int $id = null): string
    {
        return '/api/'.self::contract()['spec']['resource'].($id === null ? '' : '/'.$id);
    }

    private function table(): string
    {
        return self::contract()['spec']['resource'];
    }

    private function insert(string $role): int
    {
        return DB::table($this->table())->insertGetId($this->body($role) + [
            'created_at' => '2026-01-01 00:00:00', 'updated_at' => '2026-01-01 00:00:00',
        ]);
    }

    private function rows(): array
    {
        return DB::table($this->table())->orderBy('id')->get()->map(fn ($row) => (array) $row)->all();
    }

    private function assertRecord($response, int $id, array $body): void
    {
        $response->assertJsonPath('data.id', $id);
        foreach ($body as $field => $value) $response->assertJsonPath('data.'.$field, $value);
    }
}
