# Laravel products harness

Harness pengembangan untuk kontrak `harness/products-contract.json`. Laravel 12.70.2 dan PHPUnit 11.5.57 dikunci dalam `laravel/composer.lock`. Kontrak ini belum mendukung resource/field lain; CLI menolaknya sebelum eksekusi.

Controller `laravel/app/Http/Controllers/ProductController.php` adalah implementasi acuan buatan peneliti. Bukan hasil Qwen. `ProductsContractTest` memiliki 14 kasus internal (CRUD, field wajib, missing ID). `ProductsEdgeTest` memiliki 7 kasus untuk memeriksa kesiapan implementasi acuan (unique, batas nilai, tipe input); file ini tidak dijalankan untuk kandidat dan bukan suite acuan independen penelitian akhir.

## Jalur Docker untuk kandidat

Jalankan dari root proyek setelah Docker Desktop menggunakan Linux containers sudah tersedia:

```powershell
python -m critic_agent harness-build
python -m critic_agent harness-check
python -m critic_agent check-products examples/products.json runs/ID/initial_controller.php
```

`harness-check` harus menghasilkan READY sebelum kandidat dijalankan; `check-products` mengulang kesiapan itu dan membuat container terpisah untuk kandidat. `PASSED_INTERNAL` hanya berarti 14 test internal lulus. Perintah ini belum menggabungkan analisis statis atau loop revisi dan tidak menghasilkan status akhir LOLOS.

Container: nonroot 10001, network none, root read-only, drop capabilities, no-new-privileges, 768 MB RAM, 1 CPU, 128 PID; workspace baru pada tmpfs 512 MB dan tmp 32 MB. Input kandidat dipasang read-only. Tidak ada host mount writable, socket Docker, home, atau seluruh proyek. Paket siap di image; tidak ada unduhan saat test. Composer scripts/plugins dinonaktifkan selama penyiapan dependensi.

Image tag build awal masih memakai base PHP/Composer bertag; ID image aktual dicatat per run. Bekukan digest image sebelum eksperimen akhir. Docker Desktop/WSL2 harus memiliki memori cukup untuk Ollama dan container.

JUnit dibatasi 4 MB dan dibuat di tmpfs container. Entrypoint mengirimnya melalui envelope base64; Python memvalidasi encoding, struktur, jumlah testcase, dan konsistensi counter, lalu menyimpan arsip. Gabungan stdout/stderr dibatasi 8 MB dengan pembacaan bertahap. Melebihi batas menghentikan client dan memicu cleanup container. Logging daemon Docker dinonaktifkan untuk run ini. Tidak ada jalur bagi kandidat menulis langsung ke folder laporan host.

Timeout, laporan invalid, atau cleanup gagal tidak pernah menghasilkan READY/PASSED_INTERNAL. Log dan JUnit disimpan di `runs/harness/critic-...`. Runner memakai image ID yang sama untuk kesiapan dan kandidat serta mencoba menghapus hanya container UUID yang dibuatnya. Bila daemon masih memulai container saat cleanup gagal, periksa nama dalam hasil dan bersihkan melalui Docker.

## Pengujian lokal kode acuan yang tepercaya

Untuk pengembangan harness saja, dengan PHP 8.3 dan SQLite:

```powershell
composer install --working-dir=harness/laravel --no-interaction --prefer-dist --no-scripts --no-plugins
Set-Location harness/laravel
php vendor/bin/phpunit --do-not-cache-result
```

Jangan mengganti controller lokal dengan kode Qwen untuk menjalankan perintah ini. Kandidat hanya diuji melalui DockerRunner. Lingkungan eksekusi Codex mengembalikan `is_readable=false` walau PHP dapat membaca bytes file; PHPUnit lokal terhenti pada pemeriksaan bootstrap. Terminal pengguna telah memverifikasi readiness 21/21 dan loop 13/14 menjadi 14/14 setelah satu revisi. Codex masih tidak dapat mengakses named pipe Docker. Tes Python dengan transport terkontrol tidak menggantikan hasil Docker.

Runtime staging/report sekarang berada di `runtime.php`. Bangun ulang image setelah perubahan runtime. Evaluasi awal/akhir memakai image lain dan suite tersendiri; lihat [evaluator](../evaluation/README.md). `ProductsEdgeTest` tetap hanya kesiapan internal, bukan evaluator akhir.

## Batas integritas laporan

Controller dan PHPUnit berjalan dalam proses/konteks yang dapat dipengaruhi kandidat. XML, log, dan stdout bukan bukti tahan manipulasi. Pembatasan container melindungi akses host yang dibagikan; tidak membuktikan kandidat tidak mengganggu proses test. Tidak ada klaim keamanan/verifikasi adversarial. Implementasi `check-products` belum boleh dipakai sebagai dasar kesimpulan penelitian sebelum kesiapan image benar-benar lulus.
