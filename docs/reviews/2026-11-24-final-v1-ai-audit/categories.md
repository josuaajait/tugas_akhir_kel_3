# Hasil pemeriksaan categories

42 kasus ditelusuri. Semua fixture/expected yang tercantum konsisten dengan aturan yang dideklarasikan untuk input tersebut. Temuan F1–F3 berarti cakupan atau penanganan error paket masih perlu diperbaiki; konsistensi baris tidak sama dengan persetujuan paket.

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
| `POST_missing_name` | Input missing pada name: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_null_name` | Input null pada name: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_empty_name` | Input empty pada name: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_whitespace_name` | Input whitespace pada name: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_type_name` | Input type pada name: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_object_name` | Input object pada name: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_max_name` | Input max pada name: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_missing_description` | Input missing pada description: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_null_description` | Input null pada description: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_empty_description` | Input empty pada description: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_whitespace_description` | Input whitespace pada description: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_type_description` | Input type pada description: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_object_description` | Input object pada description: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_max_description` | Input max pada description: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_missing_name` | Input missing pada name: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_null_name` | Input null pada name: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_empty_name` | Input empty pada name: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_whitespace_name` | Input whitespace pada name: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_type_name` | Input type pada name: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_object_name` | Input object pada name: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_max_name` | Input max pada name: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_missing_description` | Input missing pada description: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_null_description` | Input null pada description: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_empty_description` | Input empty pada description: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_whitespace_description` | Input whitespace pada description: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_type_description` | Input type pada description: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_object_description` | Input object pada description: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_max_description` | Input max pada description: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_boundary_max_name` | Nilai valid boundary_max pada name: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_max_description` | Nilai valid boundary_max pada description: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `PUT_boundary_max_name` | Nilai valid boundary_max pada name: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_max_description` | Nilai valid boundary_max pada description: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |

Untuk melihat payload persis, expected status/body/state, nama kontrol negatif dan path bukti, cari resource/case_id ini di case-audit.json. Form asli dan form kerja manusia tidak diubah.
