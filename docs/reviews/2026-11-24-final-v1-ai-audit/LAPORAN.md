# Laporan pemeriksaan lima soal CRUD dan evaluator

**Kesimpulan: spesifikasi dan 358 kasus yang terdaftar konsisten pada fixture yang dipakai, tetapi paket belum layak disetujui menyeluruh atau dibekukan. Ada tiga celah evaluator yang terbukti dengan eksperimen Docker baru.**

Pemeriksa teknis: OpenAI Codex, 24 November 2026. Ini laporan pemeriksaan berbantuan AI untuk Anda baca sebelum mengisi formulir; bukan pengesahan reviewer manusia. Tidak ada formulir keputusan manusia yang diisi atau diperbaiki otomatis.

## Hasil per soal

| Soal | Kasus acuan ditelusuri | Pemetaan internal | Bukti kontrol lama cocok harapan | Status paket |
|---|---:|---:|---:|---|
| [categories](categories.md) | 42 | 12 | 88/88 | Perlu tindak lanjut F1–F3 |
| [rooms](rooms.md) | 50 | 12 | 98/98 | Perlu tindak lanjut F1–F3 |
| [assets](assets.md) | 73 | 14 | 134/134 | Perlu tindak lanjut F1–F3 |
| [courses](courses.md) | 77 | 14 | 136/136 | Perlu tindak lanjut F1–F3 |
| [shipments](shipments.md) | 116 | 18 | 192/192 | Perlu tindak lanjut F1–F3 |
| **Total** | **358** | **70** | **648/648** | **Jangan setujui massal sebelum celah ditutup** |

Angka 648/648 berarti kontrol benar diterima dan mutasi yang sudah ada menghasilkan penolakan yang diharapkan. Angka itu tetap sah untuk daftar kontrol lama. Eksperimen baru di bawah menunjukkan daftar lama belum cukup untuk mendeteksi semua pelanggaran kontrak.

## Bagian yang sudah memadai pada kasus yang ada

- POST valid memeriksa HTTP 201, ID integer baru, nilai field respons, baris database yang sama, jumlah record bertambah tepat satu dan record lama tidak berubah.
- GET koleksi memeriksa array JSON asli, ID integer unik dan nilai setiap field yang terikat ke ID. Urutan record bebas. Field tambahan diperbolehkan sesuai kontrak.
- GET satu record, PUT dan DELETE memeriksa target serta record pembanding untuk ID yang dipakai fixture. PUT/POST invalid dan 404 memeriksa bahwa tabel resource tidak berubah.
- Semua 246 vektor invalid POST/PUT memang melanggar field yang ditunjuk; nilai batas min/max, unique milik record lain dan own-unique dipetakan. Numeric string yang sah untuk aturan integer tetap diterima dan dinormalisasi pada respons.
- Lima kontrak/spec, profile, matriks, katalog kontrol,650 hash sumber dan 1.368 berkas bahan cocok. Seluruh 358 baris expected/fixture/status/cakupan ditelusuri;70 internal_covered dan 288 reference_only tetap dibedakan.

Cakupan ini dinilai dari source assertion dan bukti terstruktur, bukan dari melihat nama test saja. Semua kasus memiliki empat bukti positif acuan lama yang cocok. Rincian tiap baris berada pada lima laporan soal dan case-audit.json.

## F1 — Controller salah memilih record masih bisa lolos

**Contoh sederhana:** database berisi Furniture(ID 1) dan Hardware(ID 2). Anda meminta ID 2, tetapi controller selalu mengambil record pertama. Seharusnya test menolak perilaku ini.

Suite sekarang memasukkan target terlebih dahulu, lalu record pembanding, dan meminta operasi sukses hanya untuk target pertama. Skenario berurutan juga hanya memiliki satu record. Akibatnya, controller cacat yang tetap memeriksa keberadaan ID, lalu mengambil record pertama, tampak benar bagi semua kasus sekarang.

Probe baru [wrong_first.php](probes/wrong_first.php) hanya mengubah helper pencarian pada salinan kontrol benar. Ia **lulus seluruh suite internal dan acuan kelima soal**. Test pembanding kategori yang meminta ID kedua membuktikan GET/PUT/DELETE salah; perubahan data pendek pada ID kedua juga salah.

