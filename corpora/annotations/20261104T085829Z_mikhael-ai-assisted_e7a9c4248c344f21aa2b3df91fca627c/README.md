# Usulan ground truth: Mikhael Josua Roganda

16 anotasi telah diisi berdasarkan inspeksi kode/spec, bukti acuan Docker yang ada dan dokumentasi primer. Semua label tetap **draft_ai_assisted**. Nama pengguna dicantumkan atas instruksinya sebagai pemilik anotasi; pemeriksaan manusia belum diattestasi.

Disiapkan oleh OpenAI Codex. reviewer dan reviewed_at tetap null; blinded_to_prediction tetap false. Waktu prepared_at adalah waktu penyusunan AI, bukan waktu review manusia.

Sumber asli dan formulir anonimnya dipertahankan di C:\Perkuliahan\TA\component-evidence\20261104T082952Z_reference-evidence_26a23f11d3ab49929f39605cde0bf690. Dokumen publik menjelaskan aturan; label file proyek adalah inferensi anotasi ini, bukan ground truth milik pihak penerbit dokumentasi.

| ID | Kasus | Label draf | Bukti acuan |
|---|---|---|---|
| R001 | syn_array_valid | correct | 35/35 |
| R002 | syn_string_valid | correct | 35/35 |
| R003 | syn_syntax | problematic | UNLOADABLE_CODE |
| R004 | syn_missing_method | problematic | 32/35 |
| R005 | syn_store_status | problematic | 30/35 |
| R006 | syn_update_required | problematic | 34/35 |
| R007 | syn_missing_id | problematic | 33/35 |
| R008 | syn_wrong_delete | problematic | 33/35 |
| R009 | syn_reference_max | problematic | 33/35 |
| R010 | syn_reference_min | problematic | 33/35 |
| R011 | qwen_products_0 | problematic | 31/33 |
| R012 | qwen_products_1 | correct | 33/33 |
| R013 | qwen_books_0 | correct | 35/35 |
| R014 | qwen_inventory_items_0 | problematic | 51/57 |
| R015 | qwen_inventory_items_1 | problematic | 53/57 |
| R016 | qwen_inventory_items_2 | problematic | 53/57 |

## Dasar penilaian

### R001 — syn_array_valid

Kelima action tersedia, rules array sesuai spec, ID hilang memakai findOrFail, dan penghapusan menargetkan satu ID. Bukti acuan35/35 mendukung kesesuaian dalam kontrak/cakupan yang diperiksa.


