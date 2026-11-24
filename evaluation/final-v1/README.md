# Paket soal CRUD dan validasi evaluator final-v1

Paket ini mengimplementasikan rancangan yang disetujui pada 23 November 2026. Statusnya **persiapan sebelum pembekuan**, bukan hasil A/B atau pengesahan review manusia. Tidak ada panggilan Qwen dalam validasi evaluator.

| Soal | Model / controller | Field (semua required pada POST dan PUT) | Internal / acuan | Kontrol benar / mutasi |
|---|---|---|---:|---:|
| [categories](specs/categories.json) | Category / CategoryController | name string max48; description string max160 | 12 / 42 | 2 / 39 |
| [rooms](specs/rooms.json) | Room / RoomController | label string max40; capacity integer 1–500 | 12 / 50 | 2 / 44 |
| [assets](specs/assets.json) | Asset / AssetController | asset_code string panjang3–20 unique; name string max80; value integer0–1000000 | 14 / 73 | 2 / 62 |
| [courses](specs/courses.json) | Course / CourseController | course_code string max12 unique; credits integer1–6; quota integer0–200 | 14 / 77 | 2 / 63 |
| [shipments](specs/shipments.json) | Shipment / ShipmentController | tracking_code string panjang6–24 unique; reference_code string max20 unique; quantity integer1–5000; priority integer1–5; note string max120 | 18 / 116 | 2 / 91 |
| Total | 5 spesifikasi | Satu resource skalar per soal | **70 / 358** | **10 / 299** |

Setiap soal meminta satu controller dengan `index`, `store(Request)`, `show($id)`, `update(Request,$id)`, `destroy($id)`, mengikuti kontrak PRD. Route, model, migration dan dependensi tetap disediakan harness. Respons index200/data-array, store201/data-object, show/update200/data-object, destroy204 kosong, missing-ID404 JSON-object, validasi422/errors-field. Tidak ada foreign key, autentikasi, pagination atau PATCH. Skema lengkap tersedia pada JSON tiap soal; `python -m critic_agent prompt evaluation/final-v1/specs/RESOURCE.json` hanya menampilkan prompt dan tidak menghasilkan kode.

## Menjalankan validasi

Dari root proyek, periksa seluruh bahan lokal dahulu:

```powershell
python -m critic_agent final-validate --package final-v1 --local-only --json
```

Mode lokal memvalidasi spesifikasi/fixture, kecocokan katalog/diff/matriks tersimpan, lint semua kontrol dan scaffold, discovery PHPUnit, enumerasi dataset dan probe assertion respons tepercaya. Controller tidak dieksekusi di host. Status `LOCAL_VALIDATED` dan exit0 menyatakan pemeriksaan lokal berhasil, dengan `functional_validation: NOT_RUN`.

Untuk bukti fungsional, aktifkan Docker Desktop Linux/WSL2 dan pastikan `docker version` menunjukkan Server. Base `critic-laravel:dev` harus tersedia; bangun dengan command development `harness-build` bila lingkungan belum dipulihkan sesuai HANDOFF. Paket tidak memasang software atau mengubah keamanan global.

```powershell
python -m critic_agent final-validate --package final-v1 --build --json
```

Opsional: `--resource categories` atau daftar resource membatasi eksekusi yang diminta; manifest mencatat subset itu. `--timeout 120` membatasi satu pengamatan, `--build-timeout 600` membatasi tiap operasi persiapan/build. Jangan menyebut hasil subset sebagai validasi lima soal lengkap. Tanpa `--build`, runner mencari tag image final yang cocok dengan hash sumber saat ini. Bila source berubah, gunakan build baru; jangan mengganti label image atau manifest lama.

Setiap eksekusi membuat UUID baru di `evaluations/final-validation/`. `validation.json` mencatat planned, executed, unexecuted, PASS/FAIL/UNKNOWN, readiness, versi dependensi aktual, base/image ID, hash sumber asli, hash kanonik tambahan, kontrol dan hasil tiap pengamatan. `sources/` menyimpan byte asli; `RESOURCE/traceability.json` menghubungkan hasil per aturan ke observation JSON dan raw Docker/JUnit. Ringkasan akhir yang dibagikan perlu menyertakan arsip ini secara terpisah karena direktori evaluasi diabaikan Git.

## Makna hasil

