# Critic Agent

> **Melanjutkan proyek?** Mulai dari [panduan serah terima](docs/HANDOFF.md), diperbarui 5 November 2026: status terverifikasi, setup clone baru, artefak yang tidak ikut Git, dan daftar kerja berikutnya. [Salinan laporan komponen](docs/evidence/component-provisional-2026-11-05.json) ikut repositori agar hasil terakhir dapat dibaca setelah clone.
>
> **Untuk klien:** [Panduan serah terima klien](docs/PANDUAN-SERAH-TERIMA-KLIEN.md) memuat cara menyiapkan lingkungan, menjalankan demo, membaca hasil, dan memeriksa paket yang diterima.

Prototipe TA untuk memeriksa controller CRUD REST API Laravel hasil Qwen2.5-7B-Instruct. Versi 0.5.0 menyediakan loop lintas resource serta evaluator acuan pengembangan terpisah untuk products, books, dan inventory.

Harness acuan telah dibuktikan melalui terminal pengguna dengan 21/21 test lulus. Pada uji langsung pertama, kandidat awal Qwen lulus 13/14 dan kandidat akhir lulus 14/14 setelah satu revisi otomatis. Qwen mengganti pemanggilan response()->setContent('', 204) menjadi response()->json('', 204). Run terverifikasi tersimpan di runs/20261104T031502Z_loop_713c3f8803f441929ae6ed8f38077232. Petunjuk harness ada di [harness/README.md](harness/README.md).

## Yang tersedia

**Temuan terbaru24November:** [audit seluruh soal](docs/reviews/2026-11-24-final-v1-ai-audit/LAPORAN.md) membuktikan tiga celah evaluator yang perlu ditangani sebelum freeze: target ID kedua, string pendek yang sah dan klasifikasi JSON rusak. Paket serta bukti lama dipertahankan; status validasi kontrol di bawah tidak berarti cakupan evaluator lengkap.

- `final-validate --package final-v1` menyiapkan bukti validasi evaluator untuk lima soal baru: categories, rooms, assets, courses dan shipments. Paket memiliki70 kasus internal,358 kasus acuan, dua gaya kontrol benar per soal,299 mutasi target, matriks dan formulir review kosong. Mode `--local-only` tidak mengeksekusi controller; `--build` memvalidasi di Docker tanpa Qwen. Verifikasi23November:648/648 pengamatan memenuhi harapan dan218 tes Python lulus. [Soal, perintah, dan arti hasil](evaluation/final-v1/README.md) · [Bukti](docs/evidence/final-v1-validation-2026-11-23.md). Paket ini belum merupakan pembekuan atau pelaksanaan A/B akhir.
- `ab-smoke` menguji integrasi final-v1 dengan fixture sintetis tanpa Qwen; `ab-plan-check` memeriksa gerbang protokol; `ab-run` mengeksekusi satu slot protokol beku; `ab-report` memverifikasi arsip dan menghitung hasil per soal/kondisi. Integrasi dan agregasi sudah tersedia, sedangkan review manusia, keputusan K2 dan pembekuan masih diperlukan. Form asli paket tetap kosong; attestation disimpan terpisah agar hash paket tetap sama. [Panduan A/B final](docs/FINAL-AB.md) · [Bukti teknis](docs/evidence/final-ab-adapter-2026-11-23.md).
- [Paket review manusia](docs/review-packets/final-v1-2026-11-23/README.md) menyediakan358kasus pemeriksaan, lima form eksternal kosong, checklist/penugasan/keputusan, draf input protokol dan [ZIP mandiri](docs/review-packets/final-v1-2026-11-23/reviewer-bundle.zip) berisi sumber serta bukti. Lampiran review komponen16kasus tetap terpisah; seluruh persetujuan manusia masih pending.
- Validasi spesifikasi JSON yang ketat dan prompt dengan kontrak Laravel tetap.
- Client Ollama lokal dengan seed/suhu tercatat, timeout, dan satu retry gangguan komunikasi.
- Arsip unik tiap generasi: spesifikasi, prompt, respons mentah yang diterima, kode, hash, dan manifest; termasuk kegagalan ekstraksi/layanan.
- Pemeriksaan sintaks serta namespace/class/method/signature melalui tokenizer PHP. Controller tidak dieksekusi oleh perintah ini.
- Pemeriksaan kesiapan Python, PHP, Docker, layanan Ollama, dan nama model.
- Perintah `harness-build`, `harness-check`, dan `check-products`; parser JUnit, pembatasan output, dan arsip pemeriksaan container.
- `run-products` menjalankan loop otomatis, termasuk penghentian ketika lolos, kode identik, batas revisi, atau ERROR lingkungan/model. Arsip awal diverifikasi dengan spec/hash/config sebelum dipakai ulang.
- `evaluation-build` dan `evaluate-products` membandingkan kode awal/akhir arsip loop dengan suite pengembangan terpisah, tanpa memanggil Qwen. Evaluator products sudah diverifikasi dari terminal pengguna:31/33 menjadi33/33 (uplift6.06 poin persentase).
- `component-corpus-init`, `component-evidence`, `component-run`, dan `component-report` menyediakan korpus draf, bukti acuan terpisah serta precision/recall/FPR per kode dan asal korpus. Tidak memanggil Qwen; label manusia tetap perlu ditinjau.

