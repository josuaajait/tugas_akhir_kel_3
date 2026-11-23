# Tampilan CLI bergaya PTerm

Pengguna memilih adaptasi tampilan pterm/cli-template ke Python pada 23 November 2026. Tujuannya membuat seluruh command mudah dibaca di terminal, terutama kemajuan loop dan hasil tiap percobaan.

## Pendekatan

PTerm asli memerlukan pembungkus Go dan build tambahan. Pilihan pengguna adalah adaptasi Python standard library: header, label berwarna, tabel, spinner tahap berjalan, dan ringkasan. Tidak menyalin template atau menambahkan CI/release Go.

## Kontrak

- Terminal memakai tampilan manusia otomatis; pipe/redirection mempertahankan JSON. `--pretty` dan `--json` dapat ditulis sebelum/sesudah subcommand. `--no-color` dan `NO_COLOR` mematikan ANSI; `TERM=dumb` mematikan animasi/warna.
- `prompt` tetap mengeluarkan prompt murni. Help tetap tersedia untuk semua command, dengan header di terminal.
- Seluruh hasil terstruktur ditampilkan tanpa mengubah nilai, termasuk false, nol, N/A, ERROR dan hasil provisional. LOLOS hanya berasal dari hasil loop internal.
- Progress hanya mencerminkan tahap nyata; tidak mengarang persentase. Diagnostik/progress di stderr; hasil di stdout. Input `start` tidak tertutup spinner.
- Pertahankan exit code, aturan max3/byte-identik, prompt/model, suite, versi 0.5.0/protokol 1.0, serta arsip lama. Hash sumber baru akan berubah secara wajar; fingerprint suite/image tetap.
- Buat renderer terpisah, context-local untuk pemanggilan CLI; pemanggilan library tidak menghasilkan UI. Sanitasi kontrol terminal untuk tampilan saja; JSON/arsip asli tidak diubah.

## Validasi

Tes kontrak CLI untuk terminal/pipe, flags, prompt, error, warna, data bersarang dan lebar sempit; smoke loop memakai dependency eksternal terkendali, memeriksa hasil dan arsip nyata. Jalankan seluruh unittest serta doctor/help. Tidak menjalankan ulang eksperimen Docker/Qwen untuk perubahan presentasi.
