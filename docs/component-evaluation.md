# Evaluasi komponen Critic

Tahap ini mengukur kemampuan Critic mendeteksi controller bermasalah. Tidak ada generasi/revisi Qwen. Kandidat diperiksa melalui analisis statis dan test internal yang sudah tersedia; evaluator acuan hanya menyediakan bukti terpisah untuk peninjau label.

Implementasi memakai protokol komponen `1.0`. Versi aplikasi tetap `0.5.0` karena versi itu merupakan bagian fingerprint suite resource yang sudah diuji live. Identitas implementasi komponen dicatat sebagai `engine_sha256` pada setiap run. Perubahan versi aplikasi selanjutnya harus disertai pembekuan/build ulang suite secara terkoordinasi.

## Korpus pengembangan yang sudah disiapkan

Manifest: `corpora/development/20261104T081151Z_corpus_a55bbcbabcbd428897b21647afba354f/corpus.json`.

| Asal | Jumlah mentah | Kode/spec unik per asal | Status label |
|---|---:|---:|---|
| synthetic | 10 | 10 | Semua draf |
| qwen_formative | 6 | 5 | Semua draf |
| qwen_held_out | 0 | 0 | Belum tersedia |

Sepuluh contoh sintetis berisi dua gaya implementasi yang diusulkan benar, enam kesalahan dalam cakupan internal, dan dua penghilangan validasi batas yang hanya tercakup acuan (`reference_only`). Contoh sintetis sengaja dibangun berdasarkan kontrak/test, sehingga hasilnya dapat terlalu optimistis. Korpus Qwen mempertahankan **semua** percobaan dari tiga loop pengembangan yang dipilih secara eksplisit: products 0–1, books 0, inventory 0–2. Inventory 1 dan 2 identik; keduanya tetap diarsipkan, tetapi hanya satu dihitung dalam metrik. Ini bukan sampel acak atau held-out, dan pengulangan dalam loop tidak independen.

Kode, spesifikasi, prompt, respons mentah serta manifest/history sumber disalin dengan hash. Kode kandidat tidak diperbaiki manual. Label awal berasal dari inspeksi kode dan merupakan usulan, bukan ground truth yang sudah disahkan manusia. Tidak ada nama/peninjauan manusia yang diisikan otomatis.

Untuk menyiapkan paket baru, jalankan `python -m critic_agent component-corpus-init`. Opsi `--synthetic-only` tersedia bila arsip Qwen sumber belum ada. Perintah selalu membuat folder unik; paket lama tidak ditimpa.

## 1. Kumpulkan bukti acuan sebelum prediksi

Gunakan terminal normal yang sudah berhasil mengakses Docker. Perintah berikut dapat dijalankan dari CMD atau PowerShell pada folder proyek:

```bat
cd /d C:\Perkuliahan\TA
python -m critic_agent component-evidence corpora/development/20261104T081151Z_corpus_a55bbcbabcbd428897b21647afba354f/corpus.json --timeout 120
```

Pada PowerShell, gunakan `Set-Location C:\Perkuliahan\TA` untuk pindah folder. Baris perintah Python sama.

Image internal dan evaluator products/books/inventory yang sudah dibangun digunakan kembali. Tidak perlu mengunduh Qwen atau membangun ulang image untuk perubahan komponen ini. Runner tetap memeriksa readiness, label suite/kontrak, jumlah test, hash kandidat, image ID dan cleanup. PHP kandidat hanya dieksekusi dalam Docker.

Output memuat `corpus_manifest` baru serta `review_packet`. `COMPLETE` berarti pengumpulan bukti selesai, termasuk bila test kandidat gagal atau sintaksnya terbukti salah dalam Docker. Ini bukan status kelulusan kandidat. `ERROR` berarti ada bukti yang belum sah; periksa `cases/CASE_ID/independent-evidence.json` dan raw `harness/.../result.json`. Kegagalan akses named pipe adalah masalah izin sesi pemanggil. Jangan mengubah keamanan global atau menjalankan kandidat pada host.

Paket bukti tidak mempromosikan label. Prediksi Critic, usulan label, prompt revisi dan feedback tidak dimasukkan ke subfolder `review/`. Di dalamnya tersedia pasangan `R001.php`, `R001.spec.json`, `R001.reference.json`, dan template keputusan kosong `decisions.json`. Berikan **hanya subfolder review** kepada peninjau. `review-map.json` di luar subfolder dipakai pengelola untuk memetakan keputusan kembali ke kasus.

## 2. Tinjau dan tetapkan label manusia

