# Audit assertion products/internal — 12 November 2026

## Perbaikan paket internal v2 — 19 November 2026

Assertion `index` sekarang membaca JSON dengan membedakan objek dan array. Setiap ID integer harus cocok dengan satu record yang diharapkan dan setiap nilai `name`, `price` dan `sku` dibandingkan pada record tersebut. Dua fixture memakai nilai berbeda. Urutan bebas, field tambahan diperbolehkan, dan snapshot database tetap diperiksa.

Probe regresi `tests/test_products_collection.py` menerima dua respons valid dan menolak delapan respons invalid, termasuk objek sebagai pengganti array, ID duplikat, ID asing dan ID bertipe string. Probe hanya menjalankan assertion tepercaya dengan respons buatan. Jumlah kasus Docker tetap 14 internal dan 21 readiness.

SHA-256 sumber `ProductsContractTest.php` pada checkout yang diuji adalah `7263f17539f11086c0d3b135510bd1a1ef48561da66e3313c5302b80fec21c8f`. Gunakan tag baru `critic-laravel:products-internal-v2` dan catat image ID aktual. Hasil lama merujuk image ID di arsip masing-masing.

Audit juga menemukan penggunaan fragmen pada koleksi evaluator acuan products. Kelemahan tersebut masih terbuka. Paket dan bukti acuan v1 tetap menjadi bahan review yang dilengkapi keterbatasan ini. Perluasan validasi internal untuk null/kosong, tipe, batas dan unique serta bentuk respons lain tetap merupakan pekerjaan cakupan sebelum pembekuan.

### Verifikasi Docker

Build v2 menghasilkan image `sha256:3336feea72518efffcac6dc48d87eee65a78aa502c08c6d07393c82212ec90e4`. Readiness lulus 21/21. Fixture buatan `work/products-swapped-index.php` menukar SKU di respons tanpa menyimpan perubahan ke database. File kandidat pada kedua run memiliki input yang sama dan dijalankan melalui runner Docker.

| Image | Hasil fixture | Arsip di `runs/pilot-2026-11-19/products/regression/` |
|---|---|---|
| Legacy `27b24e706415…` | 14/14, PASSED_INTERNAL | `critic-4c3fecc3c6e54db09ab996c8875a5dd4` |
| v2 `3336feea7251…` | 13/14, FAILED_INTERNAL pada assertion index | `critic-0577a813f5e04668a1db3bacf0cdf0d7` |

Upaya readiness sebelum ekspor image selesai tersimpan sebagai ERROR/image_unavailable di folder preflight. Pengulangan setelah build menghasilkan READY. Seluruh 164 tes Python lulus.

## Ruang lingkup dan hasil

Audit pada commit `eb55eac` memetakan `ProductsContractTest.php` terhadap PRD v1.3 §9.1, FR-08/09 dan §12.1. Pemeriksaan kode dan probe assertion selesai. Ditemukan celah pengikatan field ke record pada respons index. Gerbang cakupan FR-09 masih terbuka sampai perbaikan dan verifikasi suite baru selesai.

Audit disiapkan OpenAI Codex. Review manusia independen belum dilakukan. Suite, controller, arsip eksperimen, versi aplikasi dan image tidak diubah dalam audit ini.

## Pemisahan suite

`harness/laravel/phpunit.xml` menempatkan `ProductsContractTest` dalam suite Internal dan `ProductsEdgeTest` dalam ReferenceReadiness. Kandidat mendapat 14 kasus internal, terdiri atas lima operasi sukses, enam omitted-required POST/PUT dan tiga missing-ID. Tujuh kasus Edge hanya menambah readiness menjadi 21. Lulus readiness tidak memberikan cakupan tambahan kepada kandidat.

## Matriks assertion terhadap kontrak

