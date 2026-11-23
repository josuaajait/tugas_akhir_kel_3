# Validasi teknis paket final-v1 — 23 November 2026

**Lima soal dan evaluatornya telah diimplementasikan serta divalidasi di Docker.** Seluruh648 pengamatan pada sumber akhir memenuhi harapan, tanpa FAIL/UNKNOWN atau pengamatan yang belum dijalankan. Seluruh218 tes Python lulus tanpa skip dalam234,489detik. Ini bukti kesiapan teknis evaluator; **A/B final belum dijalankan dan paket belum dibekukan**.

[Soal dan panduan](../../evaluation/final-v1/README.md) · [Manifest paket](../../evaluation/final-v1/manifest.json) · [Ringkasan JSON beserta hash dan semua percobaan](final-v1-validation-2026-11-23.json) · [Draf pemetaan20pasangan A/B](final-ab-plan-2026-11-23.draft.json).

## Hasil yang benar-benar dijalankan

| Soal | Readiness internal | Readiness acuan | Kontrol benar | Mutasi unik | Pengamatan sesuai harapan |
|---|---:|---:|---:|---:|---:|
| categories | 12/12 | 42/42 | 2 | 39 | 88/88 |
| rooms | 12/12 | 50/50 | 2 | 44 | 98/98 |
| assets | 14/14 | 73/73 | 2 | 62 | 134/134 |
| courses | 14/14 | 77/77 | 2 | 63 | 136/136 |
| shipments | 18/18 | 116/116 | 2 | 91 | 192/192 |
| Total | **70/70** | **358/358** | **10** | **299** | **648/648** |

Kedua gaya kontrol benar diterima pada internal dan acuan, termasuk pengulangan. Seluruh299 mutasi unik terdeteksi pada testcase acuan yang dipetakan. Pada internal, hasil mutasi mengikuti cakupan yang dideklarasikan: pelanggaran reference_only tetap harus lolos internal. Ada40 pengamatan kontrol benar dan608 pengamatan mutasi, termasuk pengulangan kedua kontrol benar dan satu mutasi pertama per soal/role.

`PASS` dalam laporan adalah **hasil pengamatan sesuai harapan**. Testcase pada controller yang sengaja salah memang gagal; itu bukan controller yang dinyatakan benar. Angka ini bukan precision/recall Critic, jumlah kandidat Qwen, atau ukuran efektivitas A/B. Tidak ada panggilan Qwen dalam pekerjaan ini.

Hash paket yang benar-benar divalidasi:

`f2b648aeb042f4edcbb46b1b0160c87f93c326d084009cbc6de2f0f121e4a9b7`

Kelima resource memakai base image ID yang sama, dipin sebelum build. Probe tepercaya di container memverifikasi **PHP8.3.36**, Laravel`v12.70.2`, PHPUnit`11.5.57`, dan hash Composer lock. PHP host tetap8.3.30; kedua versi ini tidak disamakan. Image internal/acuan berbeda dan ID hasil build dicocokkan dengan ID readiness serta seluruh pengamatan. ID lengkap, hash suite/spec, source asli/kanonik dan lokasi raw evidence tersimpan dalam JSON serta manifest.

## Cakupan, isolasi dan kontrol mutu

Paket baru menutup dua celah dari [audit awal](final-evaluator-audit-2026-11-23.md): pengikatan nilai pada ID record dan pembeda JSON array/object sebelum decoding asosiatif. Fixture internal membedakan field dalam record; profil acuan memakai nilai yang disusun terpisah. Internal mencakup CRUD, omitted-required dan missing-ID; tipe/min/max/unique serta vektor tambahan tetap reference_only.

Validasi memeriksa PHP lint, discovery PHPUnit yang sesungguhnya, enumerasi setiap dataset, kecocokan katalog/diff/matriks tersimpan, serta pengamatan controller di container dengan DB baru. Kegagalan negatif diberi kredit hanya jika testcase, fase assertion dan status HTTP aktual cocok dengan target. HTTP500 atau kegagalan yang tidak terjelaskan tidak diberi kredit. Target internal harus eksplisit; hasil parsial, skip/error, perubahan sumber/image, cleanup gagal atau pengulangan berbeda menjadi ERROR/UNKNOWN.

[Inspeksi kelima image internal](final-v1-image-isolation-2026-11-23.json) membaca file di container terisolasi dan memverifikasi hash aktual suite/profile. Direktori final hanya memuat Assertions.php, FinalInternalTest.php dan profile.json dengan dataset internal. Tidak ada direktori acuan, test legacy, atau implementasi rangkaian CRUD acuan yang tertinggal. Seluruh cleanup probe berhasil. Kandidat/kontrol fungsional tidak pernah dieksekusi di host.