Penulis label dan seorang peninjau berbeda memeriksa kode terhadap spesifikasi dan bukti acuan. Isi keputusan tanpa melihat prediksi Critic. Catat nama sebenarnya, alasan, kategori/coverage pelanggaran, waktu ISO8601 dengan zona waktu, dan apakah peninjau dibutakan terhadap prediksi. Jika belum sepakat, gunakan `uncertain` atau status `disputed`.

Saat ini pemindahan keputusan ke manifest dilakukan manual, tidak ada perintah impor review otomatis. Salin seluruh folder bukti yang berhasil ke folder korpus baru, lalu gunakan `review-map.json` untuk memperbarui `cases[].label` di salinan `corpus.json`:

- `value`: `correct`, `problematic`, atau `uncertain`.
- `violations`: kosong untuk `correct`; setiap pelanggaran `problematic` harus memiliki `coverage` (`internal_covered` atau `reference_only`) dan `detail` yang menjelaskan pelanggaran kontrak.
- `evidence`: pertahankan referensi bukti acuan beserta hash; tambahkan/perbarui catatan `code_inspection` dengan alasan keputusan manusia.
- `review`: isi `status: reviewed`, dua nama berbeda pada `author`/`reviewer`, `reviewed_at`, dan `blinded_to_prediction: true` hanya jika benar-benar dilakukan.

File kandidat, spec, raw bukti dan hash aset tetap dipertahankan. Jangan mengedit paket sumber atau run lama. Satu label `reviewed` memerlukan bukti independen lengkap yang cocok dengan hash kode/spec dan suite yang didukung. Bukti parsial, status lulus tanpa testcase, hash berbeda dan cleanup gagal ditolak. Hasil acuan tidak otomatis menentukan label; ketidaksesuaian harus diselesaikan dan diberi alasan oleh peninjau. Peninjau belum ditetapkan oleh perangkat lunak.

Review harus selesai **sebelum** menjalankan prediksi untuk laporan reviewed. Run menyimpan snapshot label dan waktunya; mengubah label sesudah run tidak memperbarui laporannya. Gunakan manifest salinan yang sudah direview untuk run baru.

## 3. Jalankan prediksi dan laporan

Ganti path contoh di bawah dengan manifest hasil peninjauan dan `run_directory` yang dikembalikan CLI:

```bat
python -m critic_agent component-run corpora/reviewed/NAMA_PAKET/corpus.json --timeout 120
python -m critic_agent component-report component-runs/NAMA_RUN
```

Untuk memeriksa alur menggunakan label draf, jalankan `component-run` pada manifest draf lalu gunakan `component-report RUN --provisional`. Laporan diberi `label_mode: provisional_unreviewed`; hasilnya tidak menggantikan evaluasi berlabel manusia. Jika peninjau belum melihat prediksi, jangan membagikan laporan/provenance di luar paket review kepadanya.

`component-run` hanya memberikan kode dan spec kepada pemeriksa. Temuan statis cukup menghasilkan prediksi positif dan melewati eksekusi dinamis. Prediksi negatif memerlukan statis bersih dan semua test internal lulus. Error lingkungan, hasil parsial/skipped, image berubah, atau cleanup gagal menjadi `unknown`, dikeluarkan dengan hitungan alasan. Hasil identik dapat digunakan ulang dengan `reused_from`; ini tidak dilaporkan sebagai eksekusi tambahan. Run `ERROR` dapat memiliki sebagian prediksi yang sah; laporan menunjukkan cakupan parsial tersebut, sehingga jangan menganggapnya evaluasi lengkap.

## Arti metrik dan batasnya

Positif berarti controller bermasalah. Satu kode dengan banyak temuan tetap satu prediksi:

| Ground truth | Prediksi bermasalah | Prediksi benar |
|---|---|---|
| Bermasalah | TP | FN |
| Benar | FP | TN |

Precision = TP/(TP+FP), recall = TP/(TP+FN), FPR = FP/(FP+TN). JSON menyimpan pembilang, penyebut dan persen; penyebut nol menghasilkan `null`/N/A. Default hanya memakai label reviewed yang memenuhi syarat. Label tidak pasti/disputed, review terlambat dan prediksi unknown dikeluarkan secara eksplisit. Di dalam setiap asal, satu pasangan hash kode/spec yang memenuhi syarat dihitung sekali; label yang bertentangan pada duplikat dikeluarkan.

Laporan memisahkan synthetic, qwen_formative dan qwen_held_out; tidak ada matriks gabungan. Pelanggaran `reference_only` yang lolos pemeriksaan internal tetap FN, tidak dibuang untuk menaikkan recall. Subset coverage disajikan sebagai diagnostik. Korpus kecil/terpilih dan ketergantungan antarpercobaan membatasi kesimpulan menjadi deskriptif. Sampel Qwen held-out dan pengujian akhir masih pekerjaan berikutnya.

