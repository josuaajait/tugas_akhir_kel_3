# Persiapan Semhas · Critic Agent

Dokumen ini merangkum bukti yang sudah tersedia dan keputusan yang perlu dikonfirmasi sebelum menyiapkan paket akhir. Angka 80% mengacu pada batas yang disampaikan tim. Cara menghitungnya masih perlu dicocokkan dengan rubrik program studi.

## Bukti yang bisa ditunjukkan

| Materi | Bukti development |
|---|---|
| Demo sistem | CLI `start` menerima spesifikasi CRUD, memvalidasi dan menyimpannya, menyiapkan Docker, lalu menjalankan Qwen dan Critic. Arsip `meja` mencatat readiness 22/22 dan internal 14/14. |
| Evaluasi awal–akhir | Pilot lengkap 27 pasangan. Uplift rata-rata +5,55 poin, repair 9/15, regresi 0/12. |
| Pembanding feedback | Satu pasangan products dengan kandidat awal identik menghasilkan skor akhir A 33/33 dan B 31/33. |
| Perbaikan cakupan | Products internal v2 dan evaluator products v2 masing-masing menolak fixture respons dengan SKU antar-record tertukar. |
| Metodologi dan laporan | Draf M4–M5 memisahkan bukti pilot, pembanding A/B development, dan evaluasi komponen provisional. |

[Status proyek](STATUS-PROYEK.md) · [Draf M4–M5](M4-M5-EVALUASI-DAN-LAPORAN.md) · [Bukti evaluator products v2](evidence/products-reference-v2.md)

## Keputusan pembimbing

Pada 19 November 2026, tim memilih **opsi seimbang**, yaitu 5 spesifikasi × 4 pengulangan. Draf memuat 20 pasangan dan 40 cabang, dengan dua urutan A→B dan dua B→A per spesifikasi. Seed awal dan tiga seed revisi tersimpan per slot; kedua kondisi memakai jadwal revisi yang sama. Batasnya 140 panggilan logis atau 280 percobaan HTTP jika setiap panggilan memerlukan satu retry. [Draf jadwal M4](evidence/semhas-m4-balanced-plan.json)

Jadwal memakai slot S1–S5 sampai kontrak akhir ditetapkan. Suhu 0,2, paket `semhas-m4-v1`, evaluator products v2 dan ambang K2 precision ≥80%, recall ≥75%, FPR ≤20% dicatat sebagai usulan. Konfirmasi final dan bukti gerbang FR-19 diperlukan sebelum jadwal ini menjadi manifest eksekusi.

1. **Batas 80%.** Konfirmasikan bobot implementasi, eksperimen, dan penulisan, serta bukti hasil yang diperlukan saat seminar.
2. **Lingkup sumatif.** Bawa usulan 5 spesifikasi × 4 pengulangan untuk disepakati dan tentukan kontraknya. Evaluator development yang tersedia sekarang mencakup tiga spesifikasi. Kontrak tambahan memerlukan profil acuan yang tervalidasi.
3. **Review dan K2.** Konfirmasikan apakah review 16 kasus serta keputusan ambang K2 diperlukan sebelum Semhas. Review tim saat ini ditunda. Jika protokol sumatif tetap seperti PRD, selesaikan review independen dan sepakati ambang sebelum pembekuan.
4. **Paket held-out.** Tetapkan penjaga paket dan batas akses. Pengujian independen perlu dikembangkan dan ditinjau pada kontrak yang dipilih. Simpan paket final terpisah dari materi yang dipakai untuk menyetel Critic.

## Urutan teknis setelah lingkup disepakati

1. Buat daftar kontrak dan matriks cakupan final, termasuk versi evaluator yang dipakai. Validasi setiap suite dengan controller acuan serta fixture pelanggaran target. Evaluator products v2 menyediakan contoh prosedur yang sudah berjalan.
2. Tetapkan suhu, digest model, image ID, jadwal seed dan urutan A/B, timeout serta jumlah pengulangan. Selesaikan gerbang review sesuai lingkup yang disepakati dan kunci paket versi baru.
3. Jalankan manifest secara serial dan simpan hasil setiap pasangan, termasuk kegagalan dan retry. Lengkapi Bab Hasil dengan skor awal–akhir, status, biaya, dan analisis A/B bila tersedia.
4. Siapkan demo dari spesifikasi yang sudah terverifikasi dan satu arsip pasangan lengkap sebagai bukti cadangan untuk presentasi.