| Kewajiban | Assertion internal saat ini | Penilaian |
|---|---|---|
| Index 200, `data` berisi dua record, urutan bebas | `assertOk`, `assertJsonCount`, dua `assertJsonFragment` | Parsial. Jumlah dan fragmen diperiksa, tetapi field tidak terikat pada ID/record yang sama. |
| Semua field tiap record index sesuai fixture | Fragmen pertama memuat id/name/price/sku, kedua hanya id/sku | Celah terbukti. Field record kedua bisa hilang/salah. SKU bisa tertukar. |
| Index tidak mengubah data | Snapshot seluruh tabel sebelum/sesudah | Tercakup untuk fixture dua record. |
| Store 201, ID integer dan field respons sesuai input | Status, tiga JSON path, `assertIsInt(id)` | Tercakup untuk payload valid yang disediakan. |
| Store menambah tepat satu record dan menjaga record lain | DatabaseHas dengan ID/seluruh field, count 2, snapshot record lain | Tercakup. |
| Show 200 dan record target lengkap | JSON path ID/name/price/sku | Tercakup untuk target fixture. |
| Show tidak mengubah data | Snapshot seluruh tabel | Tercakup. |
| Update 200 dan target respons sesuai input | JSON path ID/seluruh field | Tercakup untuk payload yang mengganti semua nilai. |
| Update hanya mengubah target | DatabaseHas, count 2, snapshot record lain | Tercakup. |
| Destroy 204/body kosong, hanya target terhapus | `assertNoContent`, DatabaseMissing, count 1, snapshot record lain | Tercakup. |
| Required POST/PUT untuk name/price/sku | Enam vektor menghilangkan satu field, 422 dan validation errors, snapshot tabel | Tercakup untuk field yang dihilangkan. Null/string kosong belum diuji. |
| Validasi string/integer/min/max/unique | Tidak ada pada Internal | Belum tercakup internal. Sebagian ada pada Edge readiness, sehingga tidak boleh dihitung sebagai deteksi kandidat. |
| PUT mempertahankan SKU unik milik target | Hanya Edge | Belum tercakup internal. |
| Missing-ID show/update/destroy dengan payload PUT valid | 404, Content-Type JSON, `assertIsArray(json)`, snapshot tabel | Status/header/preservasi tercakup. Objek JSON belum dibedakan dari array JSON. |
| Bentuk objek JSON dan bentuk record | Pemeriksaan path/fragmen | Parsial. Jenis objek/list dan ID integer konsisten belum ditegaskan pada semua operasi. |
| Koleksi kosong dan fixture dengan nilai berbeda | Tidak ada | Belum diuji. Kedua fixture index memakai name/price sama, sehingga salah atribusi kedua field tidak terlihat. |

Timestamp tambahan dan perubahan urutan record harus tetap diterima sesuai PRD. Matriks ini menyatakan cakupan vektor yang benar-benar ada, bukan jaminan atas seluruh kemungkinan implementasi.

## Bukti probe assertion

Probe tepercaya membentuk `Illuminate\Testing\TestResponse` dari JSON buatan dan menjalankan rangkaian assertion index yang sama persis. PHPUnit diinisialisasi hanya untuk pemformatan assertion. Tidak ada aplikasi Laravel/controller/kandidat yang dijalankan. Snapshot database tidak dipanggil karena probe mengisolasi lapisan respons. Pelanggaran respons ini dapat terjadi tanpa perubahan database.

Perintah dari root proyek adalah `php work/products-assertion-audit/probe.php`. Exit code pada 12 November 2026 adalah 0.

| Respons | Hasil assertion legacy | Hasil menurut kontrak |
|---|---|---|
| Dua record valid | accepted | Terima |
| Dua record valid dibalik urutannya | accepted | Terima |
| SKU BOOK-1 dan OTHER tertukar antar-ID | accepted | Tolak |
| Record kedua kehilangan name dan price | accepted | Tolak |
| ID duplikat menggantikan ID kedua | rejected | Tolak |
| Record kedua name=WRONG dan price=-10 | accepted | Tolak |
| Field yang diharapkan tersebar di dua record yang tidak lengkap | accepted | Tolak |

Akar masalah terlihat pada `Illuminate/Testing/AssertableJsonString::assertFragment` di vendor Laravel. Helper mencari pasangan key/value dalam JSON yang diserialisasi. Keberadaan pasangan tersebut tidak memastikan semua pasangan berada pada objek record yang sama. `assertJsonCount` hanya menambah pemeriksaan jumlah elemen.

