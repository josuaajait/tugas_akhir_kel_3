# Adaptor dan agregasi A/B final-v1 — 23 November 2026

Implementasi adaptor final-v1, gerbang protokol dan pelaporan selesai diverifikasi secara teknis. Empat pasangan fixture categories berjalan di Docker dan dibaca ulang oleh reporter sebagai EVALUATED. Tidak ada generasi Qwen, pelaksanaan grid final, pembekuan resmi atau attestation manusia. [Panduan operasi](../FINAL-AB.md) · [Ringkasan berhash](final-ab-adapter-2026-11-23.json).

## Perubahan dan validasi

`ab-smoke` memakai klien fixture tanpa transport HTTP. `ab-plan-check` membaca integritas dan kesiapan protokol. `ab-run` memerlukan protokol beku, lima review eksternal, keputusan manusia, digest/config aktual dan klaim slot eksklusif. Salinan protokol, sumber, paket, opsi/seed, endpoint, image dan timeout diperiksa saat eksekusi; digest model diamati sebelum/sesudah generasi. Kandidat awal baru dibagikan kepada kedua cabang. Loop max3, penghentian kode identik, feedback generik tetap dan evaluasi acuan sesudah kedua loop dipertahankan.

`ab-report` memeriksa hash dan path lokal relatif, receipt iterasi, raw response/prompt, kode, identitas kasus dan ikatan suite/image/protokol. Statistik dipisahkan menurut asal/protokol/sumber/model/config/skenario. Laporan menampilkan denominator nol sebagai null, kesalahan evaluator dan pasangan terputus, duplikasi pair/slot, biaya per kondisi dan generasi awal bersama satu kali; makro berbobot sama antarsoal. Tidak ada pooling sintetis dengan Qwen.

Verifikasi penuh sesudah perbaikan review: **253 tes Python lulus tanpa skip dalam 566.184 detik**. Perintah `python -m unittest discover -s tests -v`; log `work/ab-final/final-post-review-tests.log`, SHA-256 `6067e05f17785647e0f93a1484cced39d01198300942d962fce37c5eaaf33a96`. Help CLI dan pembacaan jadwal20slot diperiksa. `git diff --check` lolos setelah koreksi satu baris kosong dokumentasi.

Satu review kode AI baru menemukan delapan kelompok masalah: lokasi attestation bertabrakan dengan hash form paket, jalan pintas eksekusi/config/source, fallback path absolut final, ketidakcocokan receipt mentah, duplikasi slot/klaim gagal, interupsi/checkpoint evaluator, arsip malformed, serta biaya/status keluaran per kondisi. Enam regresi awal mereproduksi kegagalan; perbaikan dan regresi tambahan kemudian lulus. Ini review kode AI, bukan review assertion/label manusia. Semua nama/tanggal attestation dalam tes adalah fixture UNIT di direktori sementara yang dihapus, bukan bukti penelitian.

## Uji Docker sintetis aktual

| Skenario | Acuan awal | Acuan akhir A | Acuan akhir B | Revisi A/B | Penghentian B |
|---|---:|---:|---:|---:|---|
| already_valid | 42/42 | 42/42 | 42/42 | 0/0 | all_checks_passed |
| format_fail | 0/42 | 42/42 | 0/42 | 1/3 | max_revisions |
| repair | 38/42 | 42/42 | 38/42 | 1/1 | identical_code |
| syntax_fail | 0/42 | 42/42 | 0/42 | 1/1 | identical_code |

Semua memakai image categories internal/acuan yang sudah tervalidasi dan hash paket yang sama. Urutan syntax_fail adalah B→A; tiga skenario lain A→B. Readiness12/12 internal dan42/42 acuan diperiksa melalui runner aktual. Kode kandidat hanya dieksekusi di container terbatas; sintaks acuan diperiksa lewat PHP lint di image acuan. Host PHP dipakai oleh analyzer lint/tokenizer dan tes assertion tepercaya. Cleanup terverifikasi oleh receipt Docker. Semua empat pasangan EVALUATED, nol ERROR/INVALID/AMBIGUOUS; empat cohort terpisah. Total12 panggilan logis fixture, **nol panggilan generasi Qwen**. Token/retry tanpa pengamatan tetap null.

`format_fail` mempunyai initial UNAVAILABLE_CODE dan0%; `syntax_fail` mempunyai UNLOADABLE_CODE, diagnosis sintaks Docker dan0%. Lingkungan/evaluator yang gagal tetap ERROR tanpa kredit pasangan lengkap. `already_valid` menghasilkan0revisi pada kedua cabang. Hasil fixture ini hanya menguji alur; tidak mengestimasi efek feedback atau kemampuan Qwen.

Arsip mentah berada di `runs/ab-synthetic-2026-11-23/`; masing-masing pair/report/hash/image dan hasil kedua cabang tercatat pada JSON pendamping. Arsip runs/work dan image Docker tidak ikut Git. Snapshot sumber serta manifest paket disertakan dalam setiap pasangan; jangan mengubah arsip lama ketika dipindahkan.

## Batas dan pekerjaan berikutnya

Paket tetap `f2b648aeb042f4edcbb46b1b0160c87f93c326d084009cbc6de2f0f121e4a9b7`; sumber adaptor `020512666aaf479b8672dd4d8a00c82fa4cca30cded07bbf4236fa4ba3828a64`. Aplikasi0.5.0/protokol komponen1.0, kelima suite/image final, suite lama dan kandidat historis tidak diubah. Draf20pasangan tetap integrity VERIFIED / kesiapan BLOCKED; laporan rencana memuat20NOT_STARTED dan n_ab0. Form paket tetap kosong. Review aktual harus berupa lima attestation eksternal berhash agar form asli tidak mengubah hash paket.

Docker Engine29.9.2 terjangkau pada akses berizin dan keempat smoke berhasil. Doctor dalam sandbox tetap ready=false karena akses pipe Docker dan socket Ollama ditolak; ini keterbatasan akses sandbox, bukan bukti Docker tidak terpasang. Tidak ada konfigurasi keamanan global atau instalasi sistem yang diubah. Model/digest final belum diverifikasi dan belum dibekukan pada pekerjaan ini.

Berikutnya: review manusia atas assertion/label dan komponen, keputusan P-06/P-07/K2, konfigurasi/digest aktual, protokol baru yang beku, lalu seluruh20pasangan. Jangan menyimpulkan causal uplift dari fixture ini. Implementasi mempertahankan checkout yang sudah berisi perubahan pengguna; tidak ada commit/push otomatis.
