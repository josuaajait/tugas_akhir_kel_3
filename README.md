# Critic Agent

Prototipe TA untuk memeriksa controller CRUD REST API Laravel hasil Qwen2.5-7B-Instruct. Versi 0.5.0 menyediakan loop lintas resource serta evaluator acuan pengembangan terpisah untuk products, books, dan inventory.

Harness acuan telah dibuktikan melalui terminal pengguna dengan 21/21 test lulus. Pada uji langsung pertama, kandidat awal Qwen lulus 13/14 dan kandidat akhir lulus 14/14 setelah satu revisi otomatis. Qwen mengganti pemanggilan response()->setContent('', 204) menjadi response()->json('', 204). Run terverifikasi tersimpan di runs/20261104T031502Z_loop_713c3f8803f441929ae6ed8f38077232. Petunjuk harness ada di [harness/README.md](harness/README.md).

## Yang tersedia

- Validasi spesifikasi JSON yang ketat dan prompt dengan kontrak Laravel tetap.
- Client Ollama lokal dengan seed/suhu tercatat, timeout, dan satu retry gangguan komunikasi.
- Arsip unik tiap generasi: spesifikasi, prompt, respons mentah yang diterima, kode, hash, dan manifest; termasuk kegagalan ekstraksi/layanan.
- Pemeriksaan sintaks serta namespace/class/method/signature melalui tokenizer PHP. Controller tidak dieksekusi oleh perintah ini.
- Pemeriksaan kesiapan Python, PHP, Docker, layanan Ollama, dan nama model.
- Perintah `harness-build`, `harness-check`, dan `check-products`; parser JUnit, pembatasan output, dan arsip pemeriksaan container.
- `run-products` menjalankan loop otomatis, termasuk penghentian ketika lolos, kode identik, batas revisi, atau ERROR lingkungan/model. Arsip awal diverifikasi dengan spec/hash/config sebelum dipakai ulang.
- `evaluation-build` dan `evaluate-products` membandingkan kode awal/akhir arsip loop dengan suite pengembangan terpisah, tanpa memanggil Qwen. Evaluator products sudah diverifikasi dari terminal pengguna:31/33 menjadi33/33 (uplift6.06 poin persentase).

Status `AWAITING_DYNAMIC_TESTS` berarti tahap fondasi selesai tanpa temuan statis atau kode telah diekstrak, bergantung perintah yang dijalankan. **Bukan LOLOS fungsional**. `generate` tidak otomatis menjalankan `analyze`.

## Menjalankan dari folder proyek

Diperlukan Python 3.11+. Gunakan terminal pada folder yang berisi README ini. Paket Python tambahan tidak diperlukan untuk perintah di bawah.

```powershell
python -m critic_agent --help
python -m critic_agent doctor
python -m critic_agent validate examples/products.json
python -m critic_agent prompt examples/products.json
python -m critic_agent analyze examples/products.json examples/StructureOnlyController.php
python -m unittest discover -s tests -v
```

`StructureOnlyController.php` adalah fixture struktur dengan method kosong, bukan implementasi CRUD yang benar. Gunakan untuk memastikan pemeriksa statis bekerja; jangan memakainya sebagai controller acuan fungsional.

Setelah Ollama terpasang dan aktif serta model sudah diunduh:

```powershell
ollama pull qwen2.5:7b-instruct
python -m critic_agent generate examples/products.json --seed 42 --temperature 0.2 --timeout 300
```

Suhu/seed ini hanya konfigurasi pengembangan; konfigurasi penelitian ditentukan setelah pilot. Layanan dipanggil melalui localhost. Model aktual, digest dan kuantisasi masih perlu diverifikasi sebelum eksperimen. Perintah `generate` memerlukan Ollama; validasi/prompt tidak memerlukan layanan tersebut. PHP diperlukan untuk `analyze`.

