# Bukti pencatatan eksperimen FR-16

Setiap generasi dan loop baru menyimpan provenance di `run_manifest.json`. Semua entry point yang memakai loop yang sama, termasuk `start` dan `pilot-run`, mendapatkan metadata ini setelah loop dibuat.

| Yang dicatat | Lokasi dan pengertian |
|---|---|
| ID run, versi aplikasi dan hash sumber | Manifest lama tetap menyimpan versi aplikasi. `provenance.prototype_source_sha256` mencakup semua modul Python langsung di `critic_agent/`, termasuk perubahan lokal, dengan newline dinormalisasi. |
| Spesifikasi dan prompt | Arsip `spec.json` dan `prompt.txt` tetap disertai SHA-256. Untuk penggunaan ulang kandidat awal, manifest asal juga diarsipkan dan riwayat menandai bahwa Qwen tidak dipanggil ulang. |
| Identitas model | `provenance.model_identity` menyimpan nama yang diminta, nama yang ditemukan, digest, kuantisasi, dan versi Ollama. Nilai berasal dari layanan lokal sebelum run. Status dan daftar `issues` menyatakan data yang tidak berhasil diperoleh. |
| Konfigurasi model dan retry aktual | `model_request` menyimpan suhu, seed, konteks, batas keluaran, timeout dan jejak HTTP untuk setiap pemanggilan model. Di loop, data ini berada per percobaan dalam `history.json` dan `attempts/N/result.json`. Durasi dan hasil tiap percobaan HTTP tercatat terpisah dari revisi. |
| Lingkungan | Manifest menyimpan Python/platform, arsitektur, CPU, jumlah CPU logis, RAM fisik, serta versi PHP CLI dan Docker Server bila dapat diperoleh. GPU NVIDIA dan VRAM berasal dari `nvidia-smi` bila tersedia. Nilai `null` berarti data tidak teramati. |
| Test dan runner | Metadata menyimpan image yang dipilih, timeout pengujian, fingerprint kontrak resource atau fingerprint sumber suite products lokal. Image ID aktual dari hasil Docker dan profil container tercatat pada hasil dinamis. Hash suite products lokal mengidentifikasi sumber di checkout. Image ID aktual mengidentifikasi paket yang dieksekusi. Evaluator menyimpan hash suite dan image ID pada hasilnya sendiri. |

`pilot-metadata` dan `pilot-report` membaca hitungan HTTP aktual beserta jumlah panggilan yang memiliki jejak. Untuk arsip lama tanpa jejak, hitungan HTTP dan retry bernilai `null`. Pencatatan ini tidak mengubah respons model mentah atau menghitung ulang retry historis. Snapshot tag/digest adalah observasi sebelum run. Konfigurasi final dan penguncian identitas model tetap bagian dari pembekuan eksperimen.

## Bukti live

Pada 19 November 2026, sebuah smoke run di luar grid pilot mencapai **LOLOS 14/14 internal** pada image products v2. Manifest mencatat Qwen Q4_K_M, digest `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`, Ollama 0.40.16, Docker 29.9.2, RAM 16 GiB dan NVIDIA RTX 4060 Laptop GPU dengan 8.188 MiB VRAM. Jejak model mencatat satu HTTP sukses untuk suhu 0, seed 42, konteks 8.192, batas keluaran 4.096, dan timeout 300 detik. Arsip lokal ada di `work/fr16-smoke/20261119T084320Z_loop_507df259886e496f8020063c916809ac/`.

Tes terkontrol memverifikasi satu retry yang berhasil, dua percobaan yang gagal, dan pencatatan seed serta percobaan HTTP pada revisi. Seed efektif tersimpan pada setiap percobaan. Jadwal seed per kondisi, `pair_id` dan kondisi A/B menunggu implementasi FR-20. Penetapan konfigurasi dan anggaran akhir masih perlu dicatat sebelum pembekuan.
