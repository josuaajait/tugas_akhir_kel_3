# Panduan Demo Semhas Critic Agent

Pegangan tim untuk demo 10–15 menit. Tunjukkan cara kebutuhan CRUD menjadi controller Laravel, cara Critic memeriksa perilaku kode, dan bagaimana hasil serta revisi dapat ditelusuri. Siapkan demo langsung dan arsip asli sebelum seminar.

Disusun 20 November 2026 berdasarkan bukti development sampai 19 November 2026. Hasil pilot dan A/B di panduan ini merupakan hasil formatif. Evaluasi sumatif masih menunggu pembekuan dan peninjauan.

### Pembagian peran saat demo

| Peran | Tugas |
|---|---|
| Narator | Menjelaskan tujuan, alur, hasil, dan batas klaim. Memberi isyarat perpindahan layar. |
| Operator | Menjalankan terminal, mengisi wizard, membuka kode dan arsip. Membaca status aktual sebelum narator menyimpulkan. |
| Penjaga waktu dan bukti | Menyiapkan arsip cadangan dan mencatat waktu. Peran ini dapat dirangkap bila presenter hanya dua orang. |

### Urutan demo selama 12 sampai 15 menit

| Waktu | Aksi di layar | Pesan yang harus tersampaikan |
|---|---|---|
| 0–1 menit | Tampilkan terminal dan gambaran alur. | Qwen menghasilkan satu controller; Critic memeriksa dengan aturan dan test. |
| 1–4 menit | Jalankan start dan isi spesifikasi meja. | Input divalidasi, dikonfirmasi, lalu disimpan sebelum model berjalan. |
| 4–6 menit | Tampilkan tahap persiapan dan hasil sesi. | Readiness memeriksa harness; LOLOS mengikuti pemeriksaan internal. |
| 6–9 menit | Buka arsip products dan feedback destroy. | Temuan memiliki bukti, masuk ke revisi, dan diperiksa ulang. |
| 9–12 menit | Tampilkan evaluator dan satu pasangan A/B. | Skor awal dan akhir dinilai terpisah dari feedback model. |
| 12–15 menit | Sampaikan ringkasan pilot dan keterbatasan. | Sistem berjalan; efektivitas umum masih perlu evaluasi akhir. |

> Kami mendemonstrasikan Critic Agent untuk self-debugging controller CRUD Laravel. Qwen membuat kode, lalu Critic memeriksa struktur dan perilakunya. Jika ditemukan masalah, sistem mengirim feedback dan meminta revisi maksimal tiga kali.

Jika waktu hanya 10 menit, ringkas pengisian input dan hasil pilot. Tetap tampilkan satu feedback nyata, hasil akhirnya, dan perbedaan pemeriksaan internal dengan evaluator acuan.


## Persiapan sebelum hari seminar

### Pemeriksaan dari root proyek

Buka PowerShell pada folder yang memuat critic_agent, harness, dan pyproject.toml. Contoh lokasi tim di bawah adalah workspace asli; gunakan root clone yang sebenarnya bila pindah komputer.

```powershell
Set-Location -LiteralPath "C:\Perkuliahan\TA"
python -m critic_agent --help
python -m critic_agent doctor
docker version
ollama list
```

Lanjutkan demo langsung bila doctor menunjukkan ready: true, docker version menampilkan Client dan Server, dan model qwen2.5:7b-instruct tersedia. Docker menggunakan Linux containers melalui WSL2. Jalankan pemeriksaan dari terminal pengguna jika akses dari Codex dibatasi.

### Persiapan image dan latihan

```powershell
python -m critic_agent harness-build --timeout 600
python -m critic_agent harness-build --image critic-laravel:products-internal-v2 --timeout 600
python -m critic_agent harness-check --image critic-laravel:products-internal-v2
python -m critic_agent resource-build examples/books.json --timeout 600
python -m critic_agent resource-check examples/books.json
```

Lakukan build sebelum hari seminar. Perintah pertama menyiapkan image dasar critic-laravel:dev yang dipakai start. Target readiness products v2 adalah 21/21 dan books 27/27. Angka readiness memeriksa harness, bukan skor kandidat Qwen. Wizard start membangun image sesi ber-UUID; persiapannya tetap dapat memakan waktu walaupun cache tersedia.

