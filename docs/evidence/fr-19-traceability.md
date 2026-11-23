# Matriks keterlacakan development untuk FR-19

Matriks ini memetakan test development yang tersedia. Semua baris berstatus **belum ditinjau**. Paket final memerlukan matriks terpisah yang merujuk spesifikasi, fixture, image dan suite yang akan dibekukan. Kode uji Edge/Readiness hanya dipakai pada controller tepercaya.

| Alias | `spec_id` | Versi |
|---|---|---|
| P | `products_basic` | 1.0 |
| B | `books_basic` | 1.0 |
| I | `inventory_items_basic` | 1.0 |

ID test di bawah adalah nama metode PHPUnit tanpa awalan `test_`. Untuk provider, label dataset menyatakan vektor yang dipilih. P memakai ProductsContractTest internal v2 dan ProductsReferenceTest v1. B/I memakai ResourceContractTest dan ResourceReferenceTest bersama profil masing-masing.

| Spec | Rule ID | Kondisi / fixture | Internal test ID | Reference test ID | Cakupan dan assertion |
|---|---|---|---|---|---|
| P | crud.index | Dua record tersimpan | index_returns_records_without_changing_data | list_exposes_persisted_values_without_mutation | internal_covered. 200, koleksi dan DB tetap. Acuan v1 memakai fragmen dan masih perlu perbaikan pengikatan record. |
| B/I | crud.index | Dua record tersimpan | index_returns_records_without_mutation | collection_contains_both_persisted_records_without_changes | internal_covered. 200, nilai record, DB tetap. |
| P | crud.store | Payload valid dan record lain | store_persists_one_record_and_preserves_other_records | create_returns_and_persists_new_values | internal_covered. 201, nilai tersimpan, satu record baru, record lain tetap. |
| B/I | crud.store | Payload valid dan record lain | store_persists_payload_and_preserves_other | create_exposes_inserted_values_and_keeps_existing_record | internal_covered. 201, nilai tersimpan dan record lain tetap. |
| P | crud.show | Target tersedia | show_returns_target_without_changing_data | read_selects_requested_record_without_mutation | internal_covered. 200, nilai target, DB tetap. |
| B/I | crud.show | Target tersedia | show_returns_requested_record_without_mutation | read_uses_requested_identifier_and_does_not_write | internal_covered. 200, nilai target, DB tetap. |
| P | crud.update | PUT payload valid | update_changes_only_target | update_replaces_target_and_preserves_neighbour | internal_covered. 200, nilai baru pada target, record lain tetap. |
| B/I | crud.update | PUT payload valid | update_changes_only_target | replacement_returns_and_persists_all_values_only_on_target | internal_covered. 200, nilai baru pada target, record lain tetap. |
| P | crud.destroy | Target tersedia | destroy_removes_only_target_and_returns_empty_body | delete_is_empty_204_and_preserves_neighbour | internal_covered. 204 kosong, target dihapus dan record lain tetap. |
| B/I | crud.destroy | Target tersedia | destroy_removes_only_target_and_returns_empty_204 | deletion_is_empty_204_and_removes_only_requested_record | internal_covered. 204 kosong, target dihapus dan record lain tetap. |
| P | crud.missing_id | GET/PUT/DELETE ID tidak dikenal | missing_id_returns_json_404_without_changing_data | missing_identifier_is_json_404_without_mutation | internal_covered. 404 JSON, DB tetap. |
| B/I | crud.missing_id | GET/PUT/DELETE ID tidak dikenal | missing_id_returns_json_404_without_mutation | unknown_identifier_is_json_404_and_keeps_all_rows | internal_covered. 404 JSON, DB tetap. |
| P | validation.required.omitted | POST/PUT, tiap field name/price/sku dihilangkan | required_field_rejection_preserves_data, dataset store/update + field | invalid_input_reports_field_and_preserves_database, dataset store/update + missing_field | internal_covered. 422 menyebut field dan DB tetap. |
| B/I | validation.required.omitted | POST/PUT, tiap field dari spec dihilangkan | required_field_rejection_preserves_data, dataset store/update + field | invalid_payload_reports_named_field_without_database_changes, dataset POST/PUT + missing_field | internal_covered. 422 menyebut field dan DB tetap. |
| P | validation.invalid_payload | POST/PUT, dataset empty_name/empty_sku, array_name, invalid_integer, long_name, negative_price, duplicate_sku | — | invalid_input_reports_field_and_preserves_database | reference_only untuk vektor yang disebut. 422 menyebut field dan DB tetap. Tipe salah khusus sku belum memiliki vektor acuan tersendiri. |
| B | validation.invalid_payload | POST/PUT, blank_title, null_pages, title_array, pages_text, long_title, pages_below_min, pages_above_max | — | invalid_payload_reports_named_field_without_database_changes | reference_only. 422 menyebut field dan DB tetap. |
| I | validation.invalid_payload | POST/PUT, label/warehouse blank atau array, stok teks atau di luar batas, reorder pecahan atau di luar batas, panjang label/warehouse dan warehouse duplikat | — | invalid_payload_reports_named_field_without_database_changes, vektor profil inventory | reference_only. 422 menyebut field dan DB tetap. |
| P | validation.valid_boundary | POST max name dan price 0 | — | valid_boundary_is_persisted | reference_only. 201 dan nilai batas tersimpan. |
| B/I | validation.valid_boundary | POST/PUT pada dataset batas dalam profil valid | — | boundary_payload_is_accepted_and_persisted | reference_only. Status valid dan data pada batas tersimpan. |
| P/I | validation.own_unique | PUT mempertahankan nilai unique milik target | — | P: update_retains_own_unique_sku. I: update_accepts_own_unique_values_and_preserves_neighbour. | reference_only. Update diterima dan record lain tetap. |
| P/B/I | crud.empty_and_sequence | Koleksi kosong dan rangkaian CRUD | — | P: empty_collection, crud_sequence_reads_back_changes. B/I: empty_collection_is_json_and_preserves_empty_database, sequential_crud_reads_back_persisted_replacement_and_deletion. | reference_only. Koleksi kosong valid, perubahan dapat dibaca kembali dan penghapusan teramati. |

Untuk paket final, pecah baris yang mencakup beberapa field/vektor menjadi satu baris per rule dan dataset. Catat sumber fixture, hasil positif dari controller acuan, hasil negatif untuk masing-masing pelanggaran, serta nama pembuat dan peninjau yang benar-benar memeriksa artefak.
