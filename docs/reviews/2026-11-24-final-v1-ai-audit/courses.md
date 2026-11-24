# Hasil pemeriksaan courses

77 kasus ditelusuri. Semua fixture/expected yang tercantum konsisten dengan aturan yang dideklarasikan untuk input tersebut. Temuan F1–F3 berarti cakupan atau penanganan error paket masih perlu diperbaiki; konsistensi baris tidak sama dengan persetujuan paket.

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
| `POST_missing_course_code` | Input missing pada course_code: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_null_course_code` | Input null pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_empty_course_code` | Input empty pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_whitespace_course_code` | Input whitespace pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_type_course_code` | Input type pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_object_course_code` | Input object pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_max_course_code` | Input max pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_unique_course_code` | Input unique pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_missing_credits` | Input missing pada credits: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_null_credits` | Input null pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_empty_credits` | Input empty pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_whitespace_credits` | Input whitespace pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_type_credits` | Input type pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_object_credits` | Input object pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_fraction_credits` | Input fraction pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_min_credits` | Input min pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_max_credits` | Input max pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_missing_quota` | Input missing pada quota: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_null_quota` | Input null pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_empty_quota` | Input empty pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_whitespace_quota` | Input whitespace pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_type_quota` | Input type pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_object_quota` | Input object pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_fraction_quota` | Input fraction pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_min_quota` | Input min pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_max_quota` | Input max pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_missing_course_code` | Input missing pada course_code: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_null_course_code` | Input null pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_empty_course_code` | Input empty pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_whitespace_course_code` | Input whitespace pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_type_course_code` | Input type pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_object_course_code` | Input object pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_max_course_code` | Input max pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_unique_course_code` | Input unique pada course_code: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_missing_credits` | Input missing pada credits: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_null_credits` | Input null pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_empty_credits` | Input empty pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_whitespace_credits` | Input whitespace pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_type_credits` | Input type pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_object_credits` | Input object pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_fraction_credits` | Input fraction pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_min_credits` | Input min pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_max_credits` | Input max pada credits: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_missing_quota` | Input missing pada quota: HTTP 422/errors field yang benar, database tetap. | internal_covered | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_null_quota` | Input null pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_empty_quota` | Input empty pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_whitespace_quota` | Input whitespace pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_type_quota` | Input type pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_object_quota` | Input object pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_fraction_quota` | Input fraction pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_min_quota` | Input min pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `PUT_max_quota` | Input max pada quota: HTTP 422/errors field yang benar, database tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | Tidak langsung; lihat batas paket |
| `POST_boundary_max_course_code` | Nilai valid boundary_max pada course_code: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_min_credits` | Nilai valid boundary_min pada credits: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_max_credits` | Nilai valid boundary_max pada credits: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_numeric_string_credits` | Nilai valid numeric_string pada credits: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_min_quota` | Nilai valid boundary_min pada quota: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_boundary_max_quota` | Nilai valid boundary_max pada quota: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `POST_numeric_string_quota` | Nilai valid numeric_string pada quota: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F2 |
| `PUT_boundary_max_course_code` | Nilai valid boundary_max pada course_code: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_min_credits` | Nilai valid boundary_min pada credits: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_max_credits` | Nilai valid boundary_max pada credits: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_numeric_string_credits` | Nilai valid numeric_string pada credits: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_min_quota` | Nilai valid boundary_min pada quota: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_boundary_max_quota` | Nilai valid boundary_max pada quota: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_numeric_string_quota` | Nilai valid numeric_string pada quota: status sukses, respons/DB sesuai, record lain tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |
| `PUT_own_course_code` | PUT mempertahankan nilai unik milik target sendiri: diterima, target benar dan pembanding tetap. | reference_only | Cocok untuk fixture ini;4 bukti positif lama | F1, F2 |

Untuk melihat payload persis, expected status/body/state, nama kontrol negatif dan path bukti, cari resource/case_id ini di case-audit.json. Form asli dan form kerja manusia tidak diubah.