Kode keluar: 0 = perintah berhasil pada tahapnya; 1 = temuan statis/format atau BELUM LOLOS; 2 = input atau akses file invalid; 3 = prasyarat/layanan bermasalah. `run-products` menyatakan LOLOS hanya setelah pemeriksaan statis bersih dan 14/14 test internal lulus.

## Loop revisi otomatis

Gunakan kode awal yang sudah dibuat tanpa mengubah arsip sumber.

```powershell
python -m critic_agent run-products examples/products.json --initial-run runs/20261104T025540Z_4fad073a00e0484abf342797d9d9f6a6
```

Perintah ini membaca ulang kode awal, memeriksanya pada harness saat ini, mengirim feedback terbukti ke Qwen jika gagal, lalu mengulang maksimal tiga revisi. Seed dan suhu harus cocok dengan arsip awal. Untuk eksperimen pengembangan baru mulai dari generasi awal otomatis:

```powershell
python -m critic_agent run-products examples/products.json --seed 42 --temperature 0.2 --max-revisions 3
```

Keluaran tersimpan dalam folder baru `runs/..._loop_...`: `initial_controller.php`, `final_controller.php` bila tersedia, `history.json`, `run_manifest.json`, `run.log`, serta `attempts/0` sampai `attempts/3`. Setiap percobaan memuat kode/respons, hasil statis/dinamis, prompt revisi dan feedback bila revisi diperlukan. Kode akhir adalah kandidat terakhir. Respons tanpa kode menghasilkan artefak akhir yang tidak tersedia dan tercatat.

Hasil akhir LOLOS, BELUM LOLOS atau ERROR ditampilkan bersama jumlah revisi. LOLOS merujuk pemeriksaan internal. Jalankan evaluator terpisah untuk mengukur kesesuaian terhadap suite acuan.

## Evaluasi acuan awal dan akhir

Bangun ulang harness agar memakai runtime bersama terbaru, lalu bangun image evaluator yang berbeda. Jalankan pada arsip loop yang sudah selesai:

```powershell
python -m critic_agent harness-build
python -m critic_agent harness-check
python -m critic_agent evaluation-build
python -m critic_agent evaluate-products runs/20261104T031502Z_loop_713c3f8803f441929ae6ed8f38077232
```

Evaluator baru memiliki 33 kasus yang ditulis dari kontrak products: CRUD, JSON 404, field wajib, tipe, unique, batas nilai, isolasi record, dan rangkaian CRUD. Kode awal dan akhir memakai suite/image ID identik dalam container dan database baru. Suite ini disimpan di image evaluator; image internal tidak memuatnya. Entrypoint evaluator menolak mode loop internal. Rincian ada di [evaluation/README.md](evaluation/README.md).

Perintah tidak merevisi kode atau mengubah arsip sumber. Hasil baru berada di `evaluations/.../evaluation_result.json`, bersama snapshot kode dan provenance. Ringkasan memuat pembilang/penyebut, pass rate, uplift dalam poin persentase, serta indikator repair/regression untuk satu pasangan. Penyebut nol menghasilkan `null` (N/A). `EVALUATED` berarti pasangan berhasil dinilai, termasuk bila test kandidat gagal; status ini tidak berarti semua test lulus.

Hash arsip yang berubah atau file yang hilang meskipun diklaim tersedia ditolak. Respons tanpa kode yang dinyatakan arsip, atau kode gagal sintaks yang dibuktikan lint di dalam Docker, mendapat 0/33 dengan alasan test tidak dijalankan. Kegagalan kesiapan, laporan parsial/invalid, timeout yang belum diketahui penyebabnya, atau masalah lingkungan menghasilkan ERROR dan metrik pasangan `null`.

Suite ini **paket pengembangan**, dibuat setelah keluaran Qwen pertama diamati. Sebelum penelitian akhir, tinjau assertion serta contoh pelanggaran target, pisahkan kasus akhir, lalu bekukan suite/protokol/image. Jangan memakai hasil suite akhir untuk menyetel Critic. Terminal pengguna telah memverifikasi readiness evaluator33/33, kode awal31/33 dan kode akhir33/33. Ini satu pasangan pengembangan. Codex CLI juga telah menjalankan Docker dan harness-check21/21 dengan persetujuan eskalasi; sesi desktop ini masih dibatasi.

