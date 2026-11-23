# Audit awal evaluator untuk paket akhir — 23 November 2026

Audit menemukan dua celah assertion yang perlu ditangani pada **paket baru** sebelum A/B final. Tidak ada perubahan pada suite, source generator, image atau kandidat historis. Audit disiapkan OpenAI Codex; review manusia belum dilakukan. [Hasil dan fingerprint](final-evaluator-audit-2026-11-23.json).

## Hasil aktual

`python -m unittest discover -s tests -v` lulus **193 tes**, tanpa skip, dalam 35,172 detik. Log lokal: `work/final-evaluation-baseline-2026-11-23.log`. Ini memverifikasi baseline implementasi yang ada, bukan validitas suite akhir.

Probe menjalankan assertion respons tepercaya menggunakan dependensi lokal yang sudah ada. Probe tidak memuat aplikasi Laravel, database, atau controller kandidat. Fixture dua record: ID 11/title First/pages 40 dan ID 12/title Second/pages 80.

| Respons buatan | Assertion respons internal generik | Assertion koleksi acuan resource |
|---|---|---|
| Dua record sesuai fixture | Terima | Terima |
| Dua record dengan urutan dibalik | Terima | Terima |
| Nilai title/pages tertukar antar-ID | **Terima, celah** | Tolak |
| Field record hilang | Tolak | Tolak |
| ID duplikat | Tolak | Tolak |
| `data` berupa objek JSON berkunci `"0"`, `"1"` | Tidak diperiksa pada probe ini | **Terima, celah** |

1. `resource_templates/ResourceContractTest.php::test_index_returns_records_without_mutation` memakai `assertJsonFragment`. Keberadaan fragmen tidak mengikat seluruh field ke record dengan ID yang sama. Probe mengisolasi assertion respons; tidak menyatakan hasil loop Docker. Snapshot DB tidak akan membedakan kesalahan yang hanya menukar nilai respons.
2. `evaluation/resource-reference/ResourceReferenceTest.php::assertCollectionRecords` sudah mengikat record ke ID, tetapi menerima hasil `response->json('data')` yang telah didekode asosiatif. Objek JSON berkunci berurutan menjadi PHP array list; `array_is_list` tidak lagi membuktikan bentuk array pada JSON asli. Pemeriksaan bentuk perlu dilakukan sebelum informasi objek/list hilang.

## Reproduksi probe

Dari root proyek di PowerShell, jalankan source tepercaya berikut melalui stdin PHP. Tidak ada controller kandidat yang dieksekusi di host.

```powershell
@'
<?php
require 'harness/laravel/vendor/autoload.php';
require 'evaluation/resource-reference/ResourceReferenceTest.php';
(new PHPUnit\TextUI\Configuration\Builder)->build(['audit', '--no-configuration']);
$expected = [11 => ['title'=>'First','pages'=>40],12=>['title'=>'Second','pages'=>80]];
$good = [['id'=>11,'title'=>'First','pages'=>40],['id'=>12,'title'=>'Second','pages'=>80]];
$cases = ['valid'=>$good,'reversed'=>array_reverse($good),
 'swapped_values'=>[['id'=>11,'title'=>'Second','pages'=>80],['id'=>12,'title'=>'First','pages'=>40]],
 'missing_fields'=>[['id'=>11,'title'=>'First'],['id'=>12,'pages'=>80]],'duplicate'=>[$good[0],$good[0]]];
$class = new ReflectionClass(Evaluation\ResourceReferenceTest::class);
$instance = $class->newInstanceWithoutConstructor();
$method = $class->getMethod('assertCollectionRecords');
$results = [];
foreach ($cases as $name=>$records) {
 $response=Illuminate\Testing\TestResponse::fromBaseResponse(new Illuminate\Http\JsonResponse(['data'=>$records]));
 try {
  $response->assertOk()->assertJsonCount(2,'data');
  $response->assertJsonFragment(['id'=>11]+$expected[11]);
  $response->assertJsonFragment(['id'=>12]+$expected[12]);
  $internal='accepted';
 } catch (PHPUnit\Framework\AssertionFailedError $e) {$internal='rejected';}
 try {$method->invoke($instance,$response->json('data'),$expected);$reference='accepted';}
 catch (PHPUnit\Framework\AssertionFailedError $e) {$reference='rejected';}
 $results[$name]=['internal_response_assertions'=>$internal,'reference_collection_assertion'=>$reference];
}
$raw='{"data":{"0":{"id":11,"title":"First","pages":40},"1":{"id":12,"title":"Second","pages":80}}}';
$response=Illuminate\Testing\TestResponse::fromBaseResponse(new Symfony\Component\HttpFoundation\Response($raw,200,['Content-Type'=>'application/json']));
try {$method->invoke($instance,$response->json('data'),$expected);$outcome='accepted';}
catch (PHPUnit\Framework\AssertionFailedError $e) {$outcome='rejected';}
$results['numeric_keyed_json_object']=['reference_collection_assertion'=>$outcome,
 'raw_json_data_type'=>gettype(json_decode($raw)->data),'decoded_associative_type'=>gettype($response->json('data'))];
echo json_encode($results, JSON_PRETTY_PRINT),PHP_EOL;
'@ | php
```

## Batas dan tindak lanjut

Doctor dan `docker version` mendeteksi Client 29.9.2, tanpa Server: pipe `dockerDesktopLinuxEngine` tidak ditemukan. Validasi fungsional controller acuan maupun mutasi di Docker **belum dijalankan pada sesi ini**. Ini bukan bukti Docker belum terpasang. Ollama juga tidak dapat diakses dari sandbox pada pemeriksaan ini; model tidak diperlukan untuk memvalidasi evaluator.

Evaluator resource lama hanya menerima spec books/inventory yang cocok persis. Menambah lima soal baru memerlukan paket evaluator baru, fixture acuan yang disusun terpisah, matriks per aturan, kontrol benar dan mutasi target. Pertahankan fingerprint lama yang dicatat dalam JSON audit. Koreksi assertion serta validasi baru masuk paket berversi baru, sebelum pembekuan dan tanpa keluaran Qwen final. Rancangan: [paket soal dan validasi evaluator](../superpowers/specs/2026-11-23-final-evaluation-package-design.md).
