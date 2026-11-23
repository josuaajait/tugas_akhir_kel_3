# FR-19 · Persiapan pembekuan eksperimen

Paket draf mengikat protokol, sumber prototipe, prompt, spesifikasi development, Dockerfile, fixture, suite, matriks cakupan, manifest pilot, metadata model dan 27 laporan evaluator ke SHA-256. Entri memakai path relatif terhadap root proyek. Metadata mencatat konfigurasi pilot dan suite/image yang diamati pada arsip, bersama kolom rencana final untuk kasus held-out, pengulangan, konfigurasi, seed dan kondisi.

| Bagian | Status dan bukti |
|---|---|
| Daftar versi dan artefak development | 101 entri telah terverifikasi pada snapshot lokal, termasuk hasil pilot 27/27 pasangan |
| Matriks keterlacakan | Tersedia untuk tiga spesifikasi development, mencatat fixture, rule, test ID, cakupan dan hasil yang diharapkan. Status review tiap baris masih terbuka. [Matriks development](fr-19-traceability.md) |
| Validasi suite development | Readiness products v2, books dan inventory tersedia. Probe products membuktikan SKU tertukar terdeteksi di internal v2. Bukti tersebut berlaku pada paket development. [Audit products](../products-internal-assertion-audit.md) |
| Paket held-out dan validasi suite final | Belum tersedia. Unit evaluasi akhir belum diisi. |
| Review independen dan K2 | Review ditunda atas permintaan tim. Ambang K2 masih terbuka. |
| FR-20 dan konfigurasi final | Jadwal seed, kondisi, urutan, jumlah pengulangan serta keputusan A/B masih terbuka. |

Dari root proyek, pembuatan dan pemeriksaan snapshot memakai perintah berikut.

```powershell
python -m critic_agent freeze-draft runs/pilot-2026-11-19/fr18-cli-report.json --output runs/freeze-development-2026-11-19/draft.json
python -m critic_agent freeze-check runs/freeze-development-2026-11-19/draft.json
```

Pembuatan memakai mode eksklusif agar snapshot lama tetap tersimpan. Untuk snapshot baru, gunakan path baru. `freeze-check` menghitung ulang hash berkas yang terdaftar. Jika ada berkas hilang atau berubah, keluaran memuat `integrity: FAILED` dan path terkait. Arsip pilot berada di direktori Git-ignored, sehingga clone baru memerlukan arsip itu untuk memeriksa snapshot yang sama.

`integrity: VERIFIED` berarti byte artefak yang terdaftar cocok dengan snapshot. Sumber harness saat ini dan identitas image aktual dari pilot dicatat sebagai bukti terpisah. `status: BLOCKED` dan exit code 3 menunjukkan bahwa manifest masih draf. Implementasi ini menyiapkan dan memeriksa paket development. Mode pembekuan serta eksekusi paket final menunggu pemenuhan gerbang PRD §12.6 dan kelengkapan pelaporan §12.8.
