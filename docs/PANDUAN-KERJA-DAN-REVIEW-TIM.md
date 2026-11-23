# Panduan kerja dan review tim

Dicatat pada 12 November 2026 berdasarkan pembahasan dengan pengguna. Tim menyatakan dua orang akan menjadi pembangun sistem dan memerlukan panduan pelaksanaan. Dokumen ini menjadi panduan awal yang dapat disesuaikan bersama pembimbing.

## Anggota dan status penugasan

Pengguna menyebut Mikhael Josua Roganda dan Johannes Sitorus untuk peran pembuat label dan peninjau independen. Penugasan yang dicatat adalah Mikhael sebagai pembuat label dan Johannes sebagai peninjau. Penyebutan nama dan penugasan belum membuktikan pemeriksaan telah dilakukan. Keputusan, waktu pemeriksaan dan pengesahan diisi setelah kegiatan nyata.

Anggota tim boleh membangun sistem sekaligus melakukan peninjauan silang. PRD meminta pembuat dan peninjau artefak merupakan orang berbeda. Keduanya perlu memahami spesifikasi CRUD, kode Laravel serta bukti pengujian yang diperiksa. Sertifikasi profesional bukan persyaratan yang ditetapkan PRD. Kasus yang belum dipahami dapat dibahas dengan pembimbing.

## Usulan pembagian pembangunan sistem

| Area | Tanggung jawab |
|---|---|
| CLI, spesifikasi dan loop revisi | Input pengguna, validasi JSON, prompt, pemanggilan Ollama, alur generate–periksa–revisi dan arsip percobaan |
| Harness, pengujian dan evaluasi | Lingkungan Docker/Laravel, assertion test, readiness, evaluator terpisah dan perhitungan metrik |

Pembagian area di atas merupakan usulan. Pemilik masing-masing area belum dikonfirmasi. Setelah pembagian disepakati, anggota yang lain meninjau perubahan beserta hasil pengujiannya. Catat pembuat, peninjau, berkas/artefak, temuan, tanggal kegiatan sebenarnya dan keputusan review.

## Tujuan review label

Review label menentukan apakah sebuah controller sesuai spesifikasi CRUD yang diberikan. Label ini dipakai untuk menilai ketepatan deteksi Critic. Peninjau memeriksa kasus secara mandiri sebelum membandingkan keputusan dengan pembuat label.

| Label | Penggunaan |
|---|---|
| correct | Pemeriksaan kode, spesifikasi dan bukti mendukung kesesuaian dalam cakupan yang dinilai |
| problematic | Ada pelanggaran spesifikasi yang dapat dijelaskan dan ditunjukkan buktinya |
| uncertain | Bukti atau pemahaman belum cukup untuk mengambil keputusan |

## Langkah pemeriksaan satu kasus

1. Baca spesifikasi. Catat field, tipe, required, batas min/max, unique, status HTTP dan perilaku setiap operasi.
2. Baca controller. Periksa index, store, show, update dan destroy terhadap kontrak tersebut. Contohnya, field pages yang wajib dan minimal 1 perlu memiliki validasi yang sesuai pada POST dan PUT.
3. Baca hasil pengujian acuan. Cocokkan kegagalan test dengan kode dan spesifikasi. Hasil test lulus perlu disertai pemeriksaan terhadap kontrak serta cakupan assertion.
4. Tentukan label dan tulis alasan. Untuk problematic, catat method/lokasi, aturan yang dilanggar dan bukti. Contoh alasan adalah “update tidak mewajibkan field pages, padahal kontrak PUT mewajibkan semua field required.”
5. Catat cakupan pelanggaran menurut matriks versi suite yang dinilai. Gunakan internal_covered atau reference_only berdasarkan cakupan aktual.
6. Isi formulir pemeriksaan masing-masing terlebih dahulu. Setelah keduanya selesai, bandingkan keputusan dan bahas perbedaan berdasarkan bukti.
7. Jika perbedaan belum terselesaikan, pertahankan uncertain/disputed dan konsultasikan dengan pembimbing. Catat waktu dan keputusan yang sebenarnya.

Mikhael mengisi author-decisions.json dan Johannes mengisi reviewer-decisions.json. Setelah pemeriksaan keduanya dan pembahasan perbedaan selesai, isi keputusan gabungan di decisions.json. Nama pada formulir kosong belum mengesahkan label.

## Belajar melalui satu kasus latihan

Tim dapat memulai dengan satu kasus yang dijelaskan bersama Codex untuk memahami hubungan spesifikasi, kode dan hasil test. Catat kasus tersebut sebagai latihan berbantuan AI beserta bantuan yang diterima. Setelah memahami prosesnya, lakukan pemeriksaan kasus berikutnya secara mandiri.

Latihan berbantuan AI dan paparan usulan label/prediksi sebelumnya perlu diungkapkan pada catatan review. Paket baru tidak menghapus paparan tersebut. blinded_to_prediction hanya dapat bernilai true bila sesuai keadaan sebenarnya. Jika syarat reviewed-only belum terpenuhi, pertahankan status draf atau ikuti keputusan protokol bersama pembimbing.

Codex dapat menyiapkan bahan, menjelaskan kode dan memvalidasi format serta integritas formulir. Pengesahan review manusia memerlukan keputusan nyata dari pemeriksa. Codex tidak mengisi attestasi atau tanggal review manusia tanpa bukti kegiatan tersebut.

## Paket yang telah disiapkan

Paket baru berisi 16 kasus, spesifikasi, bukti acuan serta formulir kosong. Statusnya pending_human_review. Keputusan belum dipromosikan menjadi reviewed.

- [Panduan paket review](../corpora/reviews/20261112T114239Z_independent-review_54fa493b6e954a519743c76f5447e5ed/packet/README.md)
- [Formulir pembuat label](../corpora/reviews/20261112T114239Z_independent-review_54fa493b6e954a519743c76f5447e5ed/packet/author-decisions.json)
- [Formulir peninjau](../corpora/reviews/20261112T114239Z_independent-review_54fa493b6e954a519743c76f5447e5ed/packet/reviewer-decisions.json)
- [ZIP paket review](../corpora/reviews/20261112T114239Z_independent-review_54fa493b6e954a519743c76f5447e5ed/review-packet.zip)

Setelah formulir selesai, validasi keterikatan kode/spec/bukti, simpan label pada salinan korpus baru dan jalankan prediksi baru sesudah review. Arsip serta laporan provisional lama tetap menjadi rekaman development dengan status aslinya.

Acuan utama adalah PRD v1.3 bagian 12.5–12.6 dan P-07, serta docs/component-evaluation.md. Rencana eksperimen, ambang metrik dan pembekuan masih memerlukan penyelesaian keputusan yang tercatat di handoff.
