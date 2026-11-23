# Pembanding feedback A/B development · FR-20

`run-ab` menjalankan satu pasangan. Kondisi A menerima temuan spesifik Critic. Kondisi B menerima teks generik tetap. Kedua kondisi memakai pembungkus prompt, kontrak, model, opsi, batas revisi dan pemeriksaan internal yang sama. Prompt dan seluruh temuan pemeriksaan tetap disimpan di arsip cabang. Hanya feedback yang diizinkan untuk masing-masing kondisi masuk ke permintaan Qwen.

```powershell
python -m critic_agent run-ab examples/products.json --image critic-laravel:products-internal-v2 --seed 42 --order-seed 7 --revision-seeds 43 44 45
```

Command menghasilkan satu respons awal dan meneruskannya ke kedua cabang. Opsi `--initial-run` menerima arsip generasi yang sudah ada setelah pemeriksaan spesifikasi, opsi model dan hash kandidat. Respons baru yang gagal format bisa menjadi input awal bersama untuk kedua kondisi. Jumlah angka pada `--revision-seeds` menetapkan anggaran revisi, maksimal tiga. Seed ke-N dipakai untuk revisi ke-N pada kedua kondisi. `--order-seed` menetapkan urutan teracak yang tercatat di `pair.json`. Untuk beberapa pasangan, jadwalkan seed urutan dan `--repetition` sebelum eksekusi agar urutan bisa diseimbangkan. Books dan inventory memakai harness serta evaluator resource masing-masing.

Setelah kedua loop selesai, evaluator memeriksa kode awal bersama sekali dan kedua versi akhir. Hasil awal dapat dirujuk cabang berikutnya bila hash kandidat, image dan suite sesuai. `pair.json` mencatat `pair_id`, kondisi, seed, alasan berhenti, biaya awal dan biaya aktual tiap cabang, serta lokasi arsip loop dan evaluator. Jika kedua pasangan lengkap, `n_ab` bernilai 1 dan `delta_final_pp` adalah pass rate akhir A dikurangi B. Jika salah satu cabang atau evaluasi gagal, hasil yang tersedia tetap tersimpan, `n_ab` bernilai 0, dan delta bernilai `null`. Biaya pengujian dicatat dalam durasi attempt. Biaya token memakai respons model yang memiliki hitungan.

Implementasi ini menjalankan satu pasangan development per command. Grid A/B akhir dan agregasi lintas pasangan masih menunggu spesifikasi final, jadwal pengulangan, konfigurasi beku, serta seluruh gerbang FR-19.

## Verifikasi live

Pada 19 November 2026, satu pasangan products menggunakan kandidat historis yang sama di kedua cabang, suhu 0,2, seed awal 42, dan jadwal revisi 43/44/45. Seed urutan 7 menghasilkan urutan A lalu B. Hash kode awal kedua cabang identik. Evaluator acuan v1 menghasilkan 31/33 untuk kode awal, dan B merujuk bukti acuan awal yang sama dengan A. Readiness internal products v2 lulus 21/21.

| Kondisi | Internal awal → akhir | Acuan awal → akhir | Revisi dan penghentian | Token prompt / keluaran revisi |
|---|---|---|---|---:|
| A, spesifik | 13/14 → 14/14 | 31/33 → 33/33 | 1, LOLOS | 1.349 / 425 |
| B, generik | 13/14 → 13/14 | 31/33 → 31/33 | 2, BELUM LOLOS karena kode identik | 2.393 / 850 |

Selisih akhir A–B adalah +6,06 poin persentase untuk satu pasangan development. Kandidat awal diimpor dari arsip, sehingga biaya generasi awal tidak dibebankan ke pasangan ini. Hasil pada contoh terpilih ini memverifikasi alur. Uji efek pada beberapa spesifikasi masih diperlukan.

Arsip lokal `runs/ab-development/ab_2154541b80e84a709c2e1792b0236097/pair.json` menunjuk hasil cabang, prompt, respons mentah, dan evaluator. Pemeriksaan arsip mengonfirmasi seed revisi pertama 43 pada kedua kondisi, payload generik yang hanya berisi pesan tetap, serta rujukan evaluasi awal bersama. Seluruh 175 tes Python lulus.
