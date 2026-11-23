# Rancangan paket soal CRUD dan validasi evaluator akhir

Tanggal: 23 November 2026. Status: **DISETUJUI UNTUK IMPLEMENTASI** melalui pesan pengguna “oke lanjut implementasi”, belum beku dan belum siap A/B final. Disiapkan OpenAI Codex. Pengguna memilih pendekatan **lima soal baru dengan evaluator terpisah** serta menyetujui kelanjutan implementasi setelah penjelasan kelima soal. Tidak ada klaim review assertion/label manusia.

## Tujuan dan batas tahap ini

Menyiapkan lima soal yang tidak dipakai pada pilot products/books/inventory, serta bukti bahwa evaluator menerima controller benar dan menolak pelanggaran kontrak yang dituju. Tahap ini menutup bahan teknis gerbang PRD §12.6.1/3/4. Paket ditujukan untuk rencana tersimpan 5 spesifikasi × 4 pengulangan = 20 pasangan A/B, dengan 40 cabang dan maksimal 140 panggilan model logis.

Luaran tahap ini: JSON spesifikasi, uraian soal, fixture internal dan acuan terpisah, matriks assertion per vektor, controller kontrol benar, mutasi target, image dan arsip validasi, serta formulir review manusia kosong. **Pembuatan keluaran Qwen final, pembekuan resmi, pelaksanaan 20 pasangan dan agregasi akhir merupakan tahap lanjutan setelah bahan ini lolos.** Jangan menganggap validasi teknis sebagai seluruh gerbang M3 terpenuhi.

## Pendekatan yang dipilih

1. **Lima soal baru, evaluator terpisah — dipilih pengguna.** Menambah pekerjaan penulisan fixture dan validasi, tetapi menjaga pemisahan spesifikasi dari pilot dan memberi variasi susunan field.
2. Tiga soal pilot + dua baru. Lebih cepat memanfaatkan image lama, tetapi tiga soal sudah dipakai pengembangan dan harus dilaporkan sebagai pengulangan development.
3. Generator acuan otomatis langsung dari generator internal. Tidak dipilih karena fixture dan kesalahan generator yang sama dapat menghasilkan kesepakatan semu antara pemeriksa dan acuan.

Kelima soal masih satu keluarga CRUD skalar. Nama domain baru tidak menjamin independensi semantik atau keterwakilan aplikasi Laravel secara umum. Paket ini belum pernah dipakai menghasilkan kandidat final; jangan mengklaim paket dibutakan terhadap pengembang atau seluruh prosedur evaluasi komponen selesai.

## Lima soal yang diusulkan

Semua field **required pada POST dan PUT**. PUT mengganti seluruh field yang didefinisikan; bukan PATCH. `string` dan `integer` mengikuti perilaku validasi Laravel yang dikunci. Nilai integer 0 sah bila min:0; null/kosong tetap invalid. Tidak menambah aturan strict JSON integer, regex, email, enum, foreign key, autentikasi, sorting atau pagination.

| Slot / spec_id | Resource / model / controller | Field dan aturan tambahan di luar required/type | Variasi |
|---|---|---|---|
| S1 / `final_categories_v1` | categories / Category / CategoryController | name:string max:48; description:string max:160 | 2 string, tanpa unique |
| S2 / `final_rooms_v1` | rooms / Room / RoomController | label:string max:40; capacity:integer min:1 max:500 | String + integer positif |
| S3 / `final_assets_v1` | assets / Asset / AssetController | asset_code:string min:3 max:20 unique:assets,asset_code; name:string max:80; value:integer min:0 max:1000000 | Panjang minimum string, unique dan nilai nol |
| S4 / `final_courses_v1` | courses / Course / CourseController | course_code:string max:12 unique:courses,course_code; credits:integer min:1 max:6; quota:integer min:0 max:200 | Satu string unique + dua integer dengan rentang berbeda |
| S5 / `final_shipments_v1` | shipments / Shipment / ShipmentController | tracking_code:string min:6 max:24 unique:shipments,tracking_code; reference_code:string max:20 unique:shipments,reference_code; quantity:integer min:1 max:5000; priority:integer min:1 max:5; note:string max:120 | 5 field, dua unique independen |

