# Panduan serah terima Critic Agent

**Pembaruan panduan** 12 November 2026 · **Versi CLI** 0.5.0

## 1. Mengenal proyek

Critic Agent adalah prototipe berbasis terminal untuk memeriksa controller CRUD REST API Laravel. Masukannya adalah spesifikasi JSON yang menjelaskan satu resource, field dan aturan validasinya, serta status HTTP yang diharapkan. Contoh yang tersedia meliputi [products](../examples/products.json), [books](../examples/books.json), dan [inventory](../examples/inventory_items.json). Prototipe berfokus pada API JSON dengan satu resource, field skalar, dan tanpa autentikasi.

1. Qwen2.5-7B-Instruct berjalan secara lokal melalui Ollama dan menghasilkan satu berkas controller PHP.
2. Critic Agent memeriksa sintaks dan struktur controller, lalu menjalankan pengujian perilaku API di lingkungan Laravel dalam Docker.
3. Jika ada temuan, Critic Agent menyusun umpan balik berdasarkan hasil pemeriksaan. Qwen menggunakan umpan balik itu untuk merevisi kode. Proses berhenti saat semua pemeriksaan internal lulus, kode revisi identik dengan percobaan sebelumnya, batas tiga revisi tercapai, atau terjadi gangguan model atau lingkungan.
4. Evaluator acuan dapat dijalankan terpisah untuk mengukur hasil kode awal dan akhir. Tes dan hasil acuan berada di luar prompt dan umpan balik revisi.

## 2. Siapkan lingkungan

Jalankan semua perintah di PowerShell dari folder repositori yang memuat `pyproject.toml` dan `README.md`.

| Kebutuhan | Digunakan untuk |
| --- | --- |
| Python 3.11 atau lebih baru | Menjalankan CLI. Dependensi Python tambahan tidak diperlukan. |
| PHP CLI 8.3 di PATH | Lint dan pemeriksaan struktur dengan tokenizer. Jalankan perilaku controller kandidat hanya di Docker. |
| Docker Desktop dengan WSL2 dan Linux containers di Windows | Menjalankan pengujian dinamis. Build image pertama membutuhkan akses jaringan untuk image dasar dan dependensi Composer. |
| Ollama dan model `qwen2.5:7b-instruct` | Membuat atau merevisi controller. Pemeriksaan kesiapan harness dan evaluasi arsip dapat dilakukan tanpa menjalankan model. |

```powershell
python -m critic_agent --help
python -m critic_agent validate examples/books.json
python -m critic_agent doctor
docker version
```

Validasi spesifikasi menampilkan `"valid": true`. Pastikan `docker version` menampilkan bagian **Client** dan **Server**. Sebelum demo generasi, periksa hasil `doctor` setelah layanan Ollama aktif dan model terunduh.

## 3. Jalankan demo dengan spesifikasi books

`examples/books.json` mendefinisikan `BookController` dengan field wajib `title` dan `pages`. Kontraknya mencakup respons HTTP 201 untuk pembuatan data, 422 untuk input yang gagal divalidasi, dan 204 untuk penghapusan yang berhasil.

### Bangun lingkungan uji

Jalankan perintah satu per satu. Lanjutkan setelah perintah sebelumnya berhasil.

```powershell
python -m critic_agent harness-build
python -m critic_agent resource-build examples/books.json --timeout 600
python -m critic_agent resource-check examples/books.json
```

Build resource menampilkan `BUILT`. Pemeriksaan kesiapan harus menampilkan `READY` dengan 27/27 tes pada controller acuan harness. Loop di bawah menilai kandidat pada 12 tes internal.

Untuk melihat contoh kegagalan tanpa Ollama, jalankan perintah berikut setelah harness siap. Controller contoh memiliki method kosong dan hasil yang diharapkan adalah `FAILED_INTERNAL`.

```powershell
python -m critic_agent resource-check examples/books.json --code examples/NoOpBookController.php
```