Snapshot memuat kode/spec, label, bukti/provenance, manifest sumber dengan byte asli, identitas engine, image dan hasil prediksi. Pelaporan memverifikasi hash snapshot dan prediksi. Ini menjaga reproduktibilitas arsip lokal; bukan bukti kriptografis terhadap pihak yang sengaja menulis ulang seluruh manifest. Folder `component-runs/` dan `component-evidence/` diabaikan Git; korpus pengembangan terkurasi dapat disimpan bersama sumber.

## Verifikasi implementasi

`python -m unittest discover -s tests -v`: 134 tes lulus, tanpa skip pada mesin pengembangan saat pencatatan. Termasuk 18 tes komponen: matrix per kode, reference-only FN, pemisahan asal, duplikat, draf, review terlambat, hash/path/provenance, raw manifest, evidence independen, cleanup dan hasil parsial. Fixture unit bukan data penelitian.

Lint 16 kandidat paket menghasilkan 15 valid dan satu kegagalan sintaks yang sengaja ditanam. Tidak ada kandidat dieksekusi di host. Fingerprint internal books/inventory dan acuan ketiga resource masih cocok dengan hasil live sebelumnya.

Smoke CLI desktop tersimpan di `work/component-smoke/`. Docker menolak named-pipe: bukti acuan 16 kasus belum sah, prediksi dinamis unknown, dan dua cacat statis terdeteksi. Laporan reviewed memiliki nol kasus layak/N/A. Hasil parsial provisional hanya memeriksa format, bukan bukti precision/recall penelitian. Jalankan pengumpulan bukti dari terminal pengguna untuk melewati gerbang Docker berikutnya.


## Bukti live terbaru

Pengguna sudah menyelesaikan pengumpulan bukti pada `component-evidence/20261104T082952Z_reference-evidence_26a23f11d3ab49929f39605cde0bf690`. Arsip diverifikasi: COMPLETE16 kasus,4PASSED_REFERENCE,11FAILED_REFERENCE,1UNLOADABLE_CODE yang disengaja,0ERROR lingkungan. Satu kasus inventory memakai ulang hasil kode identik. Hash, suite, image dan cleanup sah; seluruh label tetap draf. Saat pengumpulan bukti keputusan review masih kosong; pembaruan isian berikutnya dijelaskan di bawah. Smoke desktop di atas tetap catatan historis, sedangkan gerbang Docker bukti komponen sekarang selesai dari terminal pengguna.

Bukti ini mendahului anotasi/prediksi. Status terkini sudah menghasilkan laporan provisional, sedangkan review manusia tetap diperlukan sebelum laporan reviewed; lihat pembaruan 5 November di bawah.


## Status terkini — 5 November 2026

Anotasi16 kasus sudah diisi dalam corpora/annotations/20261104T085829Z_mikhael-ai-assisted_e7a9c4248c344f21aa2b3df91fca627c/corpus.json:4 correct/12 problematic, atas nama Mikhael Josua Roganda sesuai permintaan pengguna, disiapkan OpenAI Codex dengan human_author_review_attested=false. reviewer/reviewed_at kosong; status draft. Sumber resmi mendukung aturan teknis; tidak ada klaim manusia penerbit sumber memberi label file proyek.

Atas permintaan berikutnya, component-evidence/.../review/decisions.json juga diisi usulan AI dengan path bukti disesuaikan. Blank sebelumnya ada di review-backups/. Folder review lokal sekarang mengandung usulan label. Untuk review independen siapkan paket bersih berisi kode/spec/bukti dan formulir kosong; pisahkan usulan label/prediksi. Mengisi decisions saja tidak mengubah corpus.json; run berikut memakai korpus anotasi di atas.

Run component-runs/20261105T005526Z_component_4a131234b1c14b5a95421e211dcdf739 COMPLETE16/0 errors. Laporan provisional tersimpan/terverifikasi:synthetic TP6/FP0/TN2/FN2 (precision6/6,recall6/8,FPR0/2);Qwen formative TP3/FP0/TN2/FN0 (precision3/3,recall3/3,FPR0/2),5 unik setelah1 duplikat. Held-out0/N-A. Dua reference-only FN tetap dihitung. [Laporan yang ikut Git](evidence/component-provisional-2026-11-05.json) dan [panduan penerus](HANDOFF.md) tersedia; raw run/bukti diabaikan Git dan dibagikan terpisah untuk audit lengkap.

Run sebelumnya5November ERROR14 unknown karena endpoint Docker belum tersedia; setelah Engine running rerun berhasil. Semua kegagalan dipertahankan. Berikutnya pilot/biaya dan review/freeze penelitian. Anotasi AI tetap provisional; laporan reviewed membutuhkan review manusia selesai sebelum prediction snapshot baru.