Masing-masing spec_version `1.0`, terikat byte/hash sendiri. Paket `final-v1` berbeda dari versi aplikasi `0.5.0` dan protokol komponen `1.0`. Kandidat hanya satu berkas controller. Route/model/migration disediakan sebagai infrastruktur tetap. Kontrak public method, Request dan ID skalar mengikuti PRD §9.1.1.

Respons: index 200 dengan objek JSON berisi data array; store 201, show/update 200 dengan data objek berisi ID integer serta semua field; destroy 204 dengan body kosong; unknown-ID GET/PUT/DELETE 404 objek JSON; input invalid 422 objek JSON dengan errors pada field yang diuji. Urutan koleksi bebas; field/timestamp tambahan diterima. Bentuk dan nilai respons diperiksa bersama efek pada database dan record pembanding.

## Cakupan internal dan acuan

Pertahankan kebijakan PRD §12.1: internal menguji lima CRUD sukses, omitted-required tiap field pada POST/PUT, dan tiga missing-ID. Perbaiki ketepatan assertion yang memang sudah dimaksudkan kontrak; jangan memperluas tipe/min/max/unique ke feedback internal.

| Slot | Field | Kasus internal kandidat yang direncanakan (`8 + 2N`) |
|---|---:|---:|
| S1 | 2 | 12 |
| S2 | 2 | 12 |
| S3 | 3 | 14 |
| S4 | 3 | 14 |
| S5 | 5 | 18 |

Readiness tambahan tetap hanya untuk controller tepercaya. Jumlah acuan ditetapkan dari enumerasi aktual test/dataset dan dicocokkan dengan matriks, bukan disalin dari angka 33/35/57 development.

Acuan mencakup setiap field pada kedua operasi: dihilangkan, null, kosong/whitespace yang ditolak required, input tipe salah yang jelas (array/objek untuk string, teks nonangka/pecahan untuk integer), setiap batas min/max invalid satu langkah di luar serta valid tepat di batas, dan setiap unique melawan record lain. Sertakan kontrol integer 0 pada min:0 dan integer negatif hanya bila kontrak mengizinkan; kelima soal ini tidak mengizinkan integer negatif. Nilai angka dalam string yang diterima validator Laravel tidak boleh ditolak semata karena JSON string. Penanganan middleware tetap sesuai base Laravel yang dikunci; tidak menambah middleware khusus.

Untuk unique, uji PUT mempertahankan nilai sendiri, mengganti menjadi nilai baru, dan collision dengan tetangga. S5 menguji kedua constraint secara terpisah, dengan nilai field unique lain tetap valid. Bila string memakai min positif, uji panjang tepat minimum dan satu di bawah minimum, terpisah dari kasus required kosong. Fixture independen harus memenuhi semua aturan dan memakai nilai berbeda antar-record/field agar salah atribusi terdeteksi.

Acuan juga menguji koleksi kosong, dua record dan urutan terbalik, pengikatan nilai ke ID, isolasi target/tetangga pada write/delete, preservasi seluruh data pada read/rejected request, dan rangkaian create/read/update/read/list/delete/read-missing. Pemeriksaan JSON asli membedakan array dan object sebelum decoding asosiatif menghilangkan informasi bentuk.

Satu baris matriks untuk setiap operasi × field × vektor, dengan rule_id, fixture/payload, expected status/body/state, ID test internal/acuan, cakupan, positive_control_id, negative_control_id, hash dan hasil validasi. Tipe/min/max/unique serta null/empty yang tidak diuji internal berlabel `reference_only`. Semua baris masuk pelaporan, termasuk false negative jika Critic tidak mendeteksinya.

## Struktur dan kompatibilitas

Simpan paket baru di `evaluation/final-v1/`: specs, uraian soal, internal, reference, profiles, controls, mutants, traceability dan review. Raw execution masuk direktori UUID di `evaluations/final-validation/`; ringkasan dan manifest relatif yang diperlukan teammate ikut Git. Jangan menaruh assertion/fixture acuan di image internal atau mengimpor generator fixture internal dari suite acuan.

