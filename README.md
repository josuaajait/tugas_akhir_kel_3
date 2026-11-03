# Critic Agent

Prototipe TA untuk memeriksa controller CRUD REST API Laravel hasil Qwen2.5-7B-Instruct. Versi 0.1.0 menyediakan **fondasi generasi dan analisis statis**, belum merupakan MVP lengkap.

Tahap berikutnya sudah ditambahkan: kode harness Laravel, controller acuan, dan runner Docker untuk kontrak products. **Belum terverifikasi melalui Docker** pada perangkat ini. Petunjuk dan batasan: [harness/README.md](harness/README.md).

## Yang tersedia

- Validasi spesifikasi JSON yang ketat dan prompt dengan kontrak Laravel tetap.
- Client Ollama lokal dengan seed/suhu tercatat, timeout, dan satu retry gangguan komunikasi.
- Arsip unik tiap generasi: spesifikasi, prompt, respons mentah yang diterima, kode, hash, dan manifest; termasuk kegagalan ekstraksi/layanan.
- Pemeriksaan sintaks serta namespace/class/method/signature melalui tokenizer PHP. Controller tidak dieksekusi oleh perintah ini.
- Pemeriksaan kesiapan Python, PHP, Docker, layanan Ollama, dan nama model.
- Perintah `harness-build`, `harness-check`, dan `check-products`; parser JUnit, pembatasan output, dan arsip pemeriksaan container. Test dinamis nyata masih menunggu Docker tersedia.

Status `AWAITING_DYNAMIC_TESTS` berarti tahap fondasi selesai tanpa temuan statis atau kode telah diekstrak, bergantung perintah yang dijalankan. **Bukan LOLOS fungsional**. `generate` tidak otomatis menjalankan `analyze`.

## Menjalankan dari folder proyek

Diperlukan Python 3.11+. Gunakan terminal pada folder yang berisi README ini. Paket Python tambahan tidak diperlukan untuk perintah di bawah.

```powershell
python -m critic_agent --help
python -m critic_agent doctor
python -m critic_agent validate examples/products.json
python -m critic_agent prompt examples/products.json
python -m critic_agent analyze examples/products.json examples/StructureOnlyController.php
python -m unittest discover -s tests -v
```

`StructureOnlyController.php` adalah fixture struktur dengan method kosong, bukan implementasi CRUD yang benar. Gunakan untuk memastikan pemeriksa statis bekerja; jangan memakainya sebagai controller acuan fungsional.

Setelah Ollama terpasang dan aktif serta model sudah diunduh:

```powershell
ollama pull qwen2.5:7b-instruct
python -m critic_agent generate examples/products.json --seed 42 --temperature 0.2 --timeout 300
```

Suhu/seed ini hanya konfigurasi pengembangan; konfigurasi penelitian ditentukan setelah pilot. Layanan dipanggil melalui localhost. Model aktual, digest dan kuantisasi masih perlu diverifikasi sebelum eksperimen. Perintah `generate` memerlukan Ollama; validasi/prompt tidak memerlukan layanan tersebut. PHP diperlukan untuk `analyze`.

Kode keluar: 0 = perintah berhasil pada tahapnya; 1 = temuan statis/format; 2 = input atau akses file invalid; 3 = prasyarat/layanan bermasalah. Tidak ada perintah yang melaporkan `LOLOS` pada versi fondasi.

## Langkah berikutnya

1. Pasang dan verifikasi Docker Desktop dengan backend WSL2 serta Ollama pada perangkat pengembangan.
2. Siapkan image PHP/Laravel dan controller acuan CRUD yang telah diuji; kunci versi/dependensi.
3. Tambahkan template test internal untuk status, respons, dan perubahan data.
4. Integrasikan pemeriksaan statis/dinamis, feedback, dan maksimal tiga revisi; pengujian dinamis wajib sebelum status LOLOS tersedia.
5. Tambahkan evaluator test acuan independen dan jalankan pilot.

Rencana fondasi: `docs/superpowers/plans/2026-11-03-foundation.md`. Batas MVP: `docs/spec-mvp.md`. Catatan kemajuan: `docs/progress.md`.

Pengujian client saat ini memakai transport terkontrol; hasilnya tidak membuktikan Qwen atau Docker sudah berjalan. Analisis statis menggunakan PHP asli bila tersedia; pengujian itu dilewati otomatis bila PHP tidak ditemukan.

## Referensi implementasi

- [Ollama Generate API](https://docs.ollama.com/api/generate)
- [PHP token_get_all](https://www.php.net/manual/en/function.token-get-all.php)
- [Laravel routing](https://laravel.com/docs/12.x/routing)

Harness awal mengunci Laravel 12.70.2 dan PHPUnit 11.5.57 dalam composer.lock. Ketepatan image/runtime serta 21 kasus Laravel masih perlu dibuktikan sebelum pembekuan eksperimen.
