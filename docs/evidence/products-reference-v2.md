# Evaluator acuan products v2

Versi v2 memeriksa objek respons, array `data`, dan nilai name, price, serta SKU pada setiap ID integer unik. Fixture memakai nama, harga, dan SKU berbeda. Pemeriksaan tidak bergantung pada urutan respons. Field tambahan diperbolehkan dan snapshot database harus tetap sama. Koleksi kosong juga harus berbentuk array. Jumlah kasus tetap 33.

| Build Docker | Controller tepercaya | Fixture SKU tertukar |
|---|---:|---:|
| v1 | READY 33/33 | PASSED_REFERENCE 33/33 |
| v2 | READY 33/33 | FAILED_REFERENCE 32/33 |

Fixture buatan menukar SKU hanya pada respons koleksi dua record. Image v2 gagal pada `test_list_exposes_persisted_values_without_mutation`. Arsip readiness, pemeriksaan fixture, dan log build tersedia di `evaluations/products-reference-v2-validation/`.

Evaluasi ulang kandidat awal dan akhir dari arsip products historis menghasilkan **31/33 → 33/33** pada v2, tanpa pemanggilan model. Arsip baru berada di `evaluations/products-reference-v2-validation/replay/20261119T114447Z_evaluation_82749a94d57b49729532b78edb37c959/`.

Fingerprint v2 adalah `b3238b844445afd7035fda8d8e59d715cb0edbe97efb4b66069652abcaf65509`. Image yang diperiksa adalah `sha256:9f58bcb33707c5ad706c2902d751ee0c7272affc20d4ed241c4311ce68d5d1a3`. Fingerprint default v1 tetap `d59c4d7c5a1311a5020b2f15d9cec203b64a3e83e57ea287caaab4731a6f0778`; arsip pilot dan komponen lama tetap merujuk suite yang dipakai pada saat eksekusi.

```powershell
python -m critic_agent evaluation-build --suite v2
python -m critic_agent reference-check-products --suite v2
python -m critic_agent evaluate-products runs/20261104T031502Z_loop_713c3f8803f441929ae6ed8f38077232 --suite v2
```

Untuk pasangan A/B products, pilih evaluator ini dengan `run-ab --reference-suite v2`. Build default v2 memakai tag `critic-laravel-evaluation:products-v2`. File sumber dan hasil validasi ini merupakan artefak development. Paket held-out dan pemetaan suite final masih memerlukan pemisahan, validasi dan review sesuai PRD.
