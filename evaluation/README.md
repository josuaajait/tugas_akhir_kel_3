# Evaluator products pengembangan

`evaluate-products` menjalankan evaluasi setelah loop selesai, tanpa generasi atau feedback. Paket ini FR-15 untuk kontrak products tetap, belum lintas resource. Suite dibuat setelah keluaran pengembangan pertama diamati; belum merupakan paket evaluasi akhir yang ditinjau/dibekukan.

```powershell
python -m critic_agent harness-build
python -m critic_agent harness-check
python -m critic_agent evaluation-build
python -m critic_agent evaluate-products runs/20261104T031502Z_loop_713c3f8803f441929ae6ed8f38077232
```

Gunakan CLI `evaluation-build`: CLI membuat konteks sementara yang berisi paket ini dan runtime saat ini, kemudian membersihkannya. `docker build evaluation/` langsung tidak memiliki salinan runtime yang diperlukan. Image default `critic-laravel-evaluation:dev` terpisah dari `critic-laravel:dev`. `--base-image` memilih harness terkunci; jangan menggunakan image evaluator sebagai base internal. Evaluator menolak mode reference/candidate milik loop.

Fingerprint mencakup kode suite, konfigurasi, entrypoint, Dockerfile, metadata, dan runtime bersama yang disalin saat build. Label image harus cocok dengan sumber sebelum kandidat dinilai. Image ID aktual yang sama dipakai untuk readiness dan kedua kandidat; masing-masing container baru memakai fixture SQLite in-memory baru. Tidak ada hasil test acuan yang masuk prompt revisi. Label/hash membantu reproduksibilitas build tepercaya, bukan bukti ketahanan terhadap kandidat yang sengaja memanipulasi proses PHPUnit.

| Kelompok | Kasus |
| --- | ---: |
| Empty/list/create/show/update/delete | 6 |
| Missing ID pada show/update/destroy | 3 |
| Sepuluh payload invalid pada store dan update | 20 |
| Batas valid | 2 |
| Update mempertahankan SKU sendiri | 1 |
| Rangkaian CRUD | 1 |
| Total | 33 |

Fixture ditanam melalui query DB, tanpa memakai controller/model kandidat. Request memakai helper JSON Laravel. Snapshot DB memeriksa efek samping. Cakupan ini tidak membuktikan semua kemungkinan pelanggaran kontrak telah ditangkap; tambah matriks cakupan dan validasi mutasi sebelum pembekuan akhir.

Arsip sumber wajib konsisten antara manifest, history, spesifikasi, dan hash kode awal/akhir. Loop ERROR dikecualikan. File yang diklaim tersedia tetapi hilang/berubah ditolak. Tidak ada kode yang diekstrak mendapat0/33 dan executed=false. Sintaks invalid dibuktikan melalui `php -n -l` di container evaluator dan dicatat UNLOADABLE_CODE0/33 tanpa testcase fiktif. Kesalahan yang menghasilkan laporan lengkap tetap dihitung dari33 kasus. Timeout/crash tanpa bukti penyebab kandidat, suite parsial, kegagalan infrastruktur, dan kesiapan gagal menghasilkan ERROR dengan metrik pasangan tidak tersedia. Jika penyebab kandidat kelak dapat dipastikan, catat bukti dan terapkan kebijakan PRD12.3 sebelum pembekuan.

`evaluation_result.json` berisi hasil kedua posisi, raw runner results, image ID, suite hash, status sumber, uplift, dan hitungan repair/regression. Snapshot manifest/history/kode berada di folder yang sama; log/XML detail di subfolder harness yang dirujuk. Satu pasangan hanya memberi indikator deskriptif, bukan estimasi efektivitas umum. Penyebut nol adalah N/A. Agregasi antarspesifikasi/A-B belum tersedia.

Verifikasi saat implementasi: lint dan hitungan provider mengonfirmasi33 kasus terdefinisi. Eksekusi fungsional Laravel di image evaluator masih menunggu terminal pengguna karena named pipe Docker ditolak dari Codex.
