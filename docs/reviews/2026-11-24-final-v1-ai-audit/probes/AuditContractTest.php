<?php
namespace Audit;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use Tests\TestCase;
class AuditContractTest extends TestCase {
    use RefreshDatabase;
    private function seedTwo(): array {
        $stamp=['created_at'=>'2026-01-02 03:04:05','updated_at'=>'2026-01-02 03:04:05'];
        $first=DB::table('categories')->insertGetId(['name'=>'Furniture','description'=>'Meeting furnishings']+$stamp);
        $second=DB::table('categories')->insertGetId(['name'=>'Hardware','description'=>'Workshop parts']+$stamp);
        return [$first,$second];
    }
    public function test_show_second_id_returns_second_record(): void {
        [$first,$second]=$this->seedTwo();
        $r=$this->getJson('/api/categories/'.$second)->assertOk();
        $this->assertSame($second,$r->json('data.id'),'Requested second ID, got another record');
        $this->assertSame('Hardware',$r->json('data.name'));
    }
    public function test_update_second_id_preserves_first_record(): void {
        [$first,$second]=$this->seedTwo();
        $before=(array)DB::table('categories')->where('id',$first)->first();
        $r=$this->putJson('/api/categories/'.$second,['name'=>'Equipment','description'=>'Lab equipment'])->assertOk();
        $this->assertSame($second,$r->json('data.id'),'Update must return requested second ID');
        $this->assertDatabaseHas('categories',['id'=>$second,'name'=>'Equipment','description'=>'Lab equipment']);
        $this->assertSame($before,(array)DB::table('categories')->where('id',$first)->first());
    }
    public function test_destroy_second_id_preserves_first_record(): void {
        [$first,$second]=$this->seedTwo();
        $before=(array)DB::table('categories')->where('id',$first)->first();
        $this->deleteJson('/api/categories/'.$second)->assertNoContent();
        $this->assertDatabaseMissing('categories',['id'=>$second]);
        $this->assertSame($before,(array)DB::table('categories')->where('id',$first)->first());
    }
    public function test_store_one_character_strings_is_valid(): void {
        $this->seedTwo();
        $r=$this->postJson('/api/categories',['name'=>'A','description'=>'B'])->assertCreated();
        $this->assertDatabaseHas('categories',['id'=>$r->json('data.id'),'name'=>'A','description'=>'B']);
    }
    public function test_update_one_character_strings_is_valid(): void {
        [$first,$second]=$this->seedTwo();
        $r=$this->putJson('/api/categories/'.$second,['name'=>'A','description'=>'B'])->assertOk();
        $this->assertSame($second,$r->json('data.id'));
        $this->assertDatabaseHas('categories',['id'=>$second,'name'=>'A','description'=>'B']);
    }
}