- Latih seluruh urutan pada laptop dan terminal yang akan dipakai, termasuk pembukaan arsip tanpa jaringan.
- Catat waktu generasi dan build aktual. Simpan satu sesi latihan lengkap sebagai cadangan, termasuk jika hasilnya BELUM LOLOS.
- Buka dua jendela terminal dan editor. Terminal pertama untuk start, terminal kedua untuk arsip. Gunakan font yang terbaca dari proyektor.
- Hubungkan charger dan tutup beban GPU yang tidak diperlukan. Siapkan dokumen ini secara lokal.

### Bahan yang wajib ikut bila pindah laptop

Git tidak membawa image Docker, model Ollama, maupun folder runs dan evaluations yang diabaikan. Salin arsip demo beserta log dan hasil pengujiannya secara terpisah. Uji kembali path pada laptop penerima. Jangan mengganti path atau hash dalam manifest historis untuk membuatnya tampak sesuai.

Siapkan minimal sesi meja, loop products, evaluasi products, dan pair.json A/B yang tercantum di halaman 8. Bila arsip tidak tersedia, gunakan ringkasan docs/evidence sebagai bukti dokumentasi dan sebutkan jenis buktinya dengan jelas.


## Demo langsung melalui input interaktif

### Mulai sesi baru

```powershell
python -m critic_agent start --seed 42 --temperature 0.2 --max-revisions 3
```

Suhu 0,2 dan seed 42 adalah konfigurasi development. Hasil live dibaca sebagaimana keluar; seed yang sama tidak menjamin keluaran identik di seluruh lingkungan.

### Isian contoh meja

| Pertanyaan wizard | Jawaban operator |
|---|---|
| Nama resource atau tabel | meja |
| Nama model | Meja |
| Nama controller | MejaController |
| Jumlah field | 3 |
| Field pertama | Nama size; tipe string |
| Batas dan unique field size | Minimum Enter; maksimum Enter; unik n |
| Field kedua | Nama status; tipe string |
| Batas dan unique field status | Minimum Enter; maksimum Enter; unik n |
| Field ketiga | Nama vip; tipe string |
| Batas dan unique field vip | Minimum Enter; maksimum Enter; unik n |
| Simpan dan jalankan self debugging | Periksa JSON, lalu jawab y |

Enter pada batas berarti tidak menambahkan min atau max. Ketiga field bertipe string dan wajib pada POST serta PUT. Field vip pada contoh ini diisi sebagai string. ID dan timestamp tidak dimasukkan sebagai field manual.

> Kami memasukkan kontrak CRUD melalui terminal. Sistem mendukung field string dan integer, lalu menampilkan JSON untuk dikonfirmasi. Setelah disetujui, spesifikasi dan riwayat sesi disimpan sebelum model dipanggil.

### Amati keluaran aktual

- Tunjukkan lokasi sesi, pemeriksaan prasyarat, build harness, dan readiness saat tahap tersebut tampil.
- Pada ringkasan akhir, baca status, stop_reason, revision_count, session_directory, dan run_directory.
- Jika langsung LOLOS, jelaskan bahwa kandidat pertama memenuhi pemeriksaan internal sehingga tidak perlu revisi. Lanjutkan ke arsip products untuk contoh perbaikan.
- Jika BELUM LOLOS atau ERROR, jelaskan penyebab dari keluaran aktual dan lanjutkan ke bukti arsip.

Bukti historis 12 November: sesi meja mencapai readiness 22/22 dan internal 14/14, LOLOS tanpa revisi. Angka tersebut adalah hasil arsip, bukan janji keluaran sesi baru.


## Menunjukkan hasil dan bukti revisi

### Buka hasil sesi yang baru selesai

Tempel session_directory dari output sesi baru pada pertanyaan PowerShell berikut. Jika sesi berhenti sebelum loop, baca session.json dan reason; run_directory dapat belum tersedia.

```powershell
$sesi = Read-Host "Tempel session_directory dari output start"
$hasil = Get-Content -LiteralPath (Join-Path $sesi "session.json") -Raw | ConvertFrom-Json
$hasil | Select-Object status, stage, stop_reason, revision_count, run_directory
if ($hasil.run_directory) {
  Get-Content -LiteralPath (Join-Path $hasil.run_directory "history.json")
}
```

