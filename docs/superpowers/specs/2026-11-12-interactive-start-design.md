# Input CRUD interaktif

Rancangan disetujui pengguna pada 12 November 2026. Command `python -m critic_agent start` menanyakan resource, model, controller dan field string/integer beserta min/max/unique. Kelima operasi dan field required mengikuti kontrak v1. Ringkasan dikonfirmasi sebelum JSON disimpan dan persiapan Docker dimulai. Input dibatasi validator spec/resource yang sudah tersedia. Input salah ditanyakan ulang. Pembatalan dan EOF menghentikan alur dengan jelas.

Command menyiapkan base harness bila belum tersedia, membangun image resource dengan tag sesi UUID, memeriksa readiness, lalu memanggil run_resource yang sudah ada. Semua tahap disimpan dalam folder sesi baru di runs/ dengan spesifikasi dan manifest sesi. Build/readiness ERROR menghentikan alur sebelum model dipanggil. Image resource dipertahankan untuk audit dan reproduksi. Evaluator acuan tetap merupakan tahap terpisah.

Pilihan implementasi Codex adalah selalu memakai harness generik untuk spesifikasi interaktif, termasuk resource bernama products. Ini memungkinkan field pengguna dan menghindari ambiguitas dengan kontrak products legacy yang tetap. Penggunaan file JSON melalui command lama tetap tersedia. Alternatif formulir saja tidak memenuhi permintaan langsung menjalankan self-debugging. Parsing bahasa alami menambah interpretasi model yang belum termasuk kontrak.

Tidak ada perubahan suite/runtime/generator resource, versi aplikasi 0.5.0 atau protokol komponen 1.0. PRD diperbarui melalui addendum input interaktif bertanggal dengan nama file v1.3 tetap. Pengujian terkontrol memakai transport Docker/model pengganti dan loop asli. Verifikasi live memerlukan engine dan model yang siap.
