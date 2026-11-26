# Paket evaluasi final-v2

Versi ini memperbaiki tiga temuan audit24November2026: operasi sukses pada ID kedua, input string sah sepanjang1–2karakter, dan klasifikasi respons JSON rusak. `final-v1` beserta sumber, image dan buktinya dipertahankan sebagai versi historis.

| Soal | Internal | Acuan | Kontrol benar | Mutasi | Observasi validasi yang direncanakan |
|---|---:|---:|---:|---:|---:|
| categories |23|53|2|46|102|
| rooms |19|57|2|50|110|
| assets |21|80|2|68|146|
| courses |21|84|2|69|148|
| shipments |29|127|2|98|206|
| Total |113|401|10|331|712|

Kontrak field dan skema input1.0 tetap sama; identitas spesifikasi menjadi `final_<resource>_v2`. Kasus baru ada pada suite internal dan acuan dengan fixture terpisah.113kasus berlabel internal_covered dan288reference_only; tidak ada kasus lama yang dihapus agar angka terlihat lebih baik.

## Perubahan perilaku evaluator

- `show_second`, `update_second`, `destroy_second` meminta ID kedua yang sudah ada, kemudian memeriksa respons dan keadaan target/pembanding menurut ID.
- `POST/PUT_short1/short2_<field>` menguji tujuh field required/string tanpa batas minimum, termasuk field unique yang sah dengan nilai pendek.
- `Assertions::object` mengubah JsonException menjadi assertion failure. Pemeriksaan raw JSON dilakukan sebelum helper Laravel yang dapat melempar ulang HttpResponseException, termasuk POST/PUT, validasi422 dan sequence-create. Kesalahan lingkungan, timeout, hasil parsial dan cleanup tetap ERROR.
- Kontrol baru menguji salah target, batas min:3 yang tidak diminta, serta malformed JSON biasa dan malformed201/200/422 yang dibawa response exception.
- Katalog/sumber kontrol berasal dari aset final-v2 yang terikat hash; materialisasi tidak memerlukan spesifikasi/profil final-v1 tersembunyi.

## Perintah

```powershell
python -m critic_agent final-validate --package final-v2 --local-only --output evaluations/final-v2-local
python -m critic_agent final-validate --package final-v2 --build --output evaluations/final-v2-validation
python -m critic_agent ab-smoke --package final-v2 --resource categories --scenario repair --output runs/ab-v2-synthetic
```

`--local-only` melakukan lint, discovery/provider dan assertion-probe tepercaya; tidak mengeksekusi controller. Pengujian fungsional hanya dilakukan dalam Docker. `ab-smoke` memakai fixture lokal, tanpa Qwen. Pilih versi secara eksplisit; default library/smoke final-v1 tetap tersedia untuk kompatibilitas arsip.

## Bukti dan review

Hasil aktual, hash/image dan batas verifikasi tercatat di [manifest paket](manifest.json). Angka rencana di atas bukan pengganti hasil aktual.

Form sumber `review/*.json` selalu kosong dan ikut fingerprint. Gunakan formulir eksternal dalam paket review; jangan memindahkan keputusan/nama/tanggal dari versi lama sebagai review yang sudah selesai. Persiapan teknis tidak membekukan protokol, tidak mengesahkan manusia, dan tidak menjalankan20pasangan final.
