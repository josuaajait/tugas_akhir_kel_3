# Lembar keputusan manusia

Gunakan `forms/decisions.json` untuk keputusan yang akan diikat protokol. Dokumen ini menjelaskan bahan keputusan, tidak menyetujui pilihan apa pun.

| Keputusan | Bahan | Yang harus dicatat |
|---|---|---|
| P-06 dan K2 | PRD12.4–12.5 dan14.2; paket komponen16kasus development | Jumlah/distribusi per asal/cakupan, duplikat dan held-out; ambang precision minimum, recall minimum, FPR maksimum; alasan dan persetujuan pembimbing sebelum sumatif. Jangan menggabungkan hasil sintetis dan Qwen formatif. |
| P-07 | PRD12.6; forms/assignments.json | Pembuat manusia, reviewer berbeda, artefak, waktu dan hasil nyata. Nama yang ditugaskan tidak berarti pekerjaan selesai. |
| FR-20/A/B | PRD12.2–12.3; jadwal20pasangan | Keputusan melakukan A/B dan alasan anggaran; kandidat awal bersama, kedua kondisi, seed/urutan/budget, laporan seluruh error/retry. Jika A/B dibatalkan, dokumentasikan batas atribusi dan revisi protokol; draf ab-run saat ini mensyaratkan execute. |
| Konfigurasi/freeze | Pilot development dan protokol draf | Model/digest aktual, suhu/konteks/panjang respons, seed, timeout, batas revisi dan profil image. Pilih berdasarkan validitas/keragaman/biaya pilot, tanpa menyetel pada hasil akhir. |

Paket final memuat lima soal × empat pengulangan =20pasangan/40cabang. Anggaran maksimal140panggilan logis berasal dari20generasi awal +20×2×3revisi; jumlah aktual bisa lebih kecil karena lulus/identik. Ini batas jadwal, bukan biaya aktual atau jaminan pengulangan menghasilkan kandidat independen.

Ambang80/75/20 yang pernah diusulkan tidak diisikan sebagai keputusan. Seluruh ambang pada form baru null hingga diputuskan. Opsi development Qwen2.5:7b-instruct, suhu0.2 dan konteks8192/panjang4096 juga bukan digest/config final yang telah disahkan.

Jangan menyatakan `component_review: reviewed` berdasarkan formulir soal atau laporan komponen provisional. Review komponen memerlukan bukti independen, dua pemeriksa, kondisi blind sebenarnya dan prediksi baru sesudah review. Keputusan P-06/P-07 tambahan direkam pada `forms/research-decisions.json`; lampirkan berkas yang selesai pada manifest baru sebagai evidence tambahan.
