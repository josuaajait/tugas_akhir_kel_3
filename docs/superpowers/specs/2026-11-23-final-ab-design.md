# Adaptor A/B final-v1 dan agregasi

Pengguna meminta kelanjutan implementasi (“oke gas”) setelah penjelasan adaptor A/B dan agregasi. Dokumen ini mencatat pilihan teknis Codex untuk lingkup tersebut; tidak mengesahkan review manusia atau menjalankan20pasangan akhir.

## Perilaku dan pendekatan

Gunakan mesin `run_ab` dan `_run_loop` yang sudah ada agar A/B memakai satu generasi awal identik, pembungkus prompt, seed per revisi, max3 dan penghentian identik yang sama. Tambahkan adaptor `ab_final.py` untuk paket final serta `ab_report.py` untuk agregasi. Alternatif menyalin seluruh loop menambah risiko kedua kondisi berbeda; mengganti suite/generator yang sudah tervalidasi tidak diperlukan. Paket evaluasi f2b648… dan image yang sudah diuji tetap dipertahankan.

Lingkup: adaptor loop/evaluator, feedback lokasi internal, preflight sintaks di Docker, arsip portabel, pembacaan protokol/pencegahan eksekusi draft, CLI smoke sintetis dan laporan gabungan. Pembekuan resmi, pengisian review, keputusan K2 serta eksekusi model akhir berada di tahap berikutnya. Semua software tetap Python standard library, aplikasi0.5.0/protokol komponen1.0.

## Adaptor dan arsip

`run_ab(kind='final', final_context=...)` menggunakan spec yang cocok persis dengan registry final-v1 dan dua FinalRunner dengan role/count/hash yang benar. Readiness internal dan acuan diselesaikan sebelum generasi. Referensi tidak masuk loop maupun feedback. Loop memakai `_run_loop` dengan count/contract final tanpa menyamar sebagai runner resource legacy. Nama dataset internal final dipetakan ke method pada feedback; isi generik B tetap teks tetap.

Evaluator memeriksa sintaks kandidat dengan PHP pada image evaluator yang dipin, di container terisolasi, tanpa eksekusi kode. Bukti parse-error dan cleanup berhasil berarti UNLOADABLE_CODE/0 test lulus/executed=false. Timeout/crash tak terjelaskan, laporan parsial atau cleanup gagal tetap ERROR. Tidak ada perubahan entrypoint, template, suite atau hash final-v1. Hasil evaluator memakai image/suite sama dan kode awal bersama cukup dievaluasi sekali.

Pair baru mencatat stage/origin/package/protocol/slot, konfigurasi, hash awal kode dan respons, kedua branch dan alasan berhenti, biaya aktual serta identitas evaluator. Semua input/sumber/adaptor dan berkas hasil yang tersedia diarsipkan dengan hash relatif di folder UUID. Kode awal impor disalin sebagai bukti, tanpa mengubah arsip asal. ERROR serta pembatalan mempertahankan branch yang sudah selesai dan branch yang belum dimulai. RUNNING tidak boleh menjadi sukses; kode/model/environment failures dibedakan sesuai PRD12.3.

## Eksekusi dan gerbang

CLI `ab-smoke --resource categories --scenario ...` memakai client fixture sintetis bawaan yang tidak terhubung Ollama. Dua kondisi tetap melewati loop/analisis statis/Docker/evaluator nyata. Skenario repair, sudah benar, gagal ekstraksi dan gagal sintaks memverifikasi alur; hasilnya diberi origin synthetic_validation dan tidak dianggap pengukuran manfaat feedback. Tidak ada generasi Qwen untuk kelima soal final sebelum freeze.

CLI `ab-plan-check MANIFEST` memeriksa integritas dan kesiapan tanpa model. `ab-run MANIFEST --pair P01` memakai konfigurasi/jadwal dari protokol yang disahkan saja, tanpa flag seed/image alternatif. Draft yang ada tetap BLOCKED dan ditolak sebelum client model dibuat. Protokol FROZEN harus mengikat paket/image/spec/suite, seluruh source prototipe, model/digest/options/timeout, jadwal unik/order/repetition, validasi paket, bukti review manusia berbeda, dan keputusan K2/FR20/komponen. Pemeriksaan hanya membaca attestation yang benar-benar tersedia; tidak membuat atau menyetujui review. Model identity aktual harus cocok sebelum dan sesudah panggilan generasi. Penerbit protokol beku resmi belum dibuat dalam lingkup ini.

## Pelaporan

CLI `ab-report RUNS [--plan MANIFEST]` membaca arsip tanpa Docker/model. Validasi ulang spec/kode/response/riwayat/evaluator/hash artefak, seed, budget, initial-sharing dan biaya dari bukti aktual. Path baru relatif pada pair sehingga snapshot bisa dipindahkan; path absolut historis tetap provenance. Laporan legacy didukung dengan assurance lebih terbatas dan cohort development tersendiri.

Unit utama satu kandidat awal/pasangan, bukan dua sampel independen. N_valid/N_pair per kondisi, N_AB pasangan lengkap. Skor, uplift, repair/regression (pembilang/penyebut), revisi, identical_code, ERROR, format/sintaks, hash unik/duplikat dan biaya dilaporkan per spec/kondisi. Tampilkan subset yang membutuhkan revisi terpisah. Ringkasan lintas spesifikasi berbobot sama; kelompok origin/stage/package/protokol/model/options/anggaran yang berbeda tidak digabung. Nol denominator adalah N/A/null. Token/transport tanpa bukti tetap tidak tersedia.

Dengan plan, setiap slot memiliki baris termasuk yang belum dimulai. Slot berisi beberapa eksekusi tanpa resolusi retry yang dapat dibuktikan diberi AMBIGUOUS dan dikeluarkan dari perbandingan, semua attempt tetap terlihat; tidak memilih hasil terbaik. Retry ERROR yang belum memiliki protokol pemulihan eksplisit tidak otomatis menjadi sampel independen. Arsip invalid/tamper dicatat dengan alasan dan tidak diberi metrik sukses. Source/package/image berbeda tidak dipool.

## Bukti dan batas

Tes unit menguji fairness, kegagalan ekstraksi/sintaks, ERROR cabang/evaluator, pembatalan, tamper, duplikat, penyebut nol, perbedaan ukuran kelompok, format legacy dan pencegahan model pada draft. Smoke Docker menggunakan fixture bertanda sintetis, bukan Qwen. Full Python suite dan hash paket/suite lama harus tetap lulus. Satu review kode segar setelah implementasi; itu bukan peninjauan assertion manusia. Checkout pengguna yang berisi dependensi belum di-commit dipertahankan; tidak ada commit/push otomatis.
