# Menjalankan dan membaca A/B final-v1

`ab-smoke`, `ab-plan-check`, `ab-run` dan `ab-report` menghubungkan paket final-v1 ke loop A/B yang sama. Paket, suite, image dan hasil historis tetap memiliki identitas masing-masing. Bukti implementasi: [verifikasi adaptor](evidence/final-ab-adapter-2026-11-23.md).

## Uji teknis tanpa Qwen

Jalankan dari root proyek dengan Docker Desktop Linux aktif:

```powershell
python -m critic_agent ab-smoke --resource categories --scenario repair --output runs/ab-synthetic --json
python -m critic_agent ab-smoke --resource categories --scenario format_fail --output runs/ab-synthetic --json
python -m critic_agent ab-smoke --resource categories --scenario syntax_fail --output runs/ab-synthetic --json
python -m critic_agent ab-smoke --resource categories --scenario already_valid --output runs/ab-synthetic --json
python -m critic_agent ab-report runs/ab-synthetic --json
```

Klien sintetis mengembalikan fixture lokal. Ia tidak memiliki transport HTTP dan tidak memanggil Ollama. Skenario dibedakan dalam cohort; hasilnya tidak mengukur kemampuan Qwen atau manfaat feedback pada populasi soal.

Kedua cabang menerima kode awal yang sama, opsi dan seed revisi yang sama. A menerima feedback spesifik internal; B menerima pesan generik tetap. Urutan cabang mengikuti `order_seed`. Evaluasi acuan dilakukan sesudah kedua loop, dengan satu hasil acuan awal bersama. Batas tiga revisi dan penghentian kode identik tetap berlaku. Tidak ada test acuan, profil acuan atau hasil acuan yang masuk prompt.

## Review dan pembekuan yang masih diperlukan

Paket siap dibagikan tersedia pada [panduan review manusia](review-packets/final-v1-2026-11-23/README.md), [ZIP bahan](review-packets/final-v1-2026-11-23/reviewer-bundle.zip) dan [form penugasan kosong](review-packets/final-v1-2026-11-23/forms/assignments.json). Paket memuat358baris pemeriksaan dan salinan bukti validasi, serta lampiran terpisah untuk16kasus komponen yang masih belum dilabeli manusia. Persiapan ini tidak mengesahkan review.

[Draf jadwal](evidence/final-ab-plan-2026-11-23.draft.json) berisi lima soal × empat pengulangan = 20 pasangan. Pemeriksaan berikut hanya membaca berkas dan mengembalikan `BLOCKED` sampai persyaratan lengkap:

```powershell
python -m critic_agent ab-plan-check docs/evidence/final-ab-plan-2026-11-23.draft.json --json
python -m critic_agent ab-report runs/ab-final --plan docs/evidence/final-ab-plan-2026-11-23.draft.json --json
```

Siapkan **manifest baru** untuk pembekuan; jangan menimpa draf atau bukti lama. `freeze-draft` development memakai format berbeda dan tidak otomatis menjadi protokol `ab-run`. Gerbang baru memeriksa:

1. Seluruh lima spesifikasi, hash paket/suite, image internal/acuan dan 20 slot unik beserta seed, pengulangan dan urutannya.
2. `configuration`: `model`, `model_digest` aktual, `endpoint` HTTP localhost, `options` dengan tepat `temperature`, `num_ctx`, `num_predict`, `max_revisions: 3`, serta `model_timeout_seconds` dan `test_timeout_seconds` positif. Seed berada dalam tiap slot jadwal. Nilai pilot tetap usulan sampai diputuskan.
3. `engine_source_sha256` dari `critic_agent.ab_archive.engine_manifest()[0]` untuk sumber yang benar-benar akan dipakai, `frozen_at` berzona waktu, `status: FROZEN`, dan `ready_for_final: true`. Mengganti dua flag terakhir saja tidak meloloskan gerbang.
4. Lima **attestation eksternal** pada `review_attestations`, masing-masing `{resource, path, sha256}`. `path` relatif terhadap root proyek, memakai `/`, dan berada di luar `evaluation/final-v1/`.
5. Keputusan manusia atas K2/jumlah-distribusi korpus pada P-06, penugasan dan bukti review silang pada P-07, keputusan FR-20 menurut PRD12.2, serta bukti validasi suite/image yang cocok.

Salin form kosong `evaluation/final-v1/review/<resource>.json` ke lokasi review eksternal. **Jangan mengisi form asli di dalam paket**: byte form tersebut ikut dalam hash paket tervalidasi. Catatan eksternal mempertahankan seluruh `case_id` form, berisi `resource`, `status: reviewed`, `human_author`, `reviewer` yang berbeda, `reviewed_at` sebelum/tepat pembekuan, `package_sha256`, `spec_sha256` dari manifest paket, dan `blank_form_sha256` dari form asli. Setiap keputusan harus `approved` dengan rationale yang menjelaskan review aktual. Sumber bukti tidak dapat membuktikan sendiri bahwa nama yang dicantumkan benar-benar melakukan review; tanggung jawab attestation tetap pada manusia yang menandatangani.