### Buat dan periksa controller

Aktifkan Ollama sebelum mengunduh model dan menjalankan demo.

```powershell
ollama pull qwen2.5:7b-instruct
python -m critic_agent doctor
$booksRun = python -m critic_agent run-resource examples/books.json --seed 42 --temperature 0.2 --timeout 300 | ConvertFrom-Json
$booksRun | ConvertTo-Json -Depth 6
```

Seed 42 dan suhu 0,2 adalah konfigurasi pengembangan. Gunakan `run_directory` dari keluaran untuk membuka arsip demo. Kandidat dapat langsung lolos pada percobaan awal, sehingga tidak setiap demo akan menampilkan revisi.

| Status | Cara membacanya |
| --- | --- |
| `LOLOS` | Kode lulus pemeriksaan statis dan seluruh tes internal untuk resource itu. |
| `BELUM LOLOS` | Masih ada temuan. Periksa `stop_reason` untuk mengetahui apakah kode identik atau batas revisi tercapai. |
| `ERROR` | Terjadi gangguan model atau lingkungan. Periksa log sebelum menilai kandidat. |
| `AWAITING_DYNAMIC_TESTS` | Keluaran dari tahap terpisah, seperti `generate` atau `analyze`, masih menunggu bukti pengujian dinamis. |

### Bandingkan kode awal dan akhir

Gunakan `$booksRun` dari demo di atas di sesi PowerShell yang sama. Jalankan untuk loop berstatus `LOLOS` atau `BELUM LOLOS`.

```powershell
python -m critic_agent resource-evaluation-build examples/books.json --timeout 600
```

Jalankan evaluator setelah build berstatus `BUILT`.

```powershell
python -m critic_agent evaluate-resource $booksRun.run_directory
```

Status `EVALUATED` berarti evaluator selesai menilai pasangan kode. Buka path `report` untuk melihat jumlah tes yang lulus dari 35 kasus acuan, perubahan persentase kelulusan dalam poin persentase, dan indikator perbaikan atau regresi.

Untuk mencoba resource lain, gunakan `run-products` setelah `harness-build` dan `harness-check` untuk products. Untuk inventory, ulangi alur books dengan [spesifikasi inventory](../examples/inventory_items.json). Lihat [perintah lengkap per resource](../README.md).

## 4. Baca hasil yang sudah tersedia

Contoh berikut berasal dari pengujian pengembangan yang diverifikasi pada 4–5 November 2026.

| Resource | Tes internal awal → akhir | Tes acuan awal → akhir | Hasil loop |
| --- | --- | --- | --- |
| Products | 13/14 → 14/14 | 31/33 → 33/33 | `LOLOS` setelah satu revisi. |
| Books | 12/12 → 12/12 | 35/35 → 35/35 | `LOLOS` pada percobaan awal. |
| Inventory | 11/16 → 12/16 | 51/57 → 53/57 | `BELUM LOLOS`. Revisi kedua menghasilkan kode identik dan empat aturan wajib untuk operasi update masih hilang. |

