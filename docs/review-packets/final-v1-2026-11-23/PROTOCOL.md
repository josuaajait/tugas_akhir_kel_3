# Penggunaan formulir pada protokol

Semua command berikut dijalankan dari root repo asli, bukan dari folder ZIP. Draf input sudah berisi path formulir eksternal relatif root repo. ZIP adalah bahan review, bukan instalasi aplikasi/harness.

```powershell
python -m critic_agent ab-plan-check docs/review-packets/final-v1-2026-11-23/protocol-inputs.draft.json --json
```

Hasil yang benar saat persiapan adalah integrity VERIFIED, status BLOCKED, planned_pairs20. Kelengkapan bahan tidak mengisi persetujuan manusia atau digest model. Mengubah ready_for_final saja tidak memenuhi gerbang.

Setelah review aktual selesai, pengelola membuat **manifest baru**. Perbarui `review_attestations` dan entri `artifacts` dengan hash form yang sudah selesai; `decisions` harus sama dengan berkas keputusannya ditambah `evidence_path`. Lampirkan keputusan P-06/P-07 tambahan serta bukti komponen yang benar-benar memenuhi syarat. Hitung ulang hash setelah formulir kembali dari reviewer; jangan memakai hash kondisi kosong dari delivery.json sebagai hash hasil review.

Isi keputusan konfigurasi aktual, model_digest, frozen_at, engine_source_sha256, status dan kesiapan hanya sesudah pemeriksaan yang diperlukan. `engine_source_sha256` berasal dari seluruh sumber aplikasi saat freeze. Arsip materi di ZIP menjaga versi yang direview; bila sumber/soal berubah, ulangi review/validasi yang terdampak dan buat versi paket/protokol baru. Jangan menulis ulang bukti lama.

```powershell
python -m critic_agent ab-plan-check path/to/new-frozen-protocol.json --json
python -m critic_agent ab-run path/to/new-frozen-protocol.json --pair P01 --output runs/ab-final --json
python -m critic_agent ab-report runs/ab-final --plan path/to/new-frozen-protocol.json --json
```

Jangan menjalankan baris ab-run sebelum gerbang READY dan persyaratan manusia lengkap. Jalankan seluruh P01–P20 tepat sekali. Klaim slot, kegagalan dan pemulihan lingkungan dipertahankan; jangan menghapus klaim agar kandidat lain dapat mengganti hasil buruk. Tidak ada Qwen atau eksekusi final pada persiapan paket ini.
