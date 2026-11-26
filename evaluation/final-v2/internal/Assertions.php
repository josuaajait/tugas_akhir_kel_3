<?php
namespace FinalEvaluation;

use PHPUnit\Framework\Assert as A;

// Trusted assertion code. Inspect original JSON before associative decoding.
final class Assertions
{
    public static function object(string $raw): \stdClass
    {
        try { $body = json_decode($raw, false, 512, JSON_THROW_ON_ERROR); }
        catch (\JsonException $e) { A::fail('Response must contain valid JSON: '.$e->getMessage()); }
        A::assertInstanceOf(\stdClass::class, $body, 'Response must be a JSON object');
        return $body;
    }

    public static function record(string $raw, int $id, array $expected): void
    {
        $body = self::object($raw);
        A::assertTrue(property_exists($body, 'data'));
        A::assertInstanceOf(\stdClass::class, $body->data);
        A::assertTrue(property_exists($body->data, 'id'));
        A::assertIsInt($body->data->id);
        A::assertSame($id, $body->data->id);
        foreach ($expected as $field => $value) {
            A::assertTrue(property_exists($body->data, $field), 'Missing response field '.$field);
            A::assertSame($value, $body->data->$field, 'Wrong value for '.$field);
        }
    }

    public static function collection(string $raw, array $expectedById): void
    {
        $body = self::object($raw);
        A::assertTrue(property_exists($body, 'data'));
        A::assertIsArray($body->data, 'Collection data must be a JSON array');
        A::assertCount(count($expectedById), $body->data);
        $seen = [];
        foreach ($body->data as $record) {
            A::assertInstanceOf(\stdClass::class, $record);
            A::assertTrue(property_exists($record, 'id'));
            A::assertIsInt($record->id);
            A::assertArrayHasKey($record->id, $expectedById);
            A::assertArrayNotHasKey($record->id, $seen);
            $seen[$record->id] = true;
            foreach ($expectedById[$record->id] as $field => $value) {
                A::assertTrue(property_exists($record, $field), 'Missing collection field '.$field);
                A::assertSame($value, $record->$field, 'Wrong collection value for '.$field);
            }
        }
    }
}