Sumber utama: evaluation/final-v1/internal/Suite.php:66,73,78,88 dan reference/Suite.php:94,101,106,116; sequence:58–70. Kontrak PRD9.1 mewajibkan ID target yang benar, bukan selalu record pertama.

**Tindak lanjut:** tambahkan keberhasilan show/update/destroy untuk ID non-pertama, periksa ID/body serta seluruh keadaan target dan record lain. Perbaikan harus masuk pada suite internal dan acuan yang tetap terpisah.

## F2 — Pembatasan string yang tidak diminta belum terdeteksi

Contoh categories: `name="A"` dan `description="B"` sah karena kedua field required/string dengan batas maksimum, tanpa minimum3. Controller yang menambahkan min:3 melanggar soal karena menolak input sah tersebut.

Probe [overstrict_min3.php](probes/overstrict_min3.php) menambahkan batas min:3. Ia tetap **lulus seluruh suite internal dan acuan kelima soal** karena contoh positif string tanpa min selalu cukup panjang. Pada dua test tambahan POST/PUT pendek untuk categories, controller benar menerima input, sedangkan probe mendapat422.

Tujuh field terdampak: `categories.name`, `categories.description`, `rooms.label`, `assets.name`, `courses.course_code`, `shipments.reference_code`, `shipments.note`.

**Tindak lanjut:** tambahkan contoh valid panjang minimum nonkosong dan panjang pendek pada POST/PUT. Case yang sudah ada tidak perlu dinyatakan salah expected-nya; yang kurang adalah contoh positif kontrak lainnya.

## F3 — Respons JSON rusak salah masuk kategori ERROR

Probe [invalid_json.php](probes/invalid_json.php) mengembalikan HTTP 200 dengan body `not-json`. Ini pelanggaran keluaran controller yang sudah diketahui, sehingga seharusnya menjadi kegagalan test/feedback.

Helper Assertions::object memanggil json_decode dengan JSON_THROW_ON_ERROR. Suite hanya menangkap assertion failure, sehingga JsonException keluar sebagai JUnit error. FinalRunner kemudian mengubahnya menjadi ERROR/incomplete_or_wrong_cases.

**Bukti baru:** seluruh lima image internal mencatat1 JUnit error dan image acuan3 error untuk index/empty/sequence. Readiness dan cleanup Docker berhasil. Dengan demikian, ini tidak disebabkan Docker mati atau framework tidak siap. Dampaknya, kode bermasalah dapat dikeluarkan dari penilaian/feedback sebagai tidak dapat dinilai.

Sumber: internal/Assertions.php:11 dan reference/Assertions.php:11; catch pada internal/Suite.php:58 dan reference/Suite.php:81; final_sandbox.py:252–253.

**Tindak lanjut:** ubah JSON kandidat yang rusak menjadi assertion failure dengan pesan jelas; pertahankan ERROR untuk gangguan lingkungan sesungguhnya. Tambahkan kontrol untuk memastikan status FAILED_INTERNAL/FAILED_REFERENCE, bukan ERROR.

## Bukti eksekusi baru

| Soal | Probe salah-ID pada internal/acuan | Probe min:3 pada internal/acuan | Probe JSON rusak: error internal/acuan |
|---|---|---|---|
| categories | Lolos 12/12 dan 42/42 | Lolos 12/12 dan 42/42 | 1/3 → ERROR |
| rooms | Lolos 12/12 dan 50/50 | Lolos 12/12 dan 50/50 | 1/3 → ERROR |
| assets | Lolos 14/14 dan 73/73 | Lolos 14/14 dan 73/73 | 1/3 → ERROR |
| courses | Lolos 14/14 dan 77/77 | Lolos 14/14 dan 77/77 | 1/3 → ERROR |
| shipments | Lolos 18/18 dan 116/116 | Lolos 18/18 dan 116/116 | 1/3 → ERROR |

Lolos pada dua kolom pertama adalah bukti celah evaluator, bukan bukti controller itu benar. Semua 30 run kandidat baru dan 10 readiness memakai image asli yang dipin. Tidak ada Qwen.

| Test pembanding baru pada categories | Lulus | Gagal |
|---|---:|---:|
| Kontrol benar, readiness |5|0|
| Kontrol benar, kandidat |5|0|
| Probe salah-ID |1|4|
| Probe min:3 |3|2|