Status `AWAITING_DYNAMIC_TESTS` berarti tahap fondasi selesai tanpa temuan statis atau kode telah diekstrak, bergantung perintah yang dijalankan. **Bukan LOLOS fungsional**. `generate` tidak otomatis menjalankan `analyze`.

## Menjalankan dari folder proyek

Untuk memasukkan kebutuhan CRUD melalui pertanyaan terminal, jalankan

```powershell
python -m critic_agent start
```

Isi nama resource/tabel, model, controller dan jumlah field, lalu nama/tipe/batas/unique setiap field. Tipe yang didukung string dan integer; semua field wajib pada POST dan PUT. Sistem menampilkan JSON untuk dikonfirmasi, menyimpannya, menyiapkan harness Docker dan menjalankan Qwen serta self-debugging maksimal tiga revisi. Jawab `n` pada konfirmasi atau tekan Ctrl+C untuk membatalkan.

Python, PHP, Docker Desktop Linux/WSL2 dan Ollama dengan model yang dipilih perlu tersedia dan aktif. Build pertama image dapat memerlukan jaringan. Kegagalan prasyarat/build/readiness dicatat sebagai ERROR sebelum Qwen dipanggil. Kemajuan dan pertanyaan tampil di stderr; hasil akhir di stdout mengikuti mode tampilan di bawah.

Folder `runs/..._interactive_UUID/` memuat `spec.json`, `session.json`, hasil prasyarat/build/readiness, log persiapan dan subfolder `runs/` untuk arsip loop. Ringkasan menampilkan `run_directory`, `final_controller` bila tersedia dan hasil percobaan. Image resource memakai tag UUID dan dipertahankan untuk audit. `start` memakai harness generik yang dibentuk dari jawaban pengguna. Command `run-products` tetap memakai kontrak products legacy.

Opsi yang tersedia antara lain `--output`, `--model`, `--temperature`, `--seed`, `--timeout`, `--test-timeout`, `--build-timeout` dan `--max-revisions`. Suhu 0.2/seed 42 adalah default development. Exit code `130` menandakan CANCELLED. Lihat `python -m critic_agent start --help`. Evaluator acuan tetap dijalankan terpisah sesuai kontrak yang didukung.

### Tampilan terminal

