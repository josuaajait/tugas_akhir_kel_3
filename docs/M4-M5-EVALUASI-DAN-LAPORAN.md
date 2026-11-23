# M4–M5 · Kesiapan eksekusi dan draf hasil development

Status per 19 November 2026. **M4 belum dijalankan. M5 sudah memiliki draf hasil formatif berdasarkan arsip development.** Dokumen ini menyatukan bukti yang tersedia untuk penyusunan laporan TA.

## M4 · Kesiapan eksekusi

Snapshot setelah implementasi FR-20 mencatat 102 entri artefak, termasuk sumber CLI terbaru, manifest pilot, bukti evaluator dan matriks development. Pemeriksaan hash menghasilkan `integrity: VERIFIED`, dengan `ready_for_final: false` dan `status: BLOCKED`. Snapshot terdahulu tetap dapat dirujuk sebagai catatan versi sebelumnya. [Manifest draf lokal](../runs/freeze-development-2026-11-19/draft-after-fr20.json)

| Gerbang sebelum M4 | Bukti yang masih dibutuhkan |
|---|---|
| Paket held-out | Spesifikasi, kandidat dan fixture akhir yang dipisahkan dari paket development dan dapat ditelusuri melalui manifest. |
| Validasi suite akhir | Bukti positif pada controller acuan, bukti negatif untuk pelanggaran target, serta matriks cakupan per aturan. Evaluator products v2 sudah menutup celah pengikatan record di development. [Bukti evaluator v2](evidence/products-reference-v2.md) |
| Review independen | Penugasan pembuat dan peninjau sudah dicatat. Review manusia ditunda, sehingga keputusan dan waktu pemeriksaan belum tersedia. |
| Ambang K2 | Ambang numerik dan distribusi kasus yang disepakati sebelum eksekusi sumatif. |
| Konfigurasi final | Model/digest, spesifikasi, image, prompt, suhu, urutan, seed, timeout, aturan berhenti dan jumlah pengulangan yang ditetapkan dalam manifest beku. |
| Rencana A/B final | FR-20 tersedia per pasangan. Grid final, urutan seimbang atau teracak, dan perhitungan lintas pasangan perlu ditetapkan sebelum M4. |

Sebagai **skenario anggaran**, batas bawah rancangan PRD adalah 5 spesifikasi × 3 pengulangan, yaitu 15 kandidat awal dan 30 cabang A/B. Dengan maksimal tiga revisi per cabang, batasnya 105 panggilan logis ke model. Kebijakan maksimal satu retry transport dapat menaikkan batas menjadi 210 percobaan HTTP. Jumlah akhir dan durasi perlu ditetapkan berdasarkan anggaran tim dan pengukuran perangkat. Satu attempt inventory pada pilot mencatat waktu sekitar 46 menit dan tetap dipertahankan pada arsip.

Ketika seluruh gerbang terpenuhi, M4 menjalankan manifest beku dalam urutan yang telah dicatat. Setiap pasangan menyimpan kandidat awal, kedua cabang, evaluasi awal bersama, evaluasi akhir per cabang, dan status. Pengecualian karena ERROR lingkungan harus dirujuk dengan ID dan penyebab. Jika diperlukan percobaan pemulihan, simpan hasil sebelumnya serta kandidat dan konfigurasi yang mendasari percobaan ulang. Perubahan paket setelah pembekuan memakai versi manifest baru. [PRD §12.6 dan §12.8](../PRD_Critic_Agent_v1.3.md)

## M5 · Hasil formatif untuk draf laporan

### Perubahan kesesuaian fungsional

Pilot faktorial mencakup 3 spesifikasi × 3 suhu × 3 seed. Seluruh 27 run valid memiliki pasangan awal–akhir dengan evaluator independen. Ada 21 LOLOS, enam BELUM LOLOS karena kode identik, nol ERROR loop, dan nol ERROR evaluator. Tercatat 23 revisi, setara 0,85 revisi per run valid.

| Resource | LOLOS internal | Perbaikan tuntas menurut acuan | Catatan |
|---|---:|---:|---|
| Products | 9/9 | 1/1 | Tiga dari tiga kode awal pada suhu 0 memiliki hash yang sama. |
| Books | 9/9 | 6/6 | Satu kandidat awal mendapat 0/35 karena gagal sintaks. Kandidat akhirnya lulus 35/35. |
| Inventory | 3/9 | 2/8 | Enam run yang belum lolos berhenti karena kode identik. |
| Seluruh pilot | 21/27 | 9/15 | Pada 12 pasangan yang awalnya lulus acuan, regresi 0/12. |

Rata-rata uplift adalah +5,55 poin persentase per pasangan. Enam penghentian identik terjadi pada 6/27 run valid dan 6/15 run yang menjalani revisi. Total 81.765 token teramati pada 50 respons. Arsip historis tidak merekam jumlah retry transport, sehingga jumlah retry tidak dapat direkonstruksi. [Ringkasan per resource dan suhu](evidence/pilot-development-2026-11-19.md) · [Laporan per run dengan hash, status, biaya dan evaluasi](../runs/pilot-2026-11-19/fr18-cli-report.json)

### Pembanding feedback spesifik dan generik

Satu pasangan development products memakai kandidat awal yang sama dengan skor 31/33. A mencapai 33/33 setelah satu revisi dan B tetap 31/33 setelah dua revisi, dengan alasan berhenti kode identik. Selisih akhir A–B adalah +6,06 poin persentase. A mencatat 1.349 token prompt dan 425 token keluaran revisi. B mencatat 2.393 token prompt dan 850 token keluaran revisi. Kandidat awal berasal dari arsip historis. Hasil ini menunjukkan satu pembanding berjalan pada konfigurasi dan contoh terpilih. [Bukti FR-20](evidence/fr-20-ab.md)

### Ketepatan deteksi Critic

Evaluasi komponen development memakai label draf berbantuan AI. Satu dari enam kandidat Qwen formatif duplikat dan tetap disimpan pada arsip. Metrik Qwen dihitung pada lima kandidat unik.

| Asal | Mentah / layak dihitung | TP/FP/TN/FN | Precision | Recall | FPR |
|---|---:|---|---:|---:|---:|
| Sintetis | 10/10 | 6/0/2/2 | 6/6 | 6/8 | 0/2 |
| Qwen formatif | 6/5 | 3/0/2/0 | 3/3 | 3/3 | 0/2 |
| Qwen held-out | 0/0 | — | N/A | N/A | N/A |

Dua FN sintetis terkait aturan batas panjang `title` dan nilai minimum `pages`. Keduanya tetap masuk denominator, dengan cakupan `reference_only`. Ketiga sumber dilaporkan sendiri karena mutasi sintetis dan kandidat formatif memiliki cara pemilihan berbeda. [Laporan komponen provisional](evidence/component-provisional-2026-11-05.json)

### Batas interpretasi dan bagian yang menunggu M4

Pilot memakai tiga kontrak Laravel, Qwen lokal Q4_K_M dan Docker Desktop WSL2. Kandidat dari spesifikasi atau hash yang sama berkorelasi. Skor internal dibatasi assertion yang tersedia. Aturan penghentian kode identik membatasi jumlah kesempatan revisi yang diamati. Skor final dan analisis lintas kondisi memerlukan grid A/B lengkap. Nilai komponen dengan review independen dan hasil held-out juga masih diperlukan. Laporan sumatif perlu mengisi konfigurasi beku, bukti peninjauan, hasil per pasangan, audit ERROR dan retry, serta keterbatasan lingkungan sesuai PRD.