Lima test pembanding mencakup show/update/destroy pada ID kedua serta POST/PUT dengan string pendek. Kontrol benar lulus seluruhnya, sehingga kegagalan probe bukan akibat test tambahan yang selalu menolak. Source [AuditContractTest.php](probes/AuditContractTest.php), [bukti native](evidence/native-probes.json) dan [bukti tambahan](evidence/additional-probes.json) disertakan. Test tambahan berada pada image audit baru; bukan bagian dari suite final-v1 yang diterbitkan.

## Apa yang perlu Anda lakukan dengan formulir

Baca ringkasan ini dan laporan soal yang bersangkutan. Jangan menyalin angka648/648 menjadi approved untuk seluruh paket. F1–F3 perlu ditindaklanjuti sebelum persetujuan/freeze; jika belum memahami atau belum memeriksa suatu bagian, pertahankan pending/uncertain. Form menampung keputusan Anda dan reviewer yang benar-benar melakukan pemeriksaan, bukan nama pengganti pemeriksa AI.

Form kerja categories.json saat audit belum valid JSON karena nama dan tanggal ditulis tanpa tanda petik. Isinya saya pertahankan, termasuk nama yang Anda masukkan. Format perlu dibenahi ketika Anda mengisi hasil sebenarnya; waktu reviewed_at harus waktu pemeriksaan aktual dengan zona waktu. Laporan ini tidak mengisi atau mengesahkan tanggal/nama manusia.

## Metode, batas dan integritas

Audit membaca seluruh lima profil, suite/assertion,358 vektor acuan dan 70 pemetaan internal. Checker aturan terpisah memeriksa input/expected yang dicantumkan, termasuk required, tipe, batas dan unique. Checker terbatas pada vektor ASCII/numerik yang terdaftar, bukan pengganti validator Laravel untuk semua input. Seluruh 650sumber dan 1.368bahan dihash ulang;648observasi23 November dicocokkan kembali. Tidak ada klaim bahwa358 vektor mencakup semua kemungkinan input.

Pemeriksaan silang kode oleh agen AI terpisah menghasilkan tiga temuan yang sama; pembuktian Docker dilakukan pada salinan kontrol baru. Tiga fault diuji pada semua lima resource dalam image aslinya. Lima test pembanding independen hanya dijalankan untuk categories; penerapan diagnosis umum pada resource lain didukung source bersama, profil, dan run fault pada masing-masing image.

Satu upaya persiapan test tambahan berhenti sebelum build karena pemilihan string XML tidak cocok dengan konfigurasi satu baris. Observasi native sudah tersimpan; konteks persiapan baru dipakai untuk hasil tambahan yang lengkap. Upaya tersebut dipertahankan di work/ dan bukan skor kandidat. Seluruh container cleanup dan penghapusan tag pin sementara sukses; tag image audit baru dipertahankan untuk reproduksi.

Hash paket tetap `f2b648aeb042f4edcbb46b1b0160c87f93c326d084009cbc6de2f0f121e4a9b7`; sumber aplikasi/adaptor tetap `020512666aaf479b8672dd4d8a00c82fa4cca30cded07bbf4236fa4ba3828a64`. Soal, suite, image final asli, kontrol/candidate historis, ZIP review lama dan formulir manusia tidak diubah. Tidak ada full unittest baru;253 tes adalah checkpoint23 November, sedangkan bukti baru adalah44 pemanggilan harness Docker (40 native +4 tambahan) dalam audit ini.

Sebelum perbaikan, tentukan versi paket berikutnya dan hash/image baru secara terkoordinasi. Pertahankan final-v1 dan hasilnya; jangan mengganti sumber/hashes lama diam-diam. Setelah memperbaiki tiga celah, ulangi validasi kontrol dan kasus tambahan, perbarui paket review, lalu lakukan peninjauan manusia dan pembekuan. Audit ini belum memperbaiki evaluator atau menjalankan20 pasangan final.

Lampiran16 kasus komponen hanya diperiksa integritas berkasnya sebagai bagian bahan; tidak dilabeli ulang atau disahkan. Temuan evaluator ini harus dipertimbangkan saat menilai kecukupan evidence komponen, tetapi tidak otomatis mengubah label/metrics historis.