Rujukan: [Laravel 12.x Validation](https://laravel.com/docs/12.x/validation), [Laravel 12.x Eloquent](https://laravel.com/docs/12.x/eloquent), [Laravel 12.x ResponseFactory API](https://api.laravel.com/docs/12.x/Illuminate/Routing/ResponseFactory.html), [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)

### R002 — syn_string_valid

Rules string bertanda pipa ekuivalen dengan rules array untuk kontrak ini; alur CRUD dan respons sesuai spec. Bukti acuan35/35. Label correct dibatasi kontrak dan cakupan pemeriksaan.


Rujukan: [Laravel 12.x Validation](https://laravel.com/docs/12.x/validation), [Laravel 12.x Eloquent](https://laravel.com/docs/12.x/eloquent), [Laravel 12.x ResponseFactory API](https://api.laravel.com/docs/12.x/Illuminate/Routing/ResponseFactory.html)

### R003 — syn_syntax

Label berdasarkan struktur kode dan diagnosis parser Docker, bukan asumsi bahwa semua assertion fungsional telah dieksekusi.

- Kurung kurawal penutup class hilang. Preflight lint dalam Docker membuktikan invalid_syntax; test fungsional belum dijalankan. Cakupan: internal_covered.

Rujukan: [PHP Manual: Command line options](https://www.php.net/manual/en/features.commandline.options.php)

### R004 — syn_missing_method

Tiga testcase acuan gagal pada pembacaan/ID hilang/rangkaian CRUD; ketiganya konsisten dengan satu cacat nama action.

- Action show($id) yang diwajibkan kontrak tidak tersedia karena diganti menjadi lookup($id); route yang memanggil show gagal. Cakupan: internal_covered.

Rujukan: [Laravel 12.x Controllers](https://laravel.com/docs/12.x/controllers)

### R005 — syn_store_status

Status201 wajib berasal dari spec proyek; RFC menjelaskan semantik201, bukan bukti bahwa setiap API publik harus memilih status yang sama.

- Kontrak store menetapkan201, tetapi kode mengembalikan200 setelah Book::create. Lima testcase yang melibatkan create melaporkan status tidak sesuai. Cakupan: internal_covered.

Rujukan: [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html), [Laravel 12.x ResponseFactory API](https://api.laravel.com/docs/12.x/Illuminate/Routing/ResponseFactory.html)

### R006 — syn_update_required

Satu testcase PUT_missing_title gagal; rule title pada store tetap wajib.

- Rule title pada PUT menghilangkan required. Request tanpa title diterima200, bertentangan dengan kontrak yang mewajibkan422. Cakupan: internal_covered.

Rujukan: [Laravel 12.x Validation](https://laravel.com/docs/12.x/validation)

### R007 — syn_missing_id

Dua testcase gagal dan mengarah ke pola penanganan ID hilang yang sama.

- show memakai Book::find tanpa cabang ID hilang. Objek yang tidak ditemukan dikembalikan sebagai data:null dengan200, sedangkan kontrak mewajibkan404. Cakupan: internal_covered.

Rujukan: [Laravel 12.x Eloquent](https://laravel.com/docs/12.x/eloquent)

### R008 — syn_wrong_delete

Test isolasi record dan delete ID tidak dikenal gagal. Dua efek tersebut berasal dari query delete tanpa penyaringan/pencarian ID.

- Book::query()->delete() tanpa kondisi menghapus semua buku. destroy tidak membatasi ID yang diminta dan juga tidak memeriksa keberadaan ID untuk respons404. Cakupan: internal_covered.

Rujukan: [Laravel 12.x Eloquent](https://laravel.com/docs/12.x/eloquent)

### R009 — syn_reference_max

Tetap bermasalah walaupun dapat lolos test internal. Klasifikasi reference_only dipertahankan agar kekurangan cakupan dapat muncul sebagai FN.

- Store dan update menghilangkan max:80 untuk title, sehingga judul81karakter tidak ditolak sebagaimana spec. Kedua testcase batas panjang acuan gagal; cakupan internal tidak menguji batas ini. Cakupan: reference_only.

Rujukan: [Laravel 12.x Validation](https://laravel.com/docs/12.x/validation)

### R010 — syn_reference_min

Pelanggaran reference_only dipertahankan dalam ground truth sementara, meskipun tidak dicakup test internal.

- Store dan update menghilangkan min:1 untuk pages. Nilai0 diterima, bertentangan dengan batas minimal1 pada spec. Kedua testcase nilai di bawah minimum gagal. Cakupan: reference_only.

Rujukan: [Laravel 12.x Validation](https://laravel.com/docs/12.x/validation)

### R011 — qwen_products_0

Acuan31/33: delete dan rangkaian CRUD gagal karena cacat destroy yang sama; bukan dua bug independen.

- response() tanpa argumen menghasilkan ResponseFactory. Pemanggilan setContent pada factory menimbulkan BadMethodCallException pada harness dan DELETE mendapat500, seharusnya204. Cakupan: internal_covered.

Rujukan: [Laravel 12.x ResponseFactory API](https://api.laravel.com/docs/12.x/Illuminate/Routing/ResponseFactory.html), [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)

### R012 — qwen_products_1

Perbaikan destroy memakai response()->json dengan status204; body kosong dibuktikan suite dalam Laravel yang dipakai. Rules required/tipe/batas/unique dan penanganan ID memenuhi kontrak pada33/33test. Label dibatasi cakupan tersebut.


Rujukan: [Laravel 12.x Validation](https://laravel.com/docs/12.x/validation), [Laravel 12.x ResponseFactory API](https://api.laravel.com/docs/12.x/Illuminate/Routing/ResponseFactory.html), [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)

### R013 — qwen_books_0

CRUD menggunakan validasi required/tipe/batas sesuai spec, pemeriksaan ID hilang404 dan penghapusan204. Respons json default200 pada show/update sesuai kontrak. Acuan35/35 mendukung label dalam cakupan pengujian.


Rujukan: [Laravel 12.x Validation](https://laravel.com/docs/12.x/validation), [Laravel 12.x ResponseFactory API](https://api.laravel.com/docs/12.x/Illuminate/Routing/ResponseFactory.html), [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)

### R014 — qwen_inventory_items_0

Acuan51/57: empat kasus field wajib PUT dan dua testcase yang terkena cacat destroy. Jumlah testcase gagal tidak disamakan dengan jumlah pola kesalahan.

- PUT mewajibkan label, stock, warehouse_code, dan reorder_level menurut spec. Keempat rule update tidak memuat required; empat request yang masing-masing kehilangan satu field mendapat200, seharusnya422. Ini satu pola kekurangan validasi dengan empat kasus bukti. Cakupan: internal_covered.
- Pemanggilan response()->empty() menimbulkan BadMethodCallException pada ResponseFactory yang dipakai harness. DELETE mengembalikan500 sebelum mencapai status204 yang diminta. Cakupan: internal_covered.

Rujukan: [Laravel 12.x Validation](https://laravel.com/docs/12.x/validation), [Laravel 12.x ResponseFactory API](https://api.laravel.com/docs/12.x/Illuminate/Routing/ResponseFactory.html), [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)

### R015 — qwen_inventory_items_1

Destroy sudah diperbaiki dan acuan53/57. Empat kegagalan tersisa adalah request PUT tanpa masing-masing field wajib; belum merupakan perbaikan penuh.

- PUT mewajibkan label, stock, warehouse_code, dan reorder_level menurut spec. Keempat rule update tidak memuat required; empat request yang masing-masing kehilangan satu field mendapat200, seharusnya422. Ini satu pola kekurangan validasi dengan empat kasus bukti. Cakupan: internal_covered.

Rujukan: [Laravel 12.x Validation](https://laravel.com/docs/12.x/validation)

### R016 — qwen_inventory_items_2

Byte kode identik dengan percobaan1. Bukti acuan53/57 digunakan ulang secara eksplisit; ini satu kandidat duplikat, bukan eksekusi independen tambahan.

- PUT mewajibkan label, stock, warehouse_code, dan reorder_level menurut spec. Keempat rule update tidak memuat required; empat request yang masing-masing kehilangan satu field mendapat200, seharusnya422. Ini satu pola kekurangan validasi dengan empat kasus bukti. Cakupan: internal_covered.

Rujukan: [Laravel 12.x Validation](https://laravel.com/docs/12.x/validation)

## Penggunaan sementara

Dari root proyek:

```bat
python -m critic_agent component-run corpora/annotations/20261104T085829Z_mikhael-ai-assisted_e7a9c4248c344f21aa2b3df91fca627c/corpus.json --timeout 120
python -m critic_agent component-report component-runs/NAMA_RUN --provisional
```

Gunakan run_directory yang benar dari output component-run untuk mengganti NAMA_RUN. Laporan sementara harus tetap mencantumkan bahwa label draf dibantu AI. Default reviewed-only tidak menerima label ini.

Untuk evaluasi reviewed, manusia memeriksa usulan, peninjau berbeda menilai secara independen, dan hanya kegiatan yang benar-benar selesai dicatat. Salin paket ini untuk keputusan reviewed; setelah itu jalankan prediksi baru. Paket review anonim asli tetap tersedia untuk peninjau.