- `VALIDATED`/exit0: seluruh pengamatan yang direncanakan pada resource yang diminta memenuhi harapan dan pengulangan stabil. Ini kelulusan teknis evaluator.
- `FAILED`/exit1: terdapat bukti lengkap bahwa kontrol benar ditolak atau target pelanggaran tidak terdeteksi.
- `ERROR`/exit3: ada bagian belum dapat dinilai, seperti Docker/build/readiness, hasil parsial, hash/role/image berubah, cleanup gagal atau bukti kegagalan yang tidak cocok target.
- `ready_for_final` tetap **false** pada semua hasil. Review manusia, K2, konfigurasi/freeze, integrasi serta eksekusi A/B akhir masih memerlukan gerbang tersendiri.

Di masing-masing resource, kedua kontrol benar dan seluruh mutasi diuji pada dua image terpisah. Dua kontrol benar dan mutasi negatif pertama diulang pada image/input sama. Rencana lengkap berjumlah **648 pengamatan kandidat**:40 pengamatan kontrol benar dan608 pengamatan mutasi, ditambah readiness serta probe runtime tepercaya. Angka ini bukan jumlah kandidat Qwen atau ukuran sampel penelitian.

## Cakupan dan bukti mutasi

Internal hanya menguji CRUD dasar, omitted-required tiap field/operasi dan tiga missing-ID. Fixture final membedakan field dalam record serta nilai antar-record. Pemeriksaan array/object membaca JSON asli, lalu memeriksa ID integer, record lengkap dan nilai per ID, serta efek database dan tetangga.

Acuan memakai [profil eksplisit](profiles/) dengan fixture berbeda dari internal. Ia menambah null/empty/whitespace, tipe salah, batas valid/invalid, unique/own-unique, angka dalam string yang diterima validator, koleksi kosong dan rangkaian CRUD. Assertion dan fixture acuan tidak disalin ke image internal. Pemisahan teknis ini belum merupakan review manusia independen; seluruh bahan disiapkan OpenAI Codex.

[Katalog kontrol](controls/) menyimpan dua gaya benar, mutasi, hash, diff terhadap kontrol Eloquent, target testcase per role, fase assertion dan status HTTP salah yang diharapkan. Ada mutasi penghilangan batas/update-required, penolakan nilai sah, status/target/write salah, field tertukar, serta penerimaan input invalid secara sengaja. Mutasi penerimaan tipe/unique/required-store memakai guard yang mengembalikan respons salah secara terkendali, sehingga crash constraint database tidak dianggap bukti deteksi.

Testcase negatif harus gagal pada fase dan HTTP aktual yang dicatat, dengan marker `FINAL_ASSERTION:<case_id>:<phase>:HTTP<status>`. Kegagalan lain, khususnya500 yang tidak direncanakan, tidak diberi kredit. Mutasi aturan reference_only harus tetap lulus internal. Kode negatif bukan hasil Qwen, tidak dipakai menghitung precision/recall Critic, dan tidak boleh disisipkan ke sampel A/B sebagai pengganti keluaran model.

## Review dan kelanjutan

[Matriks](traceability/) memuat358 baris vektor acuan, termasuk70 pemetaan internal, hasil yang diharapkan, kontrol positif/negatif serta hash. Status validasi sumber tetap PENDING; hasil aktual berada di snapshot masing-masing eksekusi. [Formulir review](review/) sengaja kosong. Salin form ke catatan eksternal untuk mencatat pembuat manusia, reviewer, tanggal dan keputusan setelah pemeriksaan nyata; form asli tetap utuh agar hash paket tervalidasi tetap sama. Perubahan soal/evaluator memerlukan versi paket dan validasi baru.

Lima slot rencana20pasangan sudah terikat ke spec/image aktual dalam draf. Setelah review dan keputusan konfigurasi, buat manifest baru untuk pembekuan. `run-ab` development tetap memakai produk/books/inventory; `ab-run` memakai protokol final yang melewati gerbang. Pertahankan semua arsip gagal, perbaikan dan percobaan ulang. [Rancangan](../../docs/superpowers/specs/2026-11-23-final-evaluation-package-design.md) · [Rencana implementasi](../../docs/superpowers/plans/2026-11-23-final-evaluation-package.md).

## Integrasi A/B

Adaptor paket dan pelaporan tersedia melalui `ab-smoke`, `ab-plan-check`, `ab-run`, `ab-report`; lihat [panduan lengkap](../../docs/FINAL-AB.md) dan [bukti teknis](../../docs/evidence/final-ab-adapter-2026-11-23.md). Review manusia dan pembekuan tetap diperlukan. Jangan mengubah form asli dalam `review/`; salin dan isi catatan review eksternal yang mengikat hash paket, spesifikasi dan form kosong.
