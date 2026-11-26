<?php
namespace FinalEvaluation;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\TestCase;

require_once __DIR__.'/Assertions.php';

class FinalReferenceTest extends TestCase
{
    // Independent oracle profile: no internal test or fixture imports.
    use RefreshDatabase;

    private static function profile(): array
    {
        return json_decode(file_get_contents(__DIR__.'/profile.json'), true, 512, JSON_THROW_ON_ERROR);
    }
    public static function cases(): array
    {
        $data = [];
        foreach (self::profile()['cases'] as $case) $data[$case['case_id']] = [$case];
        return $data;
    }
    private function table(): string { return self::profile()['spec']['resource']; }
    private function url(?int $id = null): string { return '/api/'.$this->table().($id === null ? '' : '/'.$id); }
    private function body(string $role): array { return self::profile()['fixtures'][$role]; }
    private function insert(string $role): int
    {
        return DB::table($this->table())->insertGetId($this->body($role)+[
            'created_at'=>'2026-01-02 03:04:05', 'updated_at'=>'2026-01-02 03:04:05']);
    }
    private function state(): array
    {
        return DB::table($this->table())->orderBy('id')->get()->map(fn($r)=>(array)$r)->all();
    }
    private function expected(array $case): array
    {
        $body = $case['expected'] ?? $case['payload'];
        foreach (self::profile()['spec']['fields'] as $f) {
            if ($f['type']==='integer' && array_key_exists($f['name'],$body)) $body[$f['name']] = (int)$body[$f['name']];
        }
        return $body;
    }
    private string $phase='status';
    private ?int $actualStatus=null;
    private function requestCase(string $verb, ?int $id=null, array $body=[])
    {
        $r=$this->json($verb,$this->url($id),$body);
        $this->actualStatus=$r->getStatusCode();
        return $r;
    }
    private function sequence(): void
    {
        $new=$this->body('new'); $updated=$this->body('updated');
        $this->phase='sequence.create';
        $r=$this->requestCase('POST',null,$new)->assertCreated();
        Assertions::object($r->getContent());
        $id=$r->json('data.id'); $this->assertIsInt($id);
        Assertions::record($r->getContent(),$id,$new);
        $this->phase='sequence.read';
        Assertions::record($this->requestCase('GET',$id)->assertOk()->getContent(),$id,$new);
        $this->phase='sequence.update';
        Assertions::record($this->requestCase('PUT',$id,$updated)->assertOk()->getContent(),$id,$updated);
        $this->phase='sequence.read_updated';
        Assertions::record($this->requestCase('GET',$id)->assertOk()->getContent(),$id,$updated);
        $this->phase='sequence.list';
        Assertions::collection($this->requestCase('GET')->assertOk()->getContent(),[$id=>$updated]);
        $this->phase='sequence.delete';
        $this->requestCase('DELETE',$id)->assertNoContent();
        $this->phase='sequence.missing';
        $missing=$this->requestCase('GET',$id)->assertNotFound();
        Assertions::object($missing->getContent());
        $this->assertSame([],$this->state());
    }
    #[DataProvider('cases')]
    public function test_contract(array $case): void
    {
        $this->phase='status'; $this->actualStatus=null;
        try { $this->runCase($case); }
        catch (\PHPUnit\Framework\AssertionFailedError $e) {
            $this->fail('FINAL_ASSERTION:'.$case['case_id'].':'.$this->phase.':HTTP'.($this->actualStatus ?? 0).' '.$e->getMessage());
        }
    }
    private function runCase(array $case): void
    {
        $kind=$case['kind'];
        if ($kind==='empty') {
            $r=$this->requestCase('GET')->assertOk(); $this->phase='body';
            Assertions::collection($r->getContent(),[]); $this->phase='state';
            $this->assertSame([],$this->state()); return;
        }
        if ($kind==='sequence') { $this->sequence(); return; }
        $first=$this->insert('target'); $second=$this->insert('other');
        $target=($case['target_position'] ?? 1)===2 ? $second : $first;
        $targetRole=$target===$second ? 'other' : 'target';
        $before=$this->state();
        if ($kind==='index') {
            $r=$this->requestCase('GET')->assertOk(); $this->phase='body';
            Assertions::collection($r->getContent(),[$first=>$this->body('target'),$second=>$this->body('other')]); $this->phase='state';
            $this->assertSame($before,$this->state()); return;
        }
        if ($kind==='show') {
            $r=$this->requestCase('GET',$target)->assertOk(); $this->phase='body';
            Assertions::record($r->getContent(),$target,$this->body($targetRole)); $this->phase='state';
            $this->assertSame($before,$this->state()); return;
        }
        if ($kind==='destroy') {
            $r=$this->requestCase('DELETE',$target)->assertStatus(204); $this->phase='body';
            $this->assertSame('',$r->getContent()); $this->phase='state';
            $this->assertSame(array_values(array_filter($before,fn($row)=>(int)$row['id']!==$target)),$this->state()); return;
        }
        if ($kind==='missing_id') {
            $r=$this->requestCase($case['operation'],987654,$case['payload'])->assertNotFound(); $this->phase='body';
            $this->assertSame('application/json',explode(';',$r->headers->get('Content-Type',''))[0]);
            Assertions::object($r->getContent()); $this->phase='state'; $this->assertSame($before,$this->state()); return;
        }
        $post=$case['operation']==='POST';
        $r=$this->requestCase($case['operation'],$post ? null : $target,$case['payload']);
        if ($kind==='invalid') {
            $r->assertUnprocessable(); $this->phase='body'; Assertions::object($r->getContent());
            $r->assertJsonValidationErrors([$case['field']]); $this->phase='state'; $this->assertSame($before,$this->state()); return;
        }
        $r->assertStatus($post ? 201 : 200); $this->phase='body'; Assertions::object($r->getContent()); $id=$r->json('data.id'); $this->assertIsInt($id);
        $expected=$this->expected($case);
        Assertions::record($r->getContent(),$id,$expected);
        $this->phase='state'; $this->assertDatabaseHas($this->table(),['id'=>$id]+$expected);
        $after=$this->state();
        if ($post) {
            $this->assertCount(3,$after); $this->assertNotContains($id,array_column($before,'id'));
            $this->assertSame($before,array_values(array_filter($after,fn($row)=>(int)$row['id']!==$id)));
        } else {
            $this->assertSame($target,$id); $this->assertCount(2,$after); $this->assertSame(array_values(array_filter($before,fn($row)=>(int)$row['id']!==$target)),array_values(array_filter($after,fn($row)=>(int)$row['id']!==$target)));
        }
    }
}
