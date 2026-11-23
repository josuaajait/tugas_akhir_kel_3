# Pelaporan eksperimen FR-18

Untuk mereproduksi laporan dari arsip pilot lokal, jalankan dari root proyek.

```powershell
python -m critic_agent pilot-report runs/pilot-2026-11-19/products/manifest.json runs/pilot-2026-11-19/resources/manifest.json --evaluations evaluations/pilot-2026-11-19
```

Opsi `--evaluations` membaca `evaluation_result.json` dari direktori yang diberikan beserta subdirektorinya. Report dihubungkan lewat ID run dan status sumber. Untuk pasangan yang berhasil dievaluasi, hash kode awal dan akhir dibandingkan dengan kandidat di arsip loop dan hash di riwayat. Jumlah kasus dan identitas suite serta image juga diperiksa. Dua report berhasil untuk ID run yang sama menghasilkan error agar pengguna dapat memilih direktori bukti yang tepat secara eksplisit. Percobaan evaluator yang gagal tetap tercatat bila ada hasil retry yang berhasil.

| Data | Cara menghitung |
|---|---|
| `n_valid` | Job berstatus LOLOS atau BELUM LOLOS, termasuk job yang belum dievaluasi |
| `n_pair` | Job valid yang memiliki pasangan awal–akhir dari evaluator |
| Pass rate awal/akhir | Jumlah assertion lulus dibagi total assertion pada tiap posisi, per kelompok spesifikasi, model, suhu, dan batas revisi yang memakai suite/image sama |
| Uplift | Selisih pass rate akhir dan awal per pasangan. Rata-rata dibagi `n_pair`. |
| Repair | Kandidat yang berubah dari belum lulus acuan menjadi lulus penuh, dibagi kandidat yang belum lulus acuan sejak awal |
| Regresi | Kandidat yang berubah dari lulus penuh menjadi belum lulus acuan, dibagi kandidat yang lulus acuan sejak awal |
| Rata-rata revisi | Total revisi pada job valid dibagi `n_valid`, termasuk job yang langsung lulus dengan nol revisi |
| Status dan error | Status/alasan berhenti loop, ERROR evaluator per alasan dan per arsip, serta job valid tanpa pasangan acuan |

Persentase dengan penyebut nol bernilai `null`. Agregat lintas suite menyajikan hitungan pasangan dan rata-rata uplift per pasangan. Pass rate assertion tersedia pada kelompok dengan satu suite/image. Laporan mempertahankan pengulangan pilot yang menghasilkan kode identik dan mencatat hash awal per job. Satu job yang tidak dapat dimuat karena sintaks tetap membawa skor awal 0 sesuai aturan evaluator.

## Verifikasi arsip development

CLI membaca 27 run valid dan 27 pasangan. Hasil keseluruhan adalah 21 LOLOS dan enam BELUM LOLOS karena `identical_code`, dengan 0 ERROR loop dan 0 ERROR evaluator. Rata-rata revisi 23/27 atau 0,85. Rata-rata uplift per pasangan adalah 5,55 poin persentase. Repair 9/15 atau 60%, dan regresi 0/12 atau 0%. Hasil per spesifikasi dan suhu tersedia di [laporan pilot](pilot-development-2026-11-19.md).

Snapshot hasil CLI tersedia di `runs/pilot-2026-11-19/fr18-cli-report.json`. Laporan A/B dan `N_AB` memerlukan identitas kondisi dan pasangan dari FR-20.