Sumber legacy `resources.py`, `resource_templates/*`, `resource_reference.py`, `evaluation/resource-reference/*` dan paket products tidak diubah pada tahap ini. [Audit baseline dan fingerprint](../../evidence/final-evaluator-audit-2026-11-23.json) menjadi acuan regresi. Perubahan pada berkas tersebut dapat mengubah hash suite lama; gunakan modul dan template paket baru. Versi aplikasi tetap `0.5.0`.

Bangun scaffold final melalui adaptor terpisah: boleh memakai renderer scaffold legacy sebagai infrastruktur, tetapi assertion internal final, contract hash, metadata tahap dan konfigurasi harus diganti secara eksplisit dan diikat ke byte paket final. Jangan mengklaim fingerprint legacy untuk image dengan assertion berbeda. Runner final memverifikasi package/spec/hash/count/image sendiri, tidak menyamarkan diri sebagai ResourceDockerRunner legacy. Image memakai tag baru khusus final-v1/spec/role; ID aktual dipin pada validasi.

Builder boleh menentukan pembagian modul, nama helper dan format serialisasi yang paling kecil. Harus ada entry point CLI validasi baru yang menyatakan paket final-v1 secara eksplisit dan tidak memanggil Ollama. Nama command akan didokumentasikan sesudah benar-benar tersedia. Jangan mengganti perilaku default command development atau memonkeypatch konstanta global untuk memilih suite. Adaptor menuju `run-ab` dikerjakan kemudian: fungsi saat ini hard-coded ke evaluator books/inventory dan mencatat stage development, sehingga belum dapat menjalankan lima soal baru sebagai eksperimen final.

## Validasi yang harus dihasilkan

1. Validasi semua spec terhadap kontrak JSON dan batas generator; lint scaffold, assertion dan kontrol tepercaya. Verifikasi fixture valid, distinct dan independen dari fixture internal. Enumerasi semua testcase/dataset dan cocokkan satu-ke-satu dengan matriks.
2. Probe assertion menerima JSON valid, urutan bebas dan field ekstra; menolak field tertukar, hilang, ID duplikat/asing/string, data object berkunci angka yang menyerupai array, record array yang menyerupai object, dan bentuk respons invalid. Probe hanya menguji assertion; bukan pengganti Docker.
3. Siapkan dua gaya controller benar per spec, ditulis dari kontrak: gaya Eloquent dan gaya implementasi ekuivalen dengan pencarian/response eksplisit. Keduanya bukan keluaran Qwen penelitian. Seluruh test internal/acuan harus lulus di Docker dengan DB baru. Kontrol kedua mengurangi risiko evaluator terlalu mengikat satu gaya kode.
4. Siapkan mutasi tunggal terhadap kontrol benar untuk setiap kewajiban yang dipetakan: status CRUD, record/field respons salah, target salah, no-write/extra-write, body destroy, unknown-ID, omitted-required per field/operasi, dan setiap rule tipe/batas/unique. Tambahkan mutasi over-rejection yang menolak nilai batas sah, termasuk 0, serta own-unique. Semua mutasi tersimpan, punya diff dan hash; tidak mengedit kandidat/model archive.
5. Suatu mutasi dinyatakan terdeteksi hanya bila testcase target yang dicatat gagal dengan bukti assertion/HTTP/data sesuai maksud. Kegagalan readiness, syntax tak sengaja, timeout, test tidak selesai atau kegagalan lain saja tidak boleh dihitung sebagai keberhasilan deteksi. Mutasi reference_only harus lulus suite internal bila hanya melanggar aturan di luar cakupannya; bila tidak, selidiki interaksi dan jangan ubah label untuk menaikkan hasil. Probe sintaks sengaja boleh terpisah sebagai pemeriksaan runner, bukan pengganti mutasi fungsional.
6. Ulangi pemeriksaan kontrol benar dan subset kontrol negatif yang dipetakan pada input/image/spec sama untuk membuktikan kestabilan hasil, bandingkan identitas testcase dan outcome; abaikan waktu/path UUID. Simpan semua ERROR/retry ke folder baru. Cakupan assertion yang tidak stabil tetap belum tervalidasi.
7. Ringkasan menyebut planned/executed/pass/fail/unknown untuk kontrol dan setiap mutasi, seluruh alasan, suite/image/spec/source/control hashes serta tautan raw logs/JUnit. Sukses teknis mensyaratkan semua kontrol benar diterima, semua target negatif terdeteksi, seluruh matriks terhubung, tanpa kasus belum dapat dinilai. Jangan menggunakan jumlah mutant/test sebagai confusion matrix Critic atau jumlah bug penelitian independen.