Satu review kode oleh agen AI menemukan masalah discovery nama berkas PHPUnit, identitas classname JUnit, bukti mutasi yang terlalu longgar, fixture, provenance, isolasi, runtime/base dan finalisasi arsip. Temuan ditindaklanjuti dengan regresi RED→GREEN serta verifikasi Docker. Pengamatan live juga membuktikan bahwa mutasi target update gagal pada fase pengikatan ID/state; katalog diperbaiki melalui regresi. Guard pembatalan dan timeout nonfinite diuji sebelum pemeriksaan penuh terakhir.

## Percobaan yang dipertahankan

Indeks JSON mencatat18 invokasi nyata sampai snapshot ini:2 pemeriksaan lokal,6 ERROR pada persiapan/pemetaan/integritas paket terdahulu,5 run lengkap pada sumber development sebelum guard final, dan5 run lengkap pada hash akhir di atas. Data antarpaket tidak digabung untuk menyatakan kelulusan sumber akhir. Perubahan sumber yang terjadi saat run lama berlangsung tetap tercatat sebagai kegagalan integritas; tidak ada penggantian hash atau penghapusan arsip agar terlihat lulus.

Lima arsip utama untuk diserahkan terpisah dari Git:

| Soal | Direktori di `evaluations/final-validation/` |
|---|---|
| categories | `20261123T035440Z_final-validation_1a58f61e268b498889859ccd8215bb6d` |
| rooms | `20261123T035455Z_final-validation_9fa4c953afd248c2acb2bddbd38a990c` |
| assets | `20261123T035510Z_final-validation_1de34185ff994cf089c9f0d0655091be` |
| courses | `20261123T035525Z_final-validation_29ea47c0138f40eba110d13dd7f85799` |
| shipments | `20261123T035540Z_final-validation_6cc4e84f8728460393d9abe6adf0523d` |

Sertakan pula percobaan lain dalam indeks untuk audit lengkap dan log `work/final-v1/final-verification-tests.log` yang hash-nya tercatat pada ringkasan. Tiap arsip memuat snapshot byte asli sumber, kode kontrol/diff, profil/spec, matriks dengan hasil per baris, build/runtime/readiness, observation JSON serta raw stdout/stderr/JUnit. Jangan menyunting manifest lama untuk memindahkan path absolut; pulihkan arsip pada path relatif yang sama atau buat run baru. Image Docker perlu dibagikan atau dibangun kembali.

## Keputusan dan batas pekerjaan

- Pekerjaan tetap pada checkout pengguna yang memuat dependensi belum di-commit. Tidak ada reset, migrasi worktree, commit, push atau penggabungan perubahan lain.
- Pengulangan stabilitas mencakup semua kontrol benar dan mutasi pertama per resource/role; kestabilan seluruh mutasi pada banyak pengulangan tidak diestimasi.
- Mutasi tipe/unique/required-store menerima input invalid secara sengaja melalui guard terkendali. Ini mengisolasi pelanggaran kontrak tanpa memberi kredit pada crash constraint DB; tidak diklaim mewakili distribusi kesalahan Qwen.
- Source snapshot menyimpan byte asli dan hash kanonik tambahan; aturan LF hanya berlaku pada paket baru. Perubahan byte/sumber memerlukan hash dan build yang sesuai, tanpa mengubah hasil historis.
- Review AI dan validasi teknis tidak menggantikan review manusia atas assertion/label. Semua formulir review tetap pending dengan nama/tanggal/keputusan kosong.

Versi aplikasi0.5.0, protokol komponen1.0, suite/generator legacy serta kandidat historis dipertahankan. Enam fingerprint suite legacy diverifikasi oleh tes. Tidak ada minor review yang dibiarkan mengubah klaim teknis.

## Sebelum A/B final

Draf baru sudah mengikat S1–S5 ke spesifikasi, hash, suite dan image aktual sambil mempertahankan jadwal20pasangan sebelumnya. Statusnya tetap DRAFT, konfigurasi model belum beku dan digest final kosong. Selanjutnya diperlukan adaptor paket final ke A/B, agregasi per spesifikasi/kondisi, review manusia serta keputusan P-06/P-07/K2 dan pembekuan model/protokol/manifest sebelum menjalankan seluruh jadwal. `run-ab` development saat ini belum menerima kelima soal tersebut sebagai paket final.
