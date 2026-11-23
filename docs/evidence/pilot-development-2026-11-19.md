# Pilot development, 19 November 2026

## Hasil grid lengkap

Seluruh 27 job dan 27 pasangan evaluasi sudah selesai. Ada 21 LOLOS, enam BELUM LOLOS karena `identical_code`, nol ERROR loop dan nol ERROR evaluator. Seluruh 27 kandidat awal berhasil diekstrak. Satu kandidat books kemudian gagal sintaks dan dinilai 0/35 oleh evaluator.

Setiap baris memuat tiga seed. Skor acuan adalah jumlah assertion lulus dari tiga pasangan pada spesifikasi dan suhu yang sama. Kolom perbaikan membagi jumlah kandidat akhir yang tuntas oleh jumlah kandidat awal yang belum lulus acuan. Median waktu menggunakan durasi attempt end-to-end, termasuk generasi dan pengujian.

| Resource | Suhu | LOLOS | Awal gagal internal | Hash awal unik | Acuan awal → akhir | Perbaikan tuntas | Median waktu (detik) | Token teramati |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| Products | 0 | 3/3 | 0/3 | 1/3 | 99/99 → 99/99 | N/A | 11,82 | 3.081 |
| Products | 0,2 | 3/3 | 0/3 | 3/3 | 99/99 → 99/99 | N/A | 28,43 | 3.081 |
| Products | 0,5 | 3/3 | 1/3 | 3/3 | 96/99 → 99/99 | 1/1 | 34,06 | 5.363 |
| Books | 0 | 3/3 | 2/3 | 3/3 | 101/105 → 105/105 | 2/2 | 37,06 | 8.009 |
| Books | 0,2 | 3/3 | 3/3 | 3/3 | 99/105 → 105/105 | 3/3 | 69,93 | 8.008 |
| Books | 0,5 | 3/3 | 1/3 | 3/3 | 70/105 → 105/105 | 1/1 | 33,19 | 4.379 |
| Inventory | 0 | 0/3 | 3/3 | 1/3 | 159/171 → 159/171 | 0/3 | 156,93 | 19.401 |
| Inventory | 0,2 | 1/3 | 2/3 | 3/3 | 125/171 → 125/171 | 0/2 | 46,12 | 14.244 |
| Inventory | 0,5 | 2/3 | 3/3 | 3/3 | 122/171 → 129/171 | 2/3 | 44,20 | 16.199 |

Pilot mencatat 23 revisi pada 27 job valid. Penghentian karena kode identik terjadi pada 6/27 job valid dan 6/15 job yang menjalani revisi. Berdasarkan evaluator, perbaikan tuntas teramati pada 9/15 pasangan yang gagal sejak awal dan regresi pada 0/12 pasangan yang awalnya lulus. Penyebut tersebut mencakup pengulangan yang berkorelasi dan kode duplikat.

Suhu 0 menghasilkan satu kode awal unik pada masing-masing dari tiga seed products dan inventory. Suhu 0,2 dan 0,5 menghasilkan tiga hash awal unik pada setiap resource dalam grid ini. Pada inventory, suhu 0,5 memberi dua perbaikan tuntas dan satu job yang tetap 15/57. Karena jumlah pengulangan per kelompok kecil, hasil ini belum menetapkan suhu final atau menunjukkan efek kausal feedback spesifik.

Job inventory `resources/pilot-0013` mencatat 2.764,53 detik untuk satu attempt. Respons mentah Ollama mencatat sekitar 2.700,27 detik. Penyebab durasi ekstrem belum terkonfirmasi. Angka tersebut dipertahankan dalam total dan dilaporkan bersama median. Biaya yang tercatat adalah 81.765 token dari 50 respons dengan hitungan tersedia. Retry transport tanpa respons arsip tidak termasuk.

Agregat lengkap ada di `runs/pilot-2026-11-19/grid-complete-report.json`. SHA-256 file lokal `01da03760d024fe24f5b5e001a13cfc4d4a5b35a860eeceb2c986ad251185f96`. Setiap pasangan diverifikasi terhadap hash kandidat awal/akhir dan jumlah kasus acuan. Image dan suite acuan konsisten di dalam setiap kelompok.

## Catatan batch awal suhu 0

Pada checkpoint awal, enam dari 27 job selesai. Checkpoint ini melengkapi tiga seed untuk products dan books pada suhu 0. Semua enam job berstatus LOLOS dan memiliki evaluasi awal–akhir. Snapshot checkpoint ada di `runs/pilot-2026-11-19/progress-report.json`.

| Resource | Seed | Internal awal → akhir | Acuan awal → akhir | Revisi | Durasi attempt (detik) | Token prompt / keluaran |
|---|---:|---|---|---:|---:|---:|
| products | 42 | 14/14 → 14/14 | 33/33 → 33/33 | 0 | 24,31 | 606 / 421 |
| products | 43 | 14/14 → 14/14 | 33/33 → 33/33 | 0 | 11,82 | 606 / 421 |
| products | 44 | 14/14 → 14/14 | 33/33 → 33/33 | 0 | 11,62 | 606 / 421 |
| books | 42 | 12/12 → 12/12 | 35/35 → 35/35 | 0 | 187,67 | 573 / 398 |
| books | 43 | 11/12 → 12/12 | 33/35 → 35/35 | 1 | 24,59 | 1869 / 801 |
| books | 44 | 11/12 → 12/12 | 33/35 → 35/35 | 2 | 37,06 | 3168 / 1200 |