Seluruh command mendukung tampilan bergaya [PTerm](https://github.com/pterm/cli-template) yang diadaptasi ke Python standard library: header, status berwarna dan tabel hasil. Command yang lama menampilkan indikator proses; `run-products`, `run-resource` serta loop dari `start`, pilot dan A/B juga menampilkan tahap generasi, pemeriksaan statis, test Docker dan hasil tiap percobaan. Spinner berhenti sebelum pertanyaan interaktif. Indikator hanya menunjukkan tahap berjalan, tanpa persentase perkiraan.

Tampilan ini aktif otomatis saat stdout terhubung ke terminal. Gunakan `--pretty` untuk memaksanya, `--json` untuk hasil JSON murni, dan `--no-color` atau environment `NO_COLOR` untuk mematikan warna. Flag dapat diletakkan sebelum atau sesudah nama command. Terminal tanpa dukungan ANSI memakai tampilan teks biasa; `TERM=dumb` juga mematikan animasi. Tabel panjang membungkus teks mengikuti lebar terminal.

```powershell
python -m critic_agent doctor --pretty
python -m critic_agent run-resource examples/books.json --pretty
python -m critic_agent start --pretty
python -m critic_agent validate examples/products.json --json
```

Saat stdout dipipe atau dialihkan ke file, hasil otomatis tetap JSON agar script lama dapat memakai `ConvertFrom-Json`. Kemajuan, pertanyaan dan log build Docker ada di stderr; `harness-build` dan `evaluation-build` kini memberikan ringkasan hasil terstruktur di stdout. `prompt` selalu mengeluarkan teks prompt asli, termasuk saat memakai `--pretty`; `--help` tetap berupa bantuan teks. Status LOLOS tetap berarti pemeriksaan internal lulus, sementara `AWAITING_DYNAMIC_TESTS`, ERROR dan hasil provisional mempertahankan makna aslinya. Format presentasi tidak mengubah arsip penelitian atau aturan revisi.

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

Books mendefinisikan12 kasus internal dan27 total readiness. Contoh kedua: examples/inventory_items.json, dengan model StockItem/tabel inventory_items dan16 internal/46 total readiness. Books sudah teruji: readiness27/27 dan Qwen langsung12/12. Inventory teruji: readiness46/46, kandidat11/16 menjadi12/16 lalu berhenti identical_code pada revisi2. Image default per resource terpisah. Build/check tidak memanggil Qwen. Evaluator0.5.0 sudah teruji live: books35/35 menjadi35/35; inventory51/57 menjadi53/57 dengan empat kegagalan PUT required tersisa. Baca [cakupan, batas, dan validasi negatif](docs/resource-harness.md) sebelum menjalankan pilot.

## Evaluator books dan inventory

Gunakan arsip loop yang sudah selesai. Perintah ini tidak memanggil Qwen atau mengubah kandidat.

```bat
python -m critic_agent resource-evaluation-build examples/books.json --timeout 600
python -m critic_agent evaluate-resource runs/20261104T044458Z_loop_52c1faef1c1644f3ac228b14eebdebcf
python -m critic_agent resource-evaluation-build examples/inventory_items.json --timeout 600
python -m critic_agent evaluate-resource runs/20261104T044936Z_loop_4c8045891ecc4a74a31e0117ed15932a
```

Build evaluator harus BUILT sebelum evaluasi. Books mendefinisikan35 kasus acuan dan inventory57, termasuk field wajib, tipe, min/max/unique serta batas valid POST dan PUT. Suite/data acuan dipisahkan dari template internal. Hasil awal/akhir memakai image ID dan suite yang sama dengan DB baru; raw counts, uplift, repair dan regression ditulis ke folder evaluations baru. EVALUATED berarti penilaian selesai, termasuk bila test gagal. Penyebut nol bernilai null/N/A.

Paket ini untuk pengembangan dan dibuat setelah keluaran pertama diamati; belum merupakan bukti sumatif yang dibutakan/dibekukan. Hasil live Docker sudah terverifikasi dari terminal pengguna: books35/35->35/35 (uplift0) dan inventory51/57->53/57 (uplift3.508772 poin, repair0/1). Image dan fingerprint internal serta paket products tetap kompatibel. Rincian: [evaluator resource](evaluation/resource-reference/README.md).

## Status terakhir dan langkah berikutnya

Per 5 November 2026, komponen menjalankan16 kandidat tanpa error prediksi dan menghasilkan laporan provisional. Sintetis:TP6/FP0/TN2/FN2, precision6/6=100%, recall6/8=75%, FPR0/2=0%. Qwen formatif:TP3/FP0/TN2/FN0 pada5 kode unik, precision3/3=100%, recall3/3=100%, FPR0/2=0%; satu duplikat tetap disimpan. Dua FN sintetis adalah aturan min/max reference_only. Held-out belum ada. Semua label masih draf berbantuan AI atas nama Mikhael Josua Roganda; angka kecil/formatif ini bukan hasil akhir penelitian.

Korpus: corpora/annotations/20261104T085829Z_mikhael-ai-assisted_e7a9c4248c344f21aa2b3df91fca627c/corpus.json. Run lokal: component-runs/20261105T005526Z_component_4a131234b1c14b5a95421e211dcdf739. [Laporan yang ikut Git](docs/evidence/component-provisional-2026-11-05.json) dan [provenance](docs/evidence/README.md) terpisah dari arsip raw yang diabaikan Git.

CLI menyediakan `pilot-plan`, `pilot-run`, dan `pilot-metadata`. Eksekusi pilot lengkap dan agregasi lintas job masih perlu dituntaskan, diikuti review manusia, keputusan A/B, pemisahan held-out, pembekuan konfigurasi, serta evaluasi dan pelaporan akhir. Lihat [panduan serah terima klien](docs/PANDUAN-SERAH-TERIMA-KLIEN.md#7-status-pekerjaan-lanjutan) untuk status perintah pilot.

Perintah/review komponen: [evaluasi komponen](docs/component-evaluation.md). Riwayat verifikasi kode terakhir:134 tes Python lulus tanpa skip pada 4 November 2026; jalankan ulang di clone penerima. Tes terkontrol dipisahkan dari bukti live Docker/Qwen. Versi aplikasi tetap0.5.0, protokol komponen 1.0; hash sumber dicatat.

Rencana lama: docs/superpowers/plans/. Batas MVP: [spec-mvp](docs/spec-mvp.md). Riwayat: [progress](docs/progress.md).

## Referensi implementasi

- [Ollama Generate API](https://docs.ollama.com/api/generate)
- [PHP token_get_all](https://www.php.net/manual/en/function.token-get-all.php)
- [Laravel routing](https://laravel.com/docs/12.x/routing)

Harness awal mengunci Laravel 12.70.2 dan PHPUnit 11.5.57 dalam composer.lock. Bekukan image dan konfigurasi final setelah pilot.
