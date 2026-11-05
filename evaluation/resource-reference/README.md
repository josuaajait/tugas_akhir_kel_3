# Acuan pengembangan books dan inventory

Versi0.5.0 menambahkan evaluator awal/akhir untuk dua kontrak yang sudah dipakai. Test dan data acuan berada dalam paket/image tersendiri. Tidak ada panggilan Qwen, pengiriman hasil ke feedback revisi, atau perubahan arsip loop.

Paket ini ditulis setelah keluaran pengembangan dilihat. Ia belum menjadi evaluasi akhir yang dibekukan atau dibutakan. Sebelum sumatif, tinjau assertion serta label, validasi implementasi benar dan mutasi target, siapkan kasus akhir terpisah, lalu bekukan protokol/image/suite sesuai PRD.

## Jalankan dari terminal atau Codex CLI

Image internal books/inventory yang sudah teruji dapat dipakai sebagai base; tidak perlu membangun ulang image internal. Fingerprint internal dan evaluator products tetap cocok dengan arsip yang telah diverifikasi.

```bat
python -m critic_agent resource-evaluation-build examples/books.json --timeout 600
python -m critic_agent evaluate-resource runs/20261104T044458Z_loop_52c1faef1c1644f3ac228b14eebdebcf

python -m critic_agent resource-evaluation-build examples/inventory_items.json --timeout 600
python -m critic_agent evaluate-resource runs/20261104T044936Z_loop_4c8045891ecc4a74a31e0117ed15932a
```

Jalankan evaluasi masing-masing hanya setelah build-nya BUILT. Default base adalah critic-resource-RESOURCE:dev dan target critic-resource-RESOURCE-evaluation:dev. Untuk products, tetap gunakan evaluation-build/evaluate-products yang lama. Sesi desktop Codex masih tidak dapat mengakses Docker; gunakan terminal pengguna atau CLI dengan persetujuan eskalasi sebagaimana sebelumnya. Tidak ada perubahan keamanan global.

Evaluator membaca dan memverifikasi hash kandidat awal/akhir dari arsip yang sudah ada. Books yang langsung lolos tetap dievaluasi dua kali dari container/database baru, meskipun kedua file identik. Inventory yang berhenti identical_code tetap masuk evaluasi sebagai pasangan BELUM LOLOS. Jangan mengganti kandidat atau memilih ulang run agar hasil menjadi lebih baik.

## Kasus yang direncanakan

| Kelompok | Books | Inventory |
| --- | ---: | ---: |
| Empty/list/create/read/replace/delete | 6 | 6 |
| Missing ID: GET/PUT/DELETE | 3 | 3 |
| Payload invalid: POST dan PUT | 18 | 34 |
| Batas valid: POST dan PUT | 6 | 12 |
| Update mempertahankan nilai sendiri | 1 | 1 |
| Rangkaian CRUD | 1 | 1 |
| Total | 35 | 57 |

Profil JSON memuat payload lengkap yang dipilih secara terpisah: books mencakup required, string, integer, max80, min1/max5000; inventory mencakup keempat field wajib, tipe, batas label/warehouse/stock/reorder dan duplicate warehouse_code. Nilai fixture tidak diambil dari generator internal. Kode assertion tidak mengimpor kelas atau fixture internal/readiness. Keduanya memakai model/route/migration yang sama sebagai infrastruktur aplikasi, karena kontrak yang dinilai sama.

Koleksi dicocokkan per integer ID dan seluruh field, menerima urutan valid berbeda serta menolak ID tertukar/duplikat dan field hilang. Snapshot query DB memeriksa perubahan tersimpan dan isolasi record. Request memakai Accept JSON. Satu cacat dapat menggagalkan beberapa test, misalnya destroy juga memengaruhi rangkaian CRUD; jumlah test gagal bukan jumlah bug independen.

Hanya dua kontrak profil ini yang diterima. Perubahan field/aturan/spec yang tidak cocok ditolak; tambah/tinjau profil baru terlebih dahulu. Jangan mengubah profil acuan final menggunakan hasil akhir atau menyamakan suite acuan dengan test readiness internal.

## Reproduksibilitas dan status

Build membuat konteks baru dan suite_manifest.json/build_result.json di builds/resource-evaluation. Builder memeriksa entrypoint dan label kontrak base, menolak evaluator/base resource lain, membuat tag UUID sementara dari ID base yang diperiksa, lalu membersihkan tag itu saja. Seluruh operasi Docker memakai --timeout per operasi. Metadata mencatat tahap gagal dan cleanup tanpa menutupi penyebab awal. Nama image dinormalisasi untuk melindungi base/internal/products dari penimpaan melalui alias.

Runner memeriksa hash suite dan label kontrak resource pada image ID yang digunakan. Kedua kandidat memakai image/suite yang identik dengan keadaan awal DB yang sama dalam container terpisah. Entrypoint evaluator hanya menerima evaluation-reference/evaluation-candidate, sehingga resource-* yang digunakan loop ditolak. Container tetap nonroot, network none, read-only root, tmpfs, satu input controller read-only dan batas CPU/memori/PID/output. Laporan masih observasi dari proses PHPUnit yang dapat dipengaruhi kandidat, bukan bukti tahan manipulasi adversarial.

Laporan baru di evaluations/.../evaluation_result.json memuat raw counts35/57, pass rate awal/akhir, uplift dalam poin persentase, repair/regression dengan pembilang/penyebut. Penyebut0 ditulis null/N/A. EVALUATED berarti pasangan selesai dinilai, termasuk bila kode gagal pada test; tidak berarti semua test lulus. Ini indikator satu pasangan; agregasi lintas spesifikasi/seed belum tersedia.

Source yang berubah/hilang meskipun diklaim tersedia ditolak. Kode yang dinyatakan tidak berhasil diekstrak dan syntax invalid yang dibuktikan lint Docker mendapat0 dari jumlah test yang direncanakan dengan executed=false; tidak ada assertion fiktif. Kegagalan kesiapan, suite parsial, image berubah, error infrastruktur atau timeout/crash tanpa sebab kandidat yang terbukti menghasilkan ERROR dan metrik pasangan null. Arsip sumber tidak ditimpa.

## Verifikasi implementasi

Python menguji ukuran suite, metadata, penolakan kontrak/image salah, metrik35/57, input identik, source tampering, output tidak tersedia/sintaks, error/parsial, timeout/cleanup, dan CLI tanpa panggilan model. PHP lint, enumerasi provider dan probe assertion murni dilakukan pada source tepercaya, tanpa menjalankan controller kandidat di host. Keduanya tetap memerlukan build dan eksekusi Docker di CLI pengguna sebelum hasil fungsional dapat dilaporkan.

Pembaruan4 November2026: pengguna sudah memverifikasi kedua build dan evaluasi Docker0.5.0. Books: readiness35/35, awal35/35 dan akhir35/35 (uplift0, repair N/A). Inventory: readiness57/57, awal51/57 dan akhir53/57 (uplift3.508772 poin, repair0/1). Empat kegagalan akhir adalah PUT tanpa masing-masing field wajib. Ini hasil tiga paket pengembangan bersama products, belum evaluasi sumatif. Warning InvalidDefaultArgInFrom tidak menggagalkan build; CLI telah mengisi RESOURCE_IMAGE dengan referensi base yang diperiksa. Detail provenance di docs/progress.md.

Untuk paket products dan template internal lama, audit lanjutan assertion koleksi tetap diperlukan sebelum pembekuan akhir; paket baru sudah memakai pencocokan per-record. Bukti products yang sudah ada tetap merujuk versi/hash suite lamanya.