Runtime tetap Laravel 12.70.2/PHPUnit 11.5.57 terkunci. Kandidat/kontrol fungsional hanya dieksekusi di Docker nonroot, network none, root read-only, satu controller read-only, DB/container baru, resource/output/time limit dan cleanup UUID milik sendiri. Tidak ada mount repo/home/socket, instalasi sistem, atau prune. PHP host hanya lint/tokenizer/probe assertion tepercaya.

## Review, status dan urutan setelah validasi

Formulir review menyimpan prepared_by=OpenAI Codex, human_author=null, reviewer=null, reviewed_at=null dan status pending sampai kegiatan manusia nyata dicatat. Jangan mengisi nama anggota atau tanggal sebagai bukti telah memeriksa. Setiap aturan/assertion dan keputusan cakupan ditinjau silang sebelum pembekuan; kelulusan tes bukan pengesahan manusia.

Rencana seed/order 20 pasangan pada `docs/evidence/semhas-m4-balanced-plan.json` dipertahankan sebagai draf historis. Setelah validasi teknis dan review, buat versi manifest baru yang mengikat S1–S5 ke path/hash/image aktual. Suhu 0,2 merupakan usulan berdasarkan keragaman pilot; digest model, opsi konteks/output, timeout dan perangkat aktual masih perlu dikunci sebelum final. Jangan memilih ulang soal atau suhu berdasarkan hasil A/B akhir atau mengharuskan calon kode awal gagal.

Tahap lanjutan berurutan: review dan keputusan P-06/P-07/K2; integrasi paket final ke run-ab dan agregator per spesifikasi/kondisi; manifest beku dan pemeriksaan integritas/kelengkapan; eksekusi semua 20 pasangan; pelaporan dengan ERROR, retry, duplikat dan penyebut nol. Korpus komponen dan review label independen tetap pekerjaan tersendiri; lima soal baru tidak otomatis menyelesaikan gerbang itu.

## Bukti dan kendala sesi ini

Baseline aktual 193 tes Python lulus tanpa skip dalam 35,172 detik. Probe assertion membuktikan internal generik menerima field tertukar dan acuan resource menerima object data berkunci angka. [Audit reproduktif](../../evidence/final-evaluator-audit-2026-11-23.md). Tidak ada suite final yang sudah dibangun atau controller yang sudah diuji secara fungsional dalam tahap rancangan.

Docker Client tersedia, Server belum tersedia pada endpoint Linux (pipe tidak ditemukan). Setelah rancangan disetujui, penulisan paket dan verifikasi lokal bisa berlanjut; validasi fungsional memerlukan Docker Desktop Linux aktif. Jika endpoint kemudian aktif tetapi akses ditolak, perlakukan sebagai masalah izin sandbox tersendiri. Kegagalan lingkungan tidak boleh diubah menjadi kegagalan kandidat atau validasi sukses.

## Hasil implementasi

Implementasi dan validasi teknis selesai pada23November2026:218tes Python lulus dan648/648 pengamatan Docker sesuai harapan pada hash sumber akhir. Bagian kendala di atas merekam kondisi saat rancangan dibuat. Hasil aktual, percobaan gagal yang dipertahankan dan batas kesiapan A/B ada pada [bukti final-v1](../../evidence/final-v1-validation-2026-11-23.md). Paket tetap belum beku; review manusia dan integrasi A/B final masih terbuka.