### Buka contoh revisi products dari arsip

Umumkan perpindahan ke arsip 4 November. Loop ini memakai suite internal historis, bukan products internal v2. Hasilnya 13/14 menjadi 14/14 setelah satu revisi.

```powershell
$loop = "runs/20261104T031502Z_loop_713c3f8803f441929ae6ed8f38077232"
$hist = Get-Content "$loop/history.json" -Raw | ConvertFrom-Json
$hist | Select-Object status, stop_reason, revision_count
$hist.attempts | ForEach-Object {
  [pscustomobject]@{
    iterasi = $_.iteration
    dinamis = $_.dynamic_status
    lulus = $_.dynamic.summary.passed
    total = $_.dynamic.summary.total
  }
}
Get-Content "$loop/attempts/0/feedback.json"
```

> Pada arsip ini, method destroy menghasilkan HTTP 500, padahal kontrak meminta 204. Critic menyimpan lokasi method dan bukti error. Feedback dikirim ke Qwen, kemudian kandidat revisi diuji kembali dan mencapai 14 dari 14 test internal.

### Sorot perubahan kode di editor

Buka initial_controller.php dan final_controller.php di folder loop. Pada method destroy, kode awal memakai response()->setContent('', 204); kode akhir memakai response()->json('', 204). Tunjukkan perubahan beserta bukti hasil uji, tanpa menjalankan kandidat melalui PHP host.

history.json menghubungkan percobaan, temuan, dan hasil. attempts/0/feedback.json berisi feedback awal; folder attempts berikutnya memuat kandidat dan respons. Prompt, raw response, dan run_manifest.json dapat dibuka jika penguji menanyakan keterlacakan.


## Hasil evaluator dan eksperimen development

### Pisahkan skor internal dan skor acuan

LOLOS berarti seluruh pemeriksaan internal yang tersedia lulus. Evaluator acuan berjalan terpisah, menilai kode awal dan akhir dengan suite serta image yang sama dalam satu pasangan. Test dan hasil acuan tidak menjadi input feedback model.

| Bukti historis | Internal awal ke akhir | Acuan awal ke akhir | Makna |
|---|---|---|---|
| Products 4 November | 13/14 ke 14/14 | 31/33 ke 33/33 | Satu revisi; LOLOS internal. |
| Books 4 November | 12/12 ke 12/12 | 35/35 ke 35/35 | Benar sejak awal; bukan bukti repair. |
| Inventory 4 November | 11/16 ke 12/16 | 51/57 ke 53/57 | Berhenti kode identik; belum tuntas. |

### Pilot lengkap 19 November

Grid development mencakup 3 spesifikasi × 3 suhu × 3 seed, sehingga ada 27 job dan 27 pasangan evaluasi. Hasilnya 21 LOLOS internal dan enam BELUM LOLOS karena kode identik, dengan nol ERROR loop maupun evaluator pada grid yang dilaporkan.

- Rata-rata uplift per pasangan +5,55 poin persentase. Ini berbeda dari persentase run yang LOLOS.
- Repair 9/15 kandidat yang gagal acuan sejak awal; regresi 0/12 kandidat yang awalnya lulus acuan.
- Tercatat 23 revisi dan 81.765 token pada 50 respons dengan hitungan tersedia. Retry tanpa respons arsip tidak termasuk hitungan token tersebut.
- Enam penghentian identik berarti 6/27 job valid atau 6/15 job yang menjalani revisi. Penyebut harus disebutkan.

### Satu pasangan pembanding feedback A dan B

| Kondisi | Acuan awal ke akhir | Revisi dan status |
|---|---|---|
| A dengan feedback spesifik | 31/33 ke 33/33 | 1 revisi; LOLOS |
| B dengan feedback generik | 31/33 ke 31/33 | 2 revisi; BELUM LOLOS karena kode identik |

> Pada satu pasangan development, kedua cabang memakai kode awal identik dan jadwal seed revisi yang sama. A mencapai 33/33, sedangkan B tetap 31/33. Selisih akhirnya 6,06 poin persentase. Jumlah pasangan ini belum cukup untuk menyimpulkan manfaat umum feedback spesifik.

