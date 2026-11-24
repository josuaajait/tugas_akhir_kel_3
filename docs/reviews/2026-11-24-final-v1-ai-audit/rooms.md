# Hasil pemeriksaan rooms

50 kasus ditelusuri. Semua fixture/expected yang tercantum konsisten dengan aturan yang dideklarasikan untuk input tersebut. Temuan F1–F3 berarti cakupan atau penanganan error paket masih perlu diperbaiki; konsistensi baris tidak sama dengan persetujuan paket.

[Ringkasan dan tiga temuan](LAPORAN.md) · [Data lengkap358 kasus](case-audit.json) · [Bukti eksperimen baru](evidence/native-probes.json)

Kolom bukti menunjukkan empat eksekusi acuan positif lama per kasus: dua gaya controller × dua pengulangan. Hasil ini diverifikasi ulang dari arsip23 November; bukan empat run baru. Pemeriksaan baru atas controller cacat ada di laporan utama.

| Kasus | Yang diperiksa | Cakupan Critic | Konsistensi input/expected | Temuan terkait paket |
|---|---|---|---|---|
| `index` | GET koleksi: array JSON, ID integer unik, nilai terikat ke ID, isi database tidak berubah. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | F3 |
| `store` | POST valid: HTTP 201, respons sesuai input, satu baris baru tersimpan, record lama tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `show` | GET target: ID dan seluruh field sesuai record yang diminta; database tidak berubah. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | F1, F3 |
| `update` | PUT valid: HTTP 200, respons/DB sesuai input dan ID target, record pembanding tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `destroy` | DELETE: HTTP 204/body kosong, hanya target dihapus, record pembanding tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | F1 |
| `missing_GET` | GET ID tidak ada: HTTP 404/objek JSON, payload valid bila PUT, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | F3 |
| `missing_PUT` | PUT ID tidak ada: HTTP 404/objek JSON, payload valid bila PUT, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | F3 |
| `missing_DELETE` | DELETE ID tidak ada: HTTP 404/objek JSON, payload valid bila PUT, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | F3 |
| `empty` | GET database kosong: HTTP 200, data array kosong, database tetap kosong. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F3 |
| `sequence` | Create/read/update/read/list/delete/read missing: status/data tiap langkah sesuai, database kosong di akhir. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F3 |
| `POST_missing_label` | Input missing pada label: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_null_label` | Input null pada label: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_empty_label` | Input empty pada label: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_whitespace_label` | Input whitespace pada label: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_type_label` | Input type pada label: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_object_label` | Input object pada label: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_max_label` | Input max pada label: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_missing_capacity` | Input missing pada capacity: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_null_capacity` | Input null pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_empty_capacity` | Input empty pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_whitespace_capacity` | Input whitespace pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_type_capacity` | Input type pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_object_capacity` | Input object pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_fraction_capacity` | Input fraction pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_min_capacity` | Input min pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_max_capacity` | Input max pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_missing_label` | Input missing pada label: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_null_label` | Input null pada label: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_empty_label` | Input empty pada label: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_whitespace_label` | Input whitespace pada label: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_type_label` | Input type pada label: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_object_label` | Input object pada label: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_max_label` | Input max pada label: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_missing_capacity` | Input missing pada capacity: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_null_capacity` | Input null pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_empty_capacity` | Input empty pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_whitespace_capacity` | Input whitespace pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_type_capacity` | Input type pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_object_capacity` | Input object pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_fraction_capacity` | Input fraction pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_min_capacity` | Input min pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_max_capacity` | Input max pada capacity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_boundary_max_label` | Nilai valid boundary_max pada label: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_min_capacity` | Nilai valid boundary_min pada capacity: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_max_capacity` | Nilai valid boundary_max pada capacity: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_numeric_string_capacity` | Nilai valid numeric_string pada capacity: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `PUT_boundary_max_label` | Nilai valid boundary_max pada label: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_min_capacity` | Nilai valid boundary_min pada capacity: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_max_capacity` | Nilai valid boundary_max pada capacity: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_numeric_string_capacity` | Nilai valid numeric_string pada capacity: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |

Untuk melihat payload persis, expected status/body/state, nama kontrol negatif dan path bukti, cari resource/case_id ini di case-audit.json. Form asli dan form kerja manusia tidak diubah.
