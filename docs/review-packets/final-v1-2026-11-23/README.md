# Paket review manusia final-v1

Status: **siap dibagikan untuk diperiksa, belum direview atau disetujui manusia**. Disiapkan OpenAI Codex pada23November2026. Nama pembuat manusia, reviewer, waktu pemeriksaan, keputusan dan rationale dalam formulir baru sengaja kosong.

Hash paket yang diperiksa: `f2b648aeb042f4edcbb46b1b0160c87f93c326d084009cbc6de2f0f121e4a9b7`.

Mulai dari [checklist](CHECKLIST.md), lalu [penugasan](forms/assignments.json). Bahan lengkap tersedia dalam `reviewer-bundle.zip` di folder pengiriman. Ekstrak ZIP ke folder baru sebelum membagikannya; seluruh tautan bahan di dalam paket dapat dibuka tanpa arsip `evaluations/` pada mesin asal. Folder `materials/` lokal diabaikan Git dan disertakan di ZIP. Jika menerima clone Git, gunakan ZIP untuk memperoleh bahan tersebut. Kembalikan formulir hasil review sebagai berkas baru atau salin kembali ke `forms/` setelah diperiksa pengelola; jangan menimpa bukti lama.

## Apa yang diperiksa

| Soal | Lembar pemeriksaan | Form eksternal | Internal / acuan | Kontrol benar / mutasi |
|---|---|---|---:|---:|
| categories | [42 kasus](worksheets/categories.md) | [categories.json](forms/categories.json) |12 /42|2 /39|
| rooms | [50 kasus](worksheets/rooms.md) | [rooms.json](forms/rooms.json) |12 /50|2 /44|
| assets | [73 kasus](worksheets/assets.md) | [assets.json](forms/assets.json) |14 /73|2 /62|
| courses | [77 kasus](worksheets/courses.md) | [courses.json](forms/courses.json) |14 /77|2 /63|
| shipments | [116 kasus](worksheets/shipments.md) | [shipments.json](forms/shipments.json) |18 /116|2 /91|
| Total |358 kasus acuan unik per resource/case_id|5 formulir|70 /358|10 /299|

Paket berisi650 berkas sumber yang terikat hash paket, spesifikasi, profil fixture acuan, assertion internal/acuan, kontrol benar, mutan beserta diff, matriks sumber, salinan matriks hasil validasi, lima laporan validasi mentah, serta ringkasan bukti teknis. Kelengkapan dan hash ada pada [manifest bahan](materials/material-manifest.json). `delivery.json` mencatat hash ZIP dan hash awal formulir; berkas itu berada di luar ZIP untuk menghindari hash melingkar, dan dapat dibagikan bersama ZIP. Bahan teknis adalah bukti validasi sebelumnya, bukan peninjauan manusia baru atau hasil model final.

## Cara memeriksa satu soal

1. Baca spesifikasi dan kontrak respons pada bahan panduan. Cocokkan tipe field, required/null/empty, batas panjang/nilai, unique, status HTTP, bentuk JSON dan perubahan database yang diminta.
2. Periksa assertion PHP yang benar-benar menjalankan setiap `reference_test_id`, bukan hanya judul kasus. Lembar kerja menyediakan `case_id`, rule, fixture/expected body/state dan kontrol yang dipetakan. Periksa ID integer dan pengikatan nilai ke ID, koleksi array asli, target record yang tepat, record lain tetap utuh, validasi update serta tidak adanya mutasi saat422/404.
3. Cocokkan pemetaan internal. `internal_covered` berarti ada test internal yang disebut; `reference_only` berarti test internal kosong. Jangan menyimpulkan cakupan Critic dari kelulusan suite acuan saja.
4. Periksa kedua gaya kontrol benar dan mutasi/diff target. Pada bukti validasi, **PASS berarti hasil sesuai harapan kontrol**: kontrol benar diterima, mutan ditolak pada assertion target, dan ekspektasi internal cocok. PASS pada mutan tidak berarti controller mutan lolos acuan. HTTP500/constraint crash bukan pengganti bukti assertion yang dimaksud.
5. Pembuat manusia memeriksa dan menulis alasan; reviewer lain memeriksa silang. Catat perbedaan dan penyelesaiannya. Untuk setiap `case_id`, isi `decision` dan `rationale` pada form soal. Gunakan `approved` hanya setelah pemeriksaan nyata; gunakan `changes_required` atau `uncertain` jika belum dapat disahkan. Pilihan selain approved menahan freeze.