Audit pengembangan pada 12 November 2026 menemukan bahwa tes internal daftar products dapat menerima respons dengan field yang tertukar antar-record. Perbaikan assertion dan verifikasi suite baru masih diperlukan sebelum pembekuan. [Catatan audit cakupan](progress.md#products-internal-assertion-audit--12-november-2026)

Pengujian deteksi komponen selesai pada 16 kasus dengan 0 error prediksi. Laporan memakai label draf berbantuan AI yang masih menunggu peninjauan manusia independen. Dari kasus sintetis, Critic mendeteksi 6 dari 8 kasus bermasalah. Pada keluaran Qwen di uji pengembangan, Critic mendeteksi 3 dari 3 kasus bermasalah pada lima kasus unik setelah satu duplikat dikeluarkan. Data held-out belum tersedia pada laporan tersebut. [Laporan komponen dan catatan bukti](evidence/README.md)

## 5. Temukan artefak dan periksa paket serah terima

| Lokasi | Isi |
| --- | --- |
| `critic_agent/`, `harness/`, `resource_templates/`, `evaluation/` | Kode CLI, lingkungan tes Laravel, template resource, dan suite acuan. |
| `examples/`, `corpora/`, `docs/evidence/` | Spesifikasi contoh, korpus pengembangan, dan salinan laporan komponen yang dapat dibaca setelah clone. |
| `runs/` | Arsip eksekusi, termasuk prompt, respons model, controller awal dan akhir bila tersedia, `history.json`, `run_manifest.json`, dan catatan per percobaan. |
| `evaluations/`, `component-runs/`, `component-evidence/`, `builds/` | Hasil evaluator, prediksi dan bukti komponen, serta catatan build. |

### Checklist penerimaan

- [ ] Pastikan repositori atau salinan kode dapat dibuka dan spesifikasi `examples/books.json` lolos validasi.
- [ ] Jalankan pemeriksaan kesiapan books sampai `READY` 27/27. Untuk mengecek instalasi CLI dan kode Python, jalankan `python -m unittest discover -s tests -v`.
- [ ] Jalankan satu demo dan simpan `run_directory`. Jika hanya meninjau hasil yang sudah ada, buka laporan komponen yang ikut repositori.
- [ ] Untuk audit eksperimen lama, terima ZIP arsip mentah secara terpisah. Folder keluaran lokal, image Docker, dan model Ollama berada di luar paket clone. Simpan arsip asli beserta hash, log, dan hasil gagal. [Daftar arsip yang perlu ditransfer](HANDOFF.md#apa-yang-ikut-push-dan-apa-yang-diserahkan-terpisah)

## 6. Tangani kendala umum

| Gejala | Tindakan |
| --- | --- |
| Docker hanya menampilkan Client atau pipe `dockerDesktopLinuxEngine` tidak ditemukan | Buka Docker Desktop, tunggu Engine berjalan, lalu ulangi `docker version`. |
| Akses Docker ditolak saat Engine berjalan | Ulangi pemeriksaan di terminal pengguna yang dapat mengakses Docker Server. |
| Ollama atau model belum siap | Aktifkan Ollama, jalankan `ollama pull qwen2.5:7b-instruct`, lalu ulangi `doctor`. |
| Harness gagal atau run berstatus `ERROR` | Baca `detail`, log, dan arsip run. Setelah penyebabnya diperbaiki, jalankan percobaan baru dan simpan arsip sebelumnya. |
| Folder hasil lama tidak ada setelah clone | Gunakan laporan yang ikut repositori atau minta ZIP arsip mentah dari tim proyek bila audit memerlukan log asli. |

## 7. Status pekerjaan lanjutan

CLI saat ini menyediakan `pilot-plan` untuk menyusun manifest suhu dan seed, `pilot-run` untuk menjalankan job bertahap, dan `pilot-metadata` untuk mencatat metadata dari arsip satu job. Periksa opsi dengan `python -m critic_agent pilot-plan --help`, `python -m critic_agent pilot-run --help`, dan `python -m critic_agent pilot-metadata --help`. Penyelesaian pilot penuh masih perlu diverifikasi. Agregasi lintas job dan rekap penggunaan token masih perlu dikerjakan. Metadata per job saat ini menyimpan `token_usage` sebagai `null`.

Sebelum evaluasi akhir TA, tim masih perlu meninjau label dan assertion bersama peninjau independen, memutuskan cakupan perbandingan umpan balik spesifik dan generik, menyiapkan data held-out, membekukan konfigurasi, lalu menjalankan evaluasi akhir. Angka pada panduan ini menggambarkan hasil pengembangan pada kasus yang dilaporkan. [PRD dan protokol evaluasi](../PRD_Critic_Agent_v1.3.md#12-rencana-pengujian-dan-kriteria-keberhasilan)