Probe tersedia di lampiran bawah agar bukti dapat direproduksi setelah clone karena work/ diabaikan Git.

## Tindak lanjut sebelum pembekuan

1. Buat paket suite baru dengan assertion index yang memetakan setiap record berdasarkan ID integer unik, memastikan himpunan ID sama, lalu membandingkan semua field per ID. Pakai name/price/sku berbeda antarfixture, terima urutan bebas dan field tambahan.
2. Tambahkan regresi yang menerima dua kontrol valid dan menolak empat respons pelanggaran di atas, ID duplikat, ID asing dan tipe ID salah.
3. Tegaskan bentuk objek/list sesuai kontrak pada respons yang relevan. Putuskan dan dokumentasikan cakupan validasi kandidat, termasuk null/kosong, tipe/batas/unique dan own-unique. Penambahan cakupan harus memakai versi paket baru.
4. Koordinasikan fingerprint dan build baru serta verifikasi Docker readiness dan kandidat pada suite baru. Hasil historis 14/14 dan 21/21 tetap merujuk suite lama.
5. Review manusia terhadap assertion dan matriks sebelum pembekuan. Hasil audit ini tidak mengesahkan label atau suite final.

Docker belum tersedia pada pemeriksaan lingkungan sesi ini. Tidak ada hasil live suite baru atau rerun kandidat yang diklaim.

## Identitas sumber

SHA-256 sebelum audit

- ProductsContractTest.php `0355553ee1c03aab6c95ba6532c50421f34d92b77a02b0c05beecd17896313e7`
- ProductsEdgeTest.php `bd7b05852ca858d1b62a75569262e4202cc68ec3ed0a173dc36f8449e18cc54c`
- phpunit.xml `897b0c1f7f91b65e98fcd738d29f15c6b1d04a8e588f42011168bf38436b1f1e`

## Lampiran probe yang dapat direproduksi

Simpan sebagai `work/products-assertion-audit/probe.php` dari root proyek yang memiliki vendor Laravel terkunci.

```php
<?php
require __DIR__.'/../../harness/laravel/vendor/autoload.php';
(new PHPUnit\TextUI\Configuration\Builder)->build(['assertion-probe', '--no-configuration']);
function legacyIndexAssertions(array $records): void
{
    $response = Illuminate\Testing\TestResponse::fromBaseResponse(
        new Illuminate\Http\JsonResponse(['data' => $records], 200)
    );
    $response->assertOk()->assertJsonCount(2, 'data')
        ->assertJsonFragment(['id' => 1, 'name' => 'Book', 'price' => 120, 'sku' => 'BOOK-1'])
        ->assertJsonFragment(['id' => 2, 'sku' => 'OTHER']);
}
$good = [
    ['id' => 1, 'name' => 'Book', 'price' => 120, 'sku' => 'BOOK-1'],
    ['id' => 2, 'name' => 'Book', 'price' => 120, 'sku' => 'OTHER'],
];
$cases = ['valid' => $good, 'valid_reordered' => array_reverse($good)];
$cases['swapped_sku'] = $good;
$cases['swapped_sku'][0]['sku'] = 'OTHER';
$cases['swapped_sku'][1]['sku'] = 'BOOK-1';
$cases['second_missing_fields'] = [$good[0], ['id' => 2, 'sku' => 'OTHER']];
$cases['duplicate_id'] = [$good[0], array_replace($good[1], ['id' => 1])];
$cases['second_wrong_fields'] = [$good[0], array_replace($good[1], ['name' => 'WRONG', 'price' => -10])];
$cases['split_fields'] = [
    ['id' => 1, 'name' => 'Book', 'sku' => 'OTHER'],
    ['id' => 2, 'price' => 120, 'sku' => 'BOOK-1'],
];
foreach ($cases as $name => $records) {
    try {
        legacyIndexAssertions($records);
        $results[$name] = 'accepted';
    } catch (PHPUnit\Framework\AssertionFailedError $error) {
        $results[$name] = 'rejected';
    }
}
echo json_encode($results, JSON_PRETTY_PRINT).PHP_EOL;
```
