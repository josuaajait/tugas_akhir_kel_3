# Hasil pemeriksaan shipments

116 kasus ditelusuri. Semua fixture/expected yang tercantum konsisten dengan aturan yang dideklarasikan untuk input tersebut. Temuan F1–F3 berarti cakupan atau penanganan error paket masih perlu diperbaiki; konsistensi baris tidak sama dengan persetujuan paket.

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
| `POST_missing_tracking_code` | Input missing pada tracking_code: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_null_tracking_code` | Input null pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_empty_tracking_code` | Input empty pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_whitespace_tracking_code` | Input whitespace pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_type_tracking_code` | Input type pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_object_tracking_code` | Input object pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_min_tracking_code` | Input min pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_max_tracking_code` | Input max pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_unique_tracking_code` | Input unique pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_missing_reference_code` | Input missing pada reference_code: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_null_reference_code` | Input null pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_empty_reference_code` | Input empty pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_whitespace_reference_code` | Input whitespace pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_type_reference_code` | Input type pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_object_reference_code` | Input object pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_max_reference_code` | Input max pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_unique_reference_code` | Input unique pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_missing_quantity` | Input missing pada quantity: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_null_quantity` | Input null pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_empty_quantity` | Input empty pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_whitespace_quantity` | Input whitespace pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_type_quantity` | Input type pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_object_quantity` | Input object pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_fraction_quantity` | Input fraction pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_min_quantity` | Input min pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_max_quantity` | Input max pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_missing_priority` | Input missing pada priority: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_null_priority` | Input null pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_empty_priority` | Input empty pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_whitespace_priority` | Input whitespace pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_type_priority` | Input type pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_object_priority` | Input object pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_fraction_priority` | Input fraction pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_min_priority` | Input min pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_max_priority` | Input max pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_missing_note` | Input missing pada note: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_null_note` | Input null pada note: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_empty_note` | Input empty pada note: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_whitespace_note` | Input whitespace pada note: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_type_note` | Input type pada note: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_object_note` | Input object pada note: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_max_note` | Input max pada note: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_missing_tracking_code` | Input missing pada tracking_code: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_null_tracking_code` | Input null pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_empty_tracking_code` | Input empty pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_whitespace_tracking_code` | Input whitespace pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_type_tracking_code` | Input type pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_object_tracking_code` | Input object pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_min_tracking_code` | Input min pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_max_tracking_code` | Input max pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_unique_tracking_code` | Input unique pada tracking_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_missing_reference_code` | Input missing pada reference_code: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_null_reference_code` | Input null pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_empty_reference_code` | Input empty pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_whitespace_reference_code` | Input whitespace pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_type_reference_code` | Input type pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_object_reference_code` | Input object pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_max_reference_code` | Input max pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_unique_reference_code` | Input unique pada reference_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_missing_quantity` | Input missing pada quantity: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_null_quantity` | Input null pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_empty_quantity` | Input empty pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_whitespace_quantity` | Input whitespace pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_type_quantity` | Input type pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_object_quantity` | Input object pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_fraction_quantity` | Input fraction pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_min_quantity` | Input min pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_max_quantity` | Input max pada quantity: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_missing_priority` | Input missing pada priority: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_null_priority` | Input null pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_empty_priority` | Input empty pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_whitespace_priority` | Input whitespace pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_type_priority` | Input type pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_object_priority` | Input object pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_fraction_priority` | Input fraction pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_min_priority` | Input min pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_max_priority` | Input max pada priority: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_missing_note` | Input missing pada note: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_null_note` | Input null pada note: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_empty_note` | Input empty pada note: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_whitespace_note` | Input whitespace pada note: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_type_note` | Input type pada note: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_object_note` | Input object pada note: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_max_note` | Input max pada note: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_boundary_min_tracking_code` | Nilai valid boundary_min pada tracking_code: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_max_tracking_code` | Nilai valid boundary_max pada tracking_code: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_max_reference_code` | Nilai valid boundary_max pada reference_code: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_min_quantity` | Nilai valid boundary_min pada quantity: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_max_quantity` | Nilai valid boundary_max pada quantity: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_numeric_string_quantity` | Nilai valid numeric_string pada quantity: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_min_priority` | Nilai valid boundary_min pada priority: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_max_priority` | Nilai valid boundary_max pada priority: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_numeric_string_priority` | Nilai valid numeric_string pada priority: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_max_note` | Nilai valid boundary_max pada note: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `PUT_boundary_min_tracking_code` | Nilai valid boundary_min pada tracking_code: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_max_tracking_code` | Nilai valid boundary_max pada tracking_code: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_max_reference_code` | Nilai valid boundary_max pada reference_code: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_min_quantity` | Nilai valid boundary_min pada quantity: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_max_quantity` | Nilai valid boundary_max pada quantity: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_numeric_string_quantity` | Nilai valid numeric_string pada quantity: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_min_priority` | Nilai valid boundary_min pada priority: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_max_priority` | Nilai valid boundary_max pada priority: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_numeric_string_priority` | Nilai valid numeric_string pada priority: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_max_note` | Nilai valid boundary_max pada note: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_own_tracking_code` | PUT mempertahankan nilai unik milik target sendiri: diterima, target benar dan pembanding tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_own_reference_code` | PUT mempertahankan nilai unik milik target sendiri: diterima, target benar dan pembanding tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |

Untuk melihat payload persis, expected status/body/state, nama kontrol negatif dan path bukti, cari resource/case_id ini di case-audit.json. Form asli dan form kerja manusia tidak diubah.
