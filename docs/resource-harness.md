# Harness lintas resource untuk pengembangan

Versi0.4.0 menambahkan tiga perintah. Perintah products yang sudah ada tetap memakai kontrak/image lama. Suite generik di bawah ini adalah test internal dan kesiapan. Versi0.5.0 menambahkan paket evaluator acuan pengembangan yang terpisah untuk books/inventory; lihat evaluation/resource-reference/README.md. Evaluator products tetap33 kasus.

Jalankan dari C:\Perkuliahan\TA menggunakan terminal biasa atau Codex CLI yang dapat meminta persetujuan eskalasi. Sesi desktop saat ini masih membatasi Docker. PHP diperlukan untuk lint scaffold; Docker Desktop Linux/WSL2 dan image internal critic-laravel:dev harus tersedia. Tidak perlu mengunduh ulang dependensi Laravel untuk tiap resource.

## Books: build, readiness, bukti penolakan, lalu loop

```bat
python -m critic_agent resource-build examples/books.json
python -m critic_agent resource-check examples/books.json
python -m critic_agent resource-check examples/books.json --code examples/NoOpBookController.php
python -m critic_agent run-resource examples/books.json --seed 42 --temperature 0.2 --timeout 300
```

Gerbang readiness books adalah READY27/27:12 internal dan15 readiness tambahan. Fixture NoOpBookController sengaja memiliki method kosong; target validasinya FAILED_INTERNAL dengan12 kasus yang direncanakan (exit1 untuk kegagalan kandidat). Ini contoh manual untuk validasi harness, bukan keluaran Qwen atau hasil penelitian. Bila readiness gagal, selesaikan error lingkungan/harness sebelum menjalankan loop. Hasil kandidat gagal pada tahap ini memang diharapkan; jalankan perintah berikutnya secara terpisah bila shell menghentikan urutan pada exit1.

`run-resource` memakai analisis statis dan12 test internal books pada setiap kandidat. LOLOS mensyaratkan keduanya berhasil. Maksimal tiga revisi; kode identik, batas revisi dan ERROR tetap tercatat. Model hanya menerima spesifikasi, kode sebelumnya, dan temuan internal yang dipilih. Raw output, semua temuan dan manifest berada di runs/..._loop_.... Suhu0.2/seed42 tetap parameter pengembangan, belum parameter penelitian final.

## Resource kedua

```bat
python -m critic_agent resource-build examples/inventory_items.json
python -m critic_agent resource-check examples/inventory_items.json
python -m critic_agent run-resource examples/inventory_items.json --seed 42 --temperature 0.2 --timeout 300
```

Inventory memakai tabel inventory_items dengan model StockItem (nama tabel ditetapkan eksplisit). Gerbang readiness46/46:16 internal dan30 tambahan. Readiness live sudah terverifikasi; lihat status verifikasi di bawah. Kode Qwen yang sudah diarsipkan dapat diperiksa lewat `resource-check SPEC --code FILE`, atau dipakai ulang melalui `run-resource SPEC --initial-run FOLDER` bila spesifikasi/hash/model/options cocok.

## Cakupan dan batas

Internal berisi lima kasus CRUD, field wajib pada store/update untuk setiap field dan404 untuk show/update/destroy:8+2N kasus. Semua request memakai JSON dan snapshot data tersimpan. Kesiapan menambahkan invalid type, min/max, unique, batas valid, dan update mempertahankan nilainya sendiri pada controller tepercaya. Readiness tidak dijalankan pada kandidat dan tidak disalurkan sebagai feedback. Dengan kebijakan internal ini, pelanggaran unique/nilai batas dapat tetap lolos internal; paket evaluator terpisah35/57 kasus tersedia di0.5.0, dan sudah terverifikasi live untuk development. Peninjauan/pemisahan/pembekuan tetap diperlukan sebelum evaluasi akhir.

Generator mendukung kontrak v1 JSON string/integer,1–20 field, operasi/status tetap. Batas string yang dinyatakan tidak boleh melebihi256; required dengan max0 ditolak. Unique integer dengan kedua batas memerlukan setidaknya lima nilai untuk fixture; batas satu sisi tetap didukung. Nama class PHP yang dicadangkan, Controller, tabel migrations dan sqlite_* ditolak. Input di luar cakupan ini menghasilkan error, tidak dipotong atau diabaikan.