Pilot dan pasangan A/B ini menggunakan evaluator products development v1. Evaluator products v2 tersedia sebagai paket baru; hasil lama tetap mengikuti suite aslinya. Korpus komponen masih berlabel draf berbantuan AI dan belum ditinjau manusia secara independen. Hasil held-out dan sumatif belum tersedia.


## Skenario cadangan dan kendala saat demo

### Aturan perpindahan layar

Jika sekitar menit ke-6 hasil live belum tersedia, operator beralih ke terminal arsip dan menyebutkan bahwa sesi live masih berjalan. Sesi dapat dibiarkan berjalan selama tidak mengganggu penjelasan. Jika perlu dihentikan, gunakan Ctrl+C dan pertahankan arsip pembatalannya.

> Proses langsung belum selesai dalam waktu demo. Kami lanjutkan dengan arsip eksekusi sebelumnya yang memuat spesifikasi, kode, respons model, feedback, serta hasil pengujiannya. Status sesi hari ini tetap kami catat sesuai hasil aktual.

### Pilih respons sesuai kendala

| Kondisi | Tindakan operator | Penjelasan singkat |
|---|---|---|
| Pipe dockerDesktopLinuxEngine tidak ditemukan | Buka Docker Desktop sebelum demo dan tunggu Server tersedia. Jika tidak pulih cepat, gunakan arsip. | Endpoint engine belum tersedia. |
| Akses pipe atau socket ditolak | Coba terminal pengguna yang telah dilatih. Bila tetap gagal, tampilkan arsip. | Masalah izin akses dibedakan dari engine mati. |
| Ollama atau model tidak terjangkau | Periksa layanan lokal dan ollama list. Pemulihan atau unduh model dilakukan di luar slot demo. | Layanan model belum siap. |
| Build atau generasi memakan waktu | Beralih ke arsip setelah batas waktu. Jangan memulai banyak run paralel. | Durasi aktual bergantung lingkungan dan respons model. |
| Kandidat langsung LOLOS | Tampilkan status dan nol revisi, lalu buka arsip products. | Revisi hanya diperlukan jika ada temuan. |
| BELUM LOLOS atau kode identik | Tampilkan stop_reason, revisi dan temuan tersisa. | Sistem mempertahankan hasil yang belum berhasil. |
| Arsip hilang pada clone baru | Gunakan salinan arsip yang disiapkan; bila tidak ada, buka ringkasan docs/evidence. | Arsip mentah tidak otomatis ikut Git. |

### Pertahankan keutuhan bukti

Kandidat hanya dieksekusi di Docker. Pertahankan batas maksimal tiga revisi dan aturan byte-identik. Jangan memperbaiki kandidat sumber, menimpa log, atau mengubah hash agar demo tampak berhasil. Percobaan baru harus menghasilkan arsip baru. Hindari prune dan perubahan keamanan global saat pemulihan.

Hasil ERROR lingkungan tidak dihitung sebagai skor fungsional nol tanpa dasar. Skor acuan nol karena kode gagal sintaks adalah kasus berbeda dan perlu bukti lint sesuai protokol evaluator.


## Jawaban singkat untuk pertanyaan penguji

### Apa yang dihasilkan sistem

> Qwen menghasilkan satu controller Laravel untuk satu resource CRUD. Route, model, migration, fixture dan lingkungan uji disiapkan harness. Lingkupnya API JSON dengan field skalar string dan integer, tanpa autentikasi.

### Apakah Critic juga memakai model bahasa

> Pemeriksa Critic memakai validasi struktur, PHP lint dan tokenizer, serta pengujian perilaku dalam Docker. Qwen berperan membuat dan merevisi kode. Penilaian komponen dapat dijalankan tanpa memanggil Qwen.

### Mengapa masih perlu evaluator acuan

> Pemeriksaan internal dipakai dalam loop feedback dan memiliki cakupan terbatas. Evaluator acuan menilai awal dan akhir secara terpisah. Lulus internal tidak menjamin semua aturan kontrak telah diperiksa.

### Bagaimana jika sistem gagal memperbaiki kode

> Sistem menyimpan BELUM LOLOS beserta temuan tersisa. Loop berhenti bila semua pemeriksaan lulus, kode byte-identik, atau batas revisi tercapai. ERROR lingkungan dicatat terpisah. Inventory menunjukkan perbaikan sebagian yang belum tuntas.

### Apakah hasil saat ini membuktikan efektivitas

