# Status Critic Agent, 23 November 2026

## Pembaruan paket soal dan evaluator akhir

Paket [final-v1](../evaluation/final-v1/README.md) berisi lima soal baru: categories, rooms, assets, courses dan shipments. Kelimanya lulus validasi Docker dengan70/70 readiness internal,358/358 readiness acuan,10 kontrol benar dan299 mutasi unik;648/648 pengamatan memenuhi harapan, termasuk pengulangan yang direncanakan. Seluruh218 tes Python lulus tanpa skip. [Bukti dan arsip gagal](evidence/final-v1-validation-2026-11-23.md). Semua label/assertion masih memerlukan review manusia; tidak ada Qwen atau A/B final yang dijalankan. [Draf20pasangan](evidence/final-ab-plan-2026-11-23.draft.json) kini memiliki path/hash/image lima soal, tetapi belum beku. Integrasi paket final ke A/B, agregasi, keputusan K2 dan konfigurasi final tetap terbuka.

Tabel berikut mempertahankan checkpoint development19November; pembaruan di atas supersede bagian yang menyebut spesifikasi/evaluator akhir belum tersedia.

Status mengacu pada PRD v1.3, arsip Docker, hasil pilot development, dan hasil unit test. Tim menunda review manusia atas label 16 kasus. Pekerjaan teknis pilot dan evaluator development dapat dilanjutkan selama penundaan ini.

| PRD | Status | Pekerjaan dan bukti |
|---|---|---|
| M1 · FR-01–04 | Teruji | Input JSON, wizard `start`, validasi kontrak v1, prompt dan ekstraksi PHP tersedia. Arsip live `start` untuk resource `meja` mencatat readiness 22/22 dan LOLOS 14/14 tanpa revisi. Unit test mencakup masukan invalid, pembatalan, dan kegagalan prasyarat. |
| M1 · FR-05–09 | Berjalan, audit cakupan terbuka | Kandidat berjalan di Docker dengan SQLite baru. Readiness products v2 21/21, books 27/27, inventory 46/46. Products v2 menolak fixture SKU tertukar yang lolos pada image lama. Cakupan validasi kandidat dan bentuk respons lain masih perlu ditinjau sebelum pembekuan. |
| M1 · FR-10–14 | Teruji | Feedback spesifik, loop maksimal tiga revisi, penghentian kode identik, ERROR dan arsip per percobaan tersedia. Loops development lama mencakup products 13/14 → 14/14, books 12/12 sejak awal, dan inventory 11/16 → 12/16 sebelum berhenti karena kode identik. |
| M2 · PRD §12.7 | 27/27 job dan pasangan selesai | 21 LOLOS, enam BELUM LOLOS karena kode identik, nol ERROR. Durasi, token, keragaman dan hasil acuan dicatat per resource dan suhu. Pemilihan konfigurasi final dan estimasi anggaran A/B masih terbuka. |
| M2/M3 · FR-16 | Pencatatan run terverifikasi live | Manifest baru mencatat hash sumber, identitas model, lingkungan dan identitas test. Riwayat mencatat seed efektif dan retry HTTP per panggilan. Jadwal seed A/B dan pembekuan konfigurasi akhir masih terbuka. [Bukti FR-16](evidence/fr-16-provenance.md) |
| M3 · FR-15 | Teruji untuk development | Evaluator products v2 memakai fingerprint dan image baru, lulus readiness 33/33 dan menolak fixture SKU tertukar yang lolos v1. Books dan inventory memakai evaluator 35/57 kasus. [Bukti products v2](evidence/products-reference-v2.md) |
| M3 · FR-17 | Implementasi tersedia, review ditunda | Laporan komponen provisional mencakup 16 observasi dan 15 kode unik per asal setelah deduplikasi. Matriks sintetis TP6/FP0/TN2/FN2 dan Qwen formatif TP3/FP0/TN2/FN0. Kedua FN tetap dihitung. |
| M3 · FR-18 | Terverifikasi untuk pilot | `pilot-report --evaluations` menghitung pass rate, uplift, repair, regresi, rata-rata revisi dan ERROR dari 27 pasangan aktual. Pelaporan per kondisi A/B menunggu FR-20. [Bukti FR-18](evidence/fr-18-reporting.md) |
| M3 · FR-19 | Draf terverifikasi, pembekuan tertahan | `freeze-draft` menyiapkan daftar artefak dengan SHA-256, konfigurasi pilot dan matriks development. `freeze-check` memverifikasi 101 entri. Paket held-out, validasi suite final, review, ambang K2, keputusan FR-20 serta konfigurasi final masih terbuka. [Bukti FR-19](evidence/fr-19-freeze-draft.md) |
| M3 · FR-20 | Terverifikasi pada satu pasangan development | `run-ab` menjalankan feedback spesifik dan generik dari kandidat awal identik dengan jadwal seed sama dan evaluator bersama. Uji live products menghasilkan 33/33 A dan 31/33 B. Grid final dan analisis lintas pasangan masih terbuka. [Bukti FR-20](evidence/fr-20-ab.md) |
| M4 | Tertahan | Snapshot setelah FR-20 berstatus integritas VERIFIED dengan 102 entri dan kesiapan BLOCKED. Eksekusi sumatif menunggu pembekuan. |
| M5 | Draf formatif tersedia | Draf menyatukan hasil 27 pasangan pilot, satu pasangan A/B development dan evaluasi komponen provisional. Bagian sumatif menunggu M4. [Kesiapan M4 dan draf M5](M4-M5-EVALUASI-DAN-LAPORAN.md) |

Sumber operasional mencakup [laporan pilot development](evidence/pilot-development-2026-11-19.md), [audit assertion products](products-internal-assertion-audit.md), [laporan komponen provisional](evidence/component-provisional-2026-11-05.json), dan [PRD v1.3](../PRD_Critic_Agent_v1.3.md).

Verifikasi kode terakhir menjalankan 177 tes Python tanpa kegagalan. Verifikasi live memakai Docker dan Ollama lokal.