Build membuat konteks unik di builds/resources/.../context beserta build_result.json dan hash semua berkas. Tidak ada arsip generasi/loop yang ditimpa. Model, migration, route, controller acuan dan fixture dibentuk dari spec; semua PHP hasil pembentukan di-lint sebelum build. Migration products bawaan dibuang di image turunan agar tabel resource tidak bentrok. Sumber image products/evaluator dan runtime aslinya tidak diubah.

Sejak0.4.1, `resource-build --timeout 600` memberi batas600 detik per operasi Docker (inspect, tag, build, cleanup), bukan batas10 detik tersembunyi pada tahap persiapan. Ini bukan batas total durasi seluruh rangkaian. Bila gagal, keluaran menampilkan failed_stage/reason/timeout_seconds; arsip memisahkan penyebab awal dan hasil cleanup. Timeout client belum membuktikan operasi daemon tidak sempat membuat tag, sehingga cleanup terhadap nama UUID milik build tetap dicoba. Kegagalan cleanup dicatat; tidak ada prune atau penghapusan image lain. Jalankan resource-check hanya setelah build menghasilkan BUILT.

Base image diperiksa entrypoint/label-nya: hanya harness internal yang diterima; image evaluator/resource dan aliasnya ditolak. Build membuat tag sementara miliknya sendiri dari ID base yang telah diperiksa, menggunakan tag itu untuk build, lalu membersihkannya. ID dan perintahnya dicatat. Tag target default critic-resource-RESOURCE:dev harus berbeda dari base/evaluator. `--image` mengganti target; `--base-image` harus tetap menunjuk harness internal yang cocok. Contoh ini memakai Docker daemon tepercaya; tidak ada klaim tahan manipulasi daemon.

Fingerprint mencakup spesifikasi dan sumber generator/template/runtime/config. Runner menolak image dengan fingerprint berbeda; setelah mengubah spec/template, bangun ulang image. Candidate hanya dipasang sebagai satu file read-only; container nonroot, network none, read-only root, tmpfs, batas memori/CPU/PID dan output tetap berlaku. Seluruh revisi memakai image ID yang sama. Jangan memasang folder proyek atau menjalankan kandidat di host.

## Status verifikasi

Tes Python, lint PHP, dan enumerasi data provider menguji generator, fixture, hitungan, mode, penolakan image salah, dan loop generik. Eksekusi container dilakukan melalui terminal atau CLI pengguna. Readiness products 21/21 dan evaluator products31/33 menjadi33/33 sudah diverifikasi dari arsip pengguna; setiap resource tambahan tetap memerlukan verifikasi tersendiri.

Pembaruan4 November: books telah diverifikasi langsung dari arsip pengguna: readiness27/27, NoOpBookController ditolak0/12, dan Qwen langsung LOLOS12/12 pada attempt0 tanpa revisi (runs/20261104T044458Z_loop_52c1faef1c1644f3ac228b14eebdebcf). Inventory juga terverifikasi: readiness46/46, kandidat11/16 menjadi12/16 setelah revisi pertama, lalu revisi kedua identik dan berhenti BELUM LOLOS/identical_code (runs/20261104T044936Z_loop_4c8045891ecc4a74a31e0117ed15932a). Qwen memperbaiki destroy, tetapi empat aturan required pada update masih hilang. Angka null pada percobaan reused berarti test tidak dijalankan ulang; hasil aktual terakhir12/16. Ini hasil pengembangan yang tetap dilaporkan; evaluator pengembangan books/inventory0.5.0 sudah terverifikasi Docker:books35/35→35/35;inventory51/57→53/57, repair0/1 pada inventory.

Status 5 November:ketiga resource internal/acuan development dan laporan komponen provisional sudah berjalan. Lanjutkan pilot suhu/seed/biaya, audit cakupan dan review manusia sebelum pemisahan/pembekuan akhir. Panduan penerus: [HANDOFF.md](HANDOFF.md).

Referensi build: [Docker image tag](https://docs.docker.com/reference/cli/docker/image/tag/) dan [Dockerfile](https://docs.docker.com/reference/dockerfile/).