Products memakai harness internal v2 dan evaluator acuan development v1. Tiga seed products menghasilkan satu hash awal unik dari tiga kandidat. Books menghasilkan tiga hash awal unik. Books menunjukkan dua kegagalan awal dari tiga job dan dua perbaikan tuntas dari dua kandidat yang gagal di evaluator. Uplift masing-masing pasangan books yang direvisi adalah 5,71 poin persentase. Frekuensi berhenti kode identik adalah 0/6 untuk seluruh job valid, dan 0/2 di antara job yang menjalani sedikitnya satu revisi. Pengulangan dengan hash sama tetap tercatat. Perbandingan antar suhu memerlukan penyelesaian grid.

Laporan evaluator dapat ditelusuri melalui `source_run_id` pada enam `evaluation_result.json` di `evaluations/pilot-2026-11-19/`. Arsip model dan pengujian tiap job berada pada `runs/pilot-2026-11-19/{products,resources}/executions/`.

## Catatan uji awal dan cara melanjutkan

Pilot menjalankan konfigurasi awal untuk memeriksa alur eksperimen dan pencatatan. Grid yang disiapkan mencakup products, books, inventory_items, seed 42/43/44, dan suhu 0/0,2/0,5. Batasnya tiga revisi per job. Dua manifest di `runs/pilot-2026-11-19/` memisahkan runner products (9 job) dan runner generik (18 job).

Docker Engine 29.9.2, Python 3.13.7 dan PHP host 8.3.30 terdeteksi. Ollama 0.40.16 melaporkan `qwen2.5:7b-instruct` dengan kuantisasi Q4_K_M dan digest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`. Snapshot metadata ada di `runs/pilot-2026-11-19/environment.json`. Readiness books 27/27 dan inventory 46/46 tersimpan dalam folder resources pilot.

| Job | Suhu | Seed | Internal awal → akhir | Revisi | Alasan berhenti |
|---|---:|---:|---|---:|---|
| books, resources/pilot-0001 | 0 | 42 | 12/12 → 12/12 | 0 | all_checks_passed |

Attempt books berlangsung 187,674487 detik, termasuk waktu generasi dan pemeriksaan. Respons mentah Ollama melaporkan 573 token prompt, 398 token keluaran dan durasi server 60,921 detik. Pengukuran token berasal dari respons yang diterima; metadata pilot agregat masih menggunakan `null` untuk token. Kode awal SHA-256 `9b5d20621181028c92c9701e8010e685c85753b9d4ced85ba78675a611d17b74`. Arsip lengkap berada di `runs/pilot-2026-11-19/resources/executions/pilot-0001/`.

Evaluator books memperoleh 35/35 pada kode awal dan 35/35 pada kode akhir. Uplift 0 poin persentase, repair 0/0 (N/A), dan regresi 0/1. Kandidat sudah lulus sejak awal. Arsip evaluasi ada di `evaluations/pilot-2026-11-19/20261119T024815Z_evaluation_72ed447e2f844c40b687d083bfcfcefa/`.

Pada observasi pertama ini, ekstraksi awal berhasil 1/1, hash awal unik 1/1, dan kegagalan awal 0/1. Penghentian identik 0/1 secara keseluruhan dan N/A pada denominator job yang menjalani revisi (0). Biaya A/B dan kesimpulan sumatif masih terbuka. Review label manusia ditunda. [Panduan kerja dan review tim](../PANDUAN-KERJA-DAN-REVIEW-TIM.md)

Products v2 telah lulus readiness. Perintah berikut merekam cara grid dijalankan secara serial. Runner melewati folder job yang sudah dimulai, termasuk job ERROR atau interupsi. Simpan job tersebut untuk audit dan gunakan eksekusi baru yang terlacak jika perlu retry.

```powershell
python -m critic_agent pilot-run runs/pilot-2026-11-19/products/manifest.json --kind products --image sha256:3336feea72518efffcac6dc48d87eee65a78aa502c08c6d07393c82212ec90e4 --limit 1
python -m critic_agent pilot-run runs/pilot-2026-11-19/resources/manifest.json --kind resource --limit 1
```

Untuk membaca progres dari arsip aktual, jalankan:

```powershell
python -m critic_agent pilot-report runs/pilot-2026-11-19/products/manifest.json runs/pilot-2026-11-19/resources/manifest.json
```

Laporan JSON mengelompokkan job menurut hash spesifikasi, model, suhu, dan batas revisi. `INCOMPLETE` berarti folder job ada dan hasil terminal belum tercatat. Job yang sedang berjalan juga tampak sebagai `INCOMPLETE`. Denominator metrik operasional mengikuti eksekusi valid. Kegagalan awal mencakup kegagalan format, statis, dan dinamis pada eksekusi valid. Durasi hanya ditotal untuk job dengan data durasi lengkap. Token adalah jumlah yang tercatat dalam respons mentah, bersama jumlah respons yang menyediakan hitungan dan jumlah panggilan yang tercatat pada riwayat. Retry transport tanpa respons yang diarsipkan tidak dapat dihitung dari arsip tersebut. Periksa daftar image ID sebelum membandingkan konfigurasi.