## Harness dari spesifikasi resource lain

```bat
python -m critic_agent resource-build examples/books.json
python -m critic_agent resource-check examples/books.json
python -m critic_agent run-resource examples/books.json --seed 42 --temperature 0.2 --timeout 300
```

Books mendefinisikan12 kasus internal dan27 total readiness. Contoh kedua: examples/inventory_items.json, dengan model StockItem/tabel inventory_items dan16 internal/46 total readiness. Books sudah teruji: readiness27/27 dan Qwen langsung12/12. Inventory teruji: readiness46/46, kandidat11/16 menjadi12/16 lalu berhenti identical_code pada revisi2. Image default per resource terpisah. Build/check tidak memanggil Qwen. Evaluator terpisah books/inventory tersedia mulai0.5.0 dan masih menunggu verifikasi Docker. Baca [cakupan, batas, dan validasi negatif](docs/resource-harness.md) sebelum menjalankan pilot.

## Evaluator books dan inventory

Gunakan arsip loop yang sudah selesai. Perintah ini tidak memanggil Qwen atau mengubah kandidat.

```bat
python -m critic_agent resource-evaluation-build examples/books.json --timeout 600
python -m critic_agent evaluate-resource runs/20261104T044458Z_loop_52c1faef1c1644f3ac228b14eebdebcf
python -m critic_agent resource-evaluation-build examples/inventory_items.json --timeout 600
python -m critic_agent evaluate-resource runs/20261104T044936Z_loop_4c8045891ecc4a74a31e0117ed15932a
```

Build evaluator harus BUILT sebelum evaluasi. Books mendefinisikan35 kasus acuan dan inventory57, termasuk field wajib, tipe, min/max/unique serta batas valid POST dan PUT. Suite/data acuan dipisahkan dari template internal. Hasil awal/akhir memakai image ID dan suite yang sama dengan DB baru; raw counts, uplift, repair dan regression ditulis ke folder evaluations baru. EVALUATED berarti penilaian selesai, termasuk bila test gagal. Penyebut nol bernilai null/N/A.

Paket ini untuk pengembangan dan dibuat setelah keluaran pertama diamati; belum merupakan bukti sumatif yang dibutakan/dibekukan. Hasil Docker baru perlu dijalankan di terminal/Codex CLI pengguna. Image dan fingerprint internal serta paket products tetap kompatibel. Rincian: [evaluator resource](evaluation/resource-reference/README.md).

## Langkah berikutnya

1. Verifikasi evaluator books/inventory pada arsip yang sudah ada melalui CLI pengguna.
2. Siapkan korpus berlabel dan evaluasi komponen (precision/recall/FPR).
3. Jalankan pilot, validasi cakupan, peninjauan dan pembekuan sebelum eksperimen akhir.

Rencana fondasi: `docs/superpowers/plans/2026-11-03-foundation.md`. Batas MVP: `docs/spec-mvp.md`. Catatan kemajuan: `docs/progress.md`.

Tes unit client memakai transport terkontrol. Bukti integrasi Qwen/Docker berasal dari arsip live pengguna yang dijelaskan di docs/progress.md, terpisah dari hasil unit test. Analisis statis menggunakan PHP asli bila tersedia; pengujian itu dilewati otomatis bila PHP tidak ditemukan.

## Referensi implementasi

- [Ollama Generate API](https://docs.ollama.com/api/generate)
- [PHP token_get_all](https://www.php.net/manual/en/function.token-get-all.php)
- [Laravel routing](https://laravel.com/docs/12.x/routing)

Harness awal mengunci Laravel 12.70.2 dan PHPUnit 11.5.57 dalam composer.lock. Bekukan image dan konfigurasi final setelah pilot.