Isi metadata top-level `human_author`, `reviewer`, `reviewed_at` dan `status: reviewed` hanya setelah seluruh kasus selesai dan disepakati. Kedua nama harus berbeda; gunakan waktu sebenarnya dengan zona waktu. Isian nama/waktu per kasus dapat merekam pemeriksa dan tanggal masing-masing. `package_sha256`, `spec_sha256` dan `blank_form_sha256` sudah disiapkan sebagai ikatan sumber dan tidak boleh diubah untuk menyamarkan perubahan materi. Jangan mengisi form asli di `materials/evaluation/final-v1/review/` atau di paket sumber proyek; gunakan `forms/`.

Keputusan dengan perubahan assertion/soal memerlukan versi paket dan validasi baru sebelum freeze. Jangan mengubah sumber lama, menyesuaikan hasil, menghapus kasus reference_only, atau menyatakan semua kasus disetujui berdasarkan otomatisasi650hash/648pengamatan saja.

## Keputusan tim dan pembimbing

Gunakan [form keputusan](forms/decisions.json) dan [lembar keputusan](DECISIONS.md). K2/P-06 membahas jumlah/distribusi korpus serta ambang precision/recall/FPR. P-07 membahas penugasan dan bukti peninjauan silang. Keputusan melakukan FR-20/A/B dibahas terpisah menurut PRD12.2. Seluruh field keputusan masih pending/null; jumlah20pasangan dan konfigurasi development adalah rencana/usulan yang harus dinyatakan dalam protokol akhir, bukan persetujuan pembimbing yang diasumsikan.

## Review label komponen dipisahkan

Salinan **paket komponen16kasus yang sudah ada** tersedia di [materials/component-review/README.md](materials/component-review/README.md). Bagikan hanya direktori itu kepada pembuat label/reviewer komponen. Isinya kode, spesifikasi dan bukti acuan development, tanpa usulan label AI atau prediksi Critic per kasus. `author-decisions.json`, `reviewer-decisions.json` dan `decisions.json` masih kosong. Penugasan lama yang tertulis di sana berasal dari permintaan pengguna12November; itu bukan bukti review selesai, dan tidak menetapkan reviewer lima soal final ini.

Bukti komponen memakai suite development lama. Baca juga audit assertion pada bahan panduan; kelulusan suite lama bukan bukti lengkap kebenaran. Prediksi/label draft yang pernah dilihat tidak menjadi tidak terlihat hanya karena menerima paket baru. Isi `previous_prediction_exposure` dan attestasi blind sesuai keadaan sebenarnya. Jika blind review tidak mungkin, gunakan peninjau/kasus pengganti yang disepakati; jangan mengesahkan label sebagai reviewed-only melalui attestasi fiktif. Setelah review yang memenuhi syarat, buat salinan korpus baru dan lakukan prediksi baru sesudah waktu review. Tidak ada label yang dipromosikan atau prediksi baru dalam persiapan paket ini.

## Setelah formulir dikembalikan

Pengelola memeriksa kelengkapan, dua identitas manusia yang berbeda, waktu sebenarnya, seluruh keputusan358kasus, evidence komponen dan penyelesaian perbedaan. Keputusan komponen `reviewed` tidak boleh diisi hanya karena formulir soal selesai.

[Input protokol draf](protocol-inputs.draft.json) sudah menunjuk formulir eksternal dan bukti validasi yang cocok, sambil mempertahankan20slot seed/urutan. Draf ini **tetap BLOCKED**, tidak membuat model, tidak membekukan protokol dan tidak memberi persetujuan. Path di dalam draf relatif terhadap root repo asli; jika formulir yang kembali disimpan di lokasi baru, perbarui path pada manifest baru. Setelah formulir berubah, hitung ulang seluruh hash attestation/keputusan dan entri `artifacts` pada manifest baru. Hash awal pada delivery.json adalah bukti kondisi kosong saat persiapan, bukan hash keputusan sesudah review.

Verifikasi digest/config/model aktual, sumber, image, timeout dan keputusan manusia sebelum membuat protokol baru berstatus FROZEN. Jalankan gerbang read-only sesuai [panduan protokol](PROTOCOL.md). Pelaksanaan20pasangan hanya dimulai sesudah gerbang siap; seluruh kegagalan/pemulihan tetap disimpan.

## Batas distribusi dan bukti

Paket assertion ini terbuka untuk membaca test/kontrol dan **tidak disebut paket blind**. Lampiran komponen tetap memiliki syarat paparan prediksi tersendiri. Arsip raw Docker lengkap dan image tidak disertakan: laporan validasi menyimpan observasi terstruktur, sedangkan path historis di dalamnya tetap provenance dan tidak ditulis ulang. Verifikasi ulang fungsional membutuhkan lingkungan Docker dan sumber asli proyek. Tidak ada kandidat yang dijalankan di host, tidak ada Qwen, commit/push atau pembaruan keamanan global dalam persiapan ini.