> Hasil pilot menunjukkan perubahan awal ke akhir pada paket development. Satu pasangan A/B sudah berjalan, tetapi belum cukup untuk menyimpulkan efek umum feedback spesifik. Evaluasi akhir memerlukan paket held-out, peninjauan independen dan konfigurasi beku.

### Bagaimana precision recall dan FPR dihitung

Unitnya satu contoh kode, dengan hasil per asal korpus. Sintetis: TP 6, FP 0, TN 2, FN 2; precision 6/6, recall 6/8, FPR 0/2. Qwen formatif: TP 3, FP 0, TN 2, FN 0 pada lima kode unik. Label masih draf berbantuan AI; hasilnya provisional. Dua FN sintetis tetap dihitung walaupun pelanggarannya reference_only. Held-out 0 sehingga metriknya N/A.

### Apakah penelitian sudah selesai atau mencapai 80 persen

> Implementasi dan bukti development sudah tersedia. M4 sumatif belum dijalankan dan review manusia ditunda. Persentase kesiapan semhas harus mengikuti rubrik program studi; jumlah fitur tidak langsung menjadi persentase kemajuan TA.

### Kalimat penutup demo

> Demo menunjukkan alur input, generasi, pemeriksaan, feedback dan revisi yang dapat ditelusuri. Hasil berhasil dan belum berhasil tetap disimpan. Tahap berikutnya adalah menuntaskan review serta pembekuan, lalu menjalankan evaluasi akhir sesuai manifest.


## Kartu operator dan lokasi bukti

### Perintah membaca bukti tanpa memanggil model

Jalankan dari root proyek. Perintah berikut membaca arsip lokal; pastikan seluruh folder sudah dipindahkan jika memakai laptop lain.

```powershell
$loop = "runs/20261104T031502Z_loop_713c3f8803f441929ae6ed8f38077232"
Get-Content "$loop/history.json"
Get-Content "$loop/attempts/0/feedback.json"

$ev = "evaluations/20261104T034743Z_evaluation_5b534ddeee604e72b59f70dec1be3339"
$nilai = Get-Content "$ev/evaluation_result.json" -Raw | ConvertFrom-Json
$nilai | Select-Object status, reason, expected_tests
$nilai.initial | Select-Object passed, total, pass_rate
$nilai.final | Select-Object passed, total, pass_rate

$ab = "runs/ab-development/ab_2154541b80e84a709c2e1792b0236097"
$pair = Get-Content "$ab/pair.json" -Raw | ConvertFrom-Json
$pair | Select-Object status, order, revision_seeds, n_ab, delta_final_pp
$pair.branches | ConvertTo-Json -Depth 6
```

### Bukti yang dibuka sesuai kebutuhan

| Materi | Lokasi relatif dari root proyek |
|---|---|
| Sesi meja historis | runs/20261112T131846Z_interactive_f0ec0996a862443a976cecf7b73bcfc3/session.json |
| Kode sebelum dan sesudah revisi | Pada folder $loop di atas: initial_controller.php dan final_controller.php |
| Ringkasan pilot | docs/evidence/pilot-development-2026-11-19.md |
| Pelaporan awal dan akhir | docs/evidence/fr-18-reporting.md |
| Bukti pembanding A/B | docs/evidence/fr-20-ab.md |
| Status dan kesiapan akhir | docs/STATUS-PROYEK.md dan docs/M4-M5-EVALUASI-DAN-LAPORAN.md |
| Komponen provisional | docs/evidence/component-provisional-2026-11-05.json |
| Kontrak dan metode | README.md, docs/spec-mvp.md dan PRD_Critic_Agent_v1.3.md |

### Pemeriksaan terakhir sebelum tampil

Pastikan input meja sudah dilatih, model dan engine siap, file cadangan dapat dibuka, terminal terbaca, serta narator mengetahui kapan beralih ke arsip. Setiap angka diucapkan bersama jenis suite, waktu bukti dan penyebutnya. Gunakan keluaran aktual untuk sesi hari ini.

Panduan ini mendokumentasikan langkah operasional dan bukti yang sudah tersedia. Sesi live baru tidak otomatis menghasilkan skor yang sama dengan arsip. Ikuti keputusan pembimbing untuk materi dan klaim yang disampaikan di seminar.