`decisions` memuat `status: approved`, `human_author`, `reviewer`, `reviewed_at`, `fr20: execute`, `component_review: reviewed`, serta `k2` dengan `precision_min_percent`, `recall_min_percent`, `fpr_max_percent` (0–100). `decisions.evidence_path` menunjuk catatan eksternal dengan isi sama tanpa field `evidence_path`. Ambang harus berasal dari keputusan aktual. Tidak ada persetujuan manusia yang dibuat otomatis.

`validation_evidence` adalah `{path, sha256}` ke ringkasan teknis `VALIDATED` yang mengikat paket dan image yang sama. `artifacts` berisi `{path, sha256}` untuk seluruh attestation, bukti keputusan dan bukti validasi. Seluruhnya diverifikasi dan disalin ke arsip pasangan. Hasil review yang mengharuskan perubahan soal/evaluator membutuhkan versi paket dan validasi baru, sebelum protokol dibekukan.

## Eksekusi sesudah protokol lolos

```powershell
python -m critic_agent ab-plan-check path/to/new-frozen-protocol.json --json
python -m critic_agent ab-run path/to/new-frozen-protocol.json --pair P01 --output runs/ab-final --json
```

Jalankan setiap slot P01–P20 tepat sekali. Klaim eksklusif disimpan di `<output>/<sha-protokol>/<slot>/execution.json`; klaim yang sudah ada memblokir generasi awal kedua. Kegagalan dan pembatalan dipertahankan. Jangan menghapus klaim agar hasil percobaan buruk dapat diganti. Jika protokol harus diperbaiki, dokumentasikan perubahan dan buat protokol baru.

Eksekutor memakai salinan protokol pada klaim. Digest model diamati sebelum dan sesudah setiap generasi, dan sumber, hash paket, opsi, seed, endpoint, image serta timeout diperiksa selama run. Satu kandidat awal dibuat baru; impor kandidat dan penggantian analyzer tidak diterima untuk run final.

## Membaca laporan

```powershell
python -m critic_agent ab-report runs/ab-final --plan path/to/new-frozen-protocol.json --json
```

Pembaca memverifikasi arsip lokal, hash artefak, kode, respons/prompt, receipt iterasi, identitas kasus uji dan ikatan protokol. Arsip final hanya memakai referensi path relatif di dalam pasangan. Path absolut lama dipertahankan sebagai informasi, bukan fallback pembacaan arsip final. Arsip development `products`/`resource` tetap dapat dibaca dengan pemeriksaan legacy yang lebih terbatas.

- `n_valid`: loop LOLOS/BELUM LOLOS per kondisi; `n_pair`: loop itu dengan evaluasi awal–akhir lengkap. `n_ab`: hanya pasangan dengan kedua evaluasi lengkap dan receipt eksekusi lengkap.
- Pass rate, uplift, repair, regresi, revisi, LOLOS dan penghentian identik dihitung per soal/kondisi. Denominator nol menghasilkan `null`, bukan nol persen.
- Kode tidak tersedia atau sintaks invalid memberi nol dengan alasan eksplisit. Gangguan lingkungan/evaluator tetap ERROR, bukan kegagalan fungsional yang diberi skor nol.
- Biaya revisi tersedia per kondisi; biaya generasi awal bersama dihitung sekali pada total pasangan. Token/retry yang tidak teramati tetap `null` dengan jumlah receipt yang tersedia. Status keluaran dan alasan evaluator tetap terlihat.
- Cohort memisahkan asal sintetis/development/final, protokol, paket, sumber, model/digest, opsi, anggaran dan skenario. Makro memakai bobot sama antarsoal, bukan pooling seluruh assertion.
- Duplikasi pair ID atau beberapa percobaan pada slot/protokol yang sama menjadi AMBIGUOUS, termasuk kegagalan klaim tanpa pasangan. Ini berlaku juga tanpa `--plan`. Seluruh slot yang belum dijalankan tetap terlihat bila `--plan` disertakan.
- Pasangan RUNNING menjadi INCOMPLETE dan `n_ab=0`; rincian cabang yang sudah selesai tetap tersedia. Arsip rusak menjadi INVALID tanpa menghentikan pembacaan pasangan lain.

Arsip `runs/`, `work/` dan image Docker diabaikan Git. Serahkan arsip lengkap bila hasil perlu diaudit di mesin lain; ringkasan Markdown/JSON dan kode saja tidak menyertakan seluruh receipt mentah. `ready_for_final` pada laporan deskriptif tetap false: laporan tidak memberikan attestation atau membekukan protokol.
