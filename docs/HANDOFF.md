# Serah terima Critic Agent — 5 November 2026

Dokumen awal untuk teman yang melanjutkan proyek. Lokasi kerja Mikhael: `C:\Perkuliahan\TA`; clone baru boleh berada di folder lain. Seluruh perintah dijalankan dari root clone yang memuat `critic_agent/`, `harness/`, dan `pyproject.toml`.

## Posisi sekarang

MVP CLI sudah menghasilkan kode Qwen, memeriksa controller Laravel di Docker, memberi feedback, merevisi sampai batas berhenti, mengevaluasi awal/akhir dengan suite pengembangan terpisah, dan menghasilkan laporan deteksi komponen sementara. Implementasi penelitian akhir belum selesai. Tidak ada persentase progres TA yang dihitung dari jumlah fitur.

| Bagian | Status terverifikasi |
|---|---|
| Validasi JSON, prompt, Ollama dan arsip | Tersedia; generasi Qwen lokal sudah dijalankan |
| Analisis statis | PHP lint/tokenizer, namespace/class/method/signature; tanpa eksekusi kandidat di host |
| Harness internal/readiness | Products14/21, books12/27, inventory16/46; readiness live lulus |
| Loop revisi | Max 3; all_checks_passed, identical_code, batas revisi dan ERROR diarsipkan |
| Acuan pengembangan terpisah | Products33, books35, inventory57; evaluasi awal/akhir live selesai |
| Evaluasi komponen development | COMPLETE16 kasus,0 error prediksi; laporan provisional tersimpan |
| Ground truth | 16 anotasi berbantuan AI atas nama Mikhael Josua Roganda; semua masih draf |
| Pilot suhu/seed dan biaya | Belum dijalankan; belum ada CLI pilot khusus |
| A/B feedback spesifik versus generik | Belum diimplementasikan/dijalankan |
| Agregasi lintas run, held-out, pembekuan akhir | Belum selesai; held-out saat ini0 kasus |
| Evaluasi akhir dan laporan TA akhir | Belum selesai |

Versi aplikasi `0.5.0`, protokol komponen `1.0`. Jangan menaikkan versi aplikasi atau mengubah suite/template/runtime saat mengerjakan bagian tidak terkait: versi/sumber ikut fingerprint image. Perubahan terkoordinasi memerlukan hash dan build baru; hasil lama tetap disimpan.

## Hasil yang sudah ada

### Loop dan evaluasi awal–akhir

| Resource | Internal awal→akhir | Revisi/status | Acuan awal→akhir | Uplift acuan | Repair |
|---|---|---|---|---|---|
| Products | 13/14→14/14 | 1, LOLOS | 31/33→33/33 | +6.060606 poin | 1/1 |
| Books | 12/12→12/12 | 0, LOLOS sejak awal | 35/35→35/35 | 0 poin | 0/0, N/A |
| Inventory | 11/16→12/16 | 2, BELUM LOLOS/identical_code | 51/57→53/57 | +3.508772 poin | 0/1 |

Inventory memperbaiki respons destroy, tetapi rule required pada empat field update tetap hilang. Percobaan2 identik dengan1. Pertahankan hasil ini; jangan memperbaiki kandidat arsip untuk memaksakan LOLOS. Dua testcase acuan tambahan yang lulus akibat satu perbaikan destroy bukan dua bug independen. Books yang benar sejak awal tidak menunjukkan efek repair. Tiga loop tersebut adalah data formatif, bukan estimasi efektivitas populasi.

### Deteksi komponen sementara

Run terakhir: `component-runs/20261105T005526Z_component_4a131234b1c14b5a95421e211dcdf739`.

| Korpus | Mentah/layak dihitung | TP/FP/TN/FN | Precision | Recall | FPR |
|---|---|---|---|---|---|
| Sintetis | 10/10 | 6/0/2/2 | 6/6=100% | 6/8=75% | 0/2=0% |
| Qwen formatif | 6/5 | 3/0/2/0 | 3/3=100% | 3/3=100% | 0/2=0% |
| Qwen held-out | 0/0 | 0/0/0/0 | N/A | N/A | N/A |

Satu duplikat inventory dikeluarkan dari metrik, tetap disimpan dalam arsip. Dua FN sintetis adalah penghilangan max:80 pada title dan min:1 pada pages. Keduanya reference_only: test internal memang belum memeriksa batas itu. Jangan membuang FN atau mengubah test untuk menaikkan angka dari paket sama. Tidak ada matriks gabungan antarasal. FPR0/2 dan hasil Qwen3/3 memiliki penyebut kecil. Semua hasil memakai label draf berbantuan AI, bukan label manusia independen.

Salinan laporan yang dapat ikut Git: [laporan JSON](evidence/component-provisional-2026-11-05.json); provenance/hash: [catatan bukti](evidence/README.md). Arsip raw lokal tetap diperlukan untuk audit lengkap.

## Mulai dari clone baru

Prasyarat: Python>=3.11, PHP CLI 8.3 untuk lint/tokenizer, Docker dengan Linux containers (Windows: Docker Desktop/WSL2). Ollama hanya diperlukan bila menghasilkan/merevisi kode. Baseline teramati: Python 3.13.7, PHP 8.3.30, Laravel 12.70.2 dan PHPUnit 11.5.57; dua paket terakhir dikunci di harness/laravel/composer.lock. Python proyek memakai standard library; jalankan dari root clone.

```bat
python -m critic_agent --help
python -m critic_agent doctor
python -m critic_agent validate examples/books.json
python -m unittest discover -s tests -v
docker version
```

Riwayat verifikasi kode:134 tes Python lulus tanpa skip pada 4 November 2026. Jalankan ulang di mesin penerima dan catat hasil aktual; ini bukan klaim sudah diuji di mesin baru. doctor dapat melaporkan Ollama/model belum siap walaupun evaluasi tanpa model dapat dilanjutkan. docker version harus menampilkan Client dan Server sebelum harness dijalankan.

### Bangun image pada mesin penerima

Image Docker, cache dependensi dan model Ollama tidak dikirim lewat Git. Build pertama memerlukan jaringan untuk base image/Composer. Jalankan satu per satu dan lanjutkan setelah build/readiness berhasil:

```bat
python -m critic_agent harness-build
python -m critic_agent harness-check
python -m critic_agent resource-build examples/books.json --timeout 600
python -m critic_agent resource-check examples/books.json
python -m critic_agent resource-build examples/inventory_items.json --timeout 600
python -m critic_agent resource-check examples/inventory_items.json
python -m critic_agent evaluation-build
python -m critic_agent resource-evaluation-build examples/books.json --timeout 600
python -m critic_agent resource-evaluation-build examples/inventory_items.json --timeout 600
```

Target readiness:products 21/21, books 27/27, inventory 46/46. Evaluator memeriksa readiness sebelum menilai kandidat. ID image hasil build baru boleh berbeda dari mesin Mikhael; jangan mengganti ID arsip lama. Jangan memakai image evaluator sebagai harness internal.

### Lanjutkan komponen tanpa menghasilkan Qwen lagi

Korpus16 label draf beserta kode/spec/bukti:

`corpora/annotations/20261104T085829Z_mikhael-ai-assisted_e7a9c4248c344f21aa2b3df91fca627c/corpus.json`

Pastikan korpus itu ikut commit. Jalankan di **PowerShell** dari root clone; script mengambil run_directory otomatis:

```powershell
$componentResult = python -m critic_agent component-run "corpora/annotations/20261104T085829Z_mikhael-ai-assisted_e7a9c4248c344f21aa2b3df91fca627c/corpus.json" --timeout 120 | ConvertFrom-Json
$componentResult | ConvertTo-Json -Depth 4
if ($componentResult.status -eq 'COMPLETE') {
    python -m critic_agent component-report $componentResult.run_directory --provisional
}
```

Target COMPLETE16 kasus/0 prediction_errors. Setiap percobaan membuat folder baru. Jika ERROR, baca readiness/dynamic, pulihkan penyebab, lalu rerun ke folder baru; hasil gagal tidak ditimpa. Laporan --provisional memakai draf. Default reviewed-only mengecualikan draf; belum ada label yang disahkan dua manusia.

component-corpus-init tanpa --synthetic-only mengimpor tiga loop lokal terpilih. Clone tanpa runs/ tidak dapat membentuk ulang korpus Qwen dengan perintah itu; gunakan korpus terkurasi yang sudah di-commit. Untuk korpus sintetis baru saja, gunakan component-corpus-init --synthetic-only.

### Bila akan menjalankan model

```bat
ollama pull qwen2.5:7b-instruct
python -m critic_agent doctor
python -m critic_agent run-resource examples/books.json --seed 42 --temperature 0.2 --timeout 300
```

Model lokal di http://127.0.0.1:11434; opsi development seed42/temperature0.2, num_ctx8192/num_predict4096. Suhu/seed final belum ditetapkan. Digest model, kuantisasi aktual, versi Ollama dan perangkat perlu dicatat sebelum eksperimen. Tidak perlu membuat ulang generasi lama untuk membaca laporan.


## Apa yang ikut push dan apa yang diserahkan terpisah

Git mengabaikan runs/, evaluations/, builds/, component-runs/, component-evidence/, work/, vendor dan .env. Setelah clone, path arsip lokal dalam dokumen ini dapat belum ada. corpora/, kode, tests, docs dan contoh spesifikasi dapat ikut commit; pastikan tidak tertinggal sebagai untracked. Modul komponen baru dan perubahan CLI harus ikut commit bersama dokumen bila belum pernah di-commit.

Untuk meneruskan analisis terhadap eksperimen yang sama, Mikhael membagikan arsip lokal berikut secara terpisah (misalnya ZIP); penerima menempatkannya di path relatif sama di root clone:

| Artefak | Path relatif lokal |
|---|---|
| Loop products | `runs/20261104T031502Z_loop_713c3f8803f441929ae6ed8f38077232` |
| Generasi awal products, untuk impor ulang asal Qwen | `runs/20261104T025540Z_4fad073a00e0484abf342797d9d9f6a6` |
| Loop books | `runs/20261104T044458Z_loop_52c1faef1c1644f3ac228b14eebdebcf` |
| Loop inventory | `runs/20261104T044936Z_loop_4c8045891ecc4a74a31e0117ed15932a` |
| Acuan products | `evaluations/20261104T034743Z_evaluation_5b534ddeee604e72b59f70dec1be3339` |
| Acuan books | `evaluations/20261104T070227Z_evaluation_fcb7a7d760c8409a86d42b0181a75a4a` |
| Acuan inventory | `evaluations/20261104T070315Z_evaluation_a4530545547b4b7dba2dc39eed6fc03c` |
| Bukti label komponen | `component-evidence/20261104T082952Z_reference-evidence_26a23f11d3ab49929f39605cde0bf690` |
| Run komponen berhasil | `component-runs/20261105T005526Z_component_4a131234b1c14b5a95421e211dcdf739` |
| Run gagal lingkungan yang tetap dicatat | `component-runs/20261105T005039Z_component_704c26e46dcd41a08e2656daee8a6cac` |

Sertakan raw harness logs/JUnit/readiness yang dirujuk run/evaluasi untuk audit penuh; ringkasan docs tidak menggantikannya. Beberapa provenance menyimpan path absolut mesin asal. Jangan mengedit manifest/hash massal untuk memindahkannya; pertahankan sumber dan gunakan korpus dengan aset relatif atau jalankan eksperimen development baru.

File component-evidence/.../review/decisions.json sekarang sudah diisi usulan AI atas permintaan pengguna. Formulir kosong sebelumnya ada di review-backups/. Folder review terisi itu bukan paket label-kosong lagi: untuk review independen sediakan paket bersih berisi kode/spec/bukti dan formulir kosong, tanpa usulan label/prediksi. Isian decisions tidak otomatis diimpor ke corpus.json; korpus anotasi di atas sudah memiliki draf yang dipakai run terakhir.

## Pekerjaan berikutnya, berurutan

1. **Pulihkan lingkungan dan bahan serah terima.** Jalankan pemeriksaan lokal, bangun image, verifikasi korpus dan reproduksi laporan provisional. Penerima mencatat hasil sendiri; clone tidak membawa image atau raw run.
2. **Implementasikan dan jalankan pilot suhu/seed/biaya.** PRD12.7 mengusulkan2–3spesifikasi development × 3 seed × suhu0/0.2/0.5; belum merupakan hasil. Catat validitas ekstraksi, hash awal unik/duplikat, kandidat awal gagal, pola temuan, identical_code serta durasi/token. Tetapkan daftar seed/timeout. Belum ada CLI pilot/aggregator; perlu manifest eksekusi dan ringkasan. Jangan mengarang nama perintah yang belum ada.
3. **Review nyata dan keputusan lingkup.** Tetapkan pembuat/peninjau berbeda untuk label dan assertion; tuntaskan P-06/P-07/ambang K2 bersama pembimbing. Anotasi saat ini prepared_by=OpenAI Codex, human_author_review_attested=false; nama Mikhael adalah atribusi yang diminta, bukan bukti pemeriksaan manual. Reviewer/reviewed_at kosong. Status reviewed dicatat setelah kegiatan nyata, sebelum prediction run baru.
4. **Putuskan A/B sebelum pembekuan.** Cabang feedback generik belum ada. Pastikan cukup kandidat awal gagal, anggaran revisi/seed adil dan analisis penghentian identik dicatat. Jika ablasi dipotong, tulis keterbatasan atribusi sesuai PRD12.2/12.8; jangan mengklaim uplift disebabkan khusus rincian feedback.
5. **Audit dan pisahkan paket akhir.** Tinjau assertion collection legacy products/internal (audit terbuka), cakupan internal/reference_only, dan contoh valid/invalid. Siapkan held-out yang belum dipakai development. Bekukan kode/spec/test/image/model/prompt/seed/stop rule/label/protokol sebelum evaluasi akhir. Perluasan cakupan adalah paket/version baru.
6. **Eksekusi dan pelaporan akhir.** Manifest lengkap, agregasi deskriptif per spesifikasi/kondisi/korpus dengan pembilang/penyebut, retry/ERROR dan duplikat. Simpan semua keluaran; tidak memilih kandidat terbaik atau menganggap pengulangan dari spesifikasi sama independen.

## Kendala yang pernah ditemukan

- Run pertama5November gagal14 prediksi karena pipe DockerDesktopLinuxEngine tidak ditemukan. Setelah Docker dibuka, run baru COMPLETE. Ini berbeda dari akses pipe ditolak sandbox Codex saat engine berjalan. Gunakan terminal pengguna yang menampilkan Docker Server; tidak perlu mengubah keamanan global.
- docker desktop start pernah gagal membaca registry walaupun aplikasi terpasang per-user. Membuka aplikasinya berhasil dan menunjukkan Engine running. Jangan menyimpulkan Docker belum terpasang dari satu lookup C:\Program Files yang gagal.
- ISI_DENGAN_RUN_DIRECTORY adalah penanda contoh, bukan folder nyata. Gunakan path output atau script PowerShell di atas.
- Build resource pernah timeout pada tag10detik;0.4.1 sudah memakai --timeout pada persiapan/build/cleanup. Gunakan --timeout600 pada build bila perlu; jangan prune image lain.
- InvalidDefaultArgInFrom pernah muncul pada evaluator tetapi build berhasil dengan base eksplisit. Jangan mengubah suite terverifikasi untuk merapikan warning tanpa mencatat hash/build baru.

## Peta berkas dan aturan kerja

| Lokasi | Peran |
|---|---|
| `critic_agent/spec.py`, `prompts.py`, `ollama.py`, `generation.py` | Kontrak, prompt, transport model, ekstraksi/arsip |
| `static.py`, `feedback.py`, `orchestrator.py` | Analisis statis, temuan, loop revisi |
| `sandbox.py`, `process.py`, `harness/` | Docker runner, pembatasan output dan harness products |
| `resources.py`, `resource_templates/` | Generator/harness internal resource |
| `reference.py`, `resource_reference.py`, `evaluation/` | Evaluator terpisah, suite dan metrik pasangan |
| `component_corpus.py`, `component_evaluation.py`, `component_report.py` | Korpus, bukti, prediksi komponen dan metrik per kode |
| `tests/` | Tes implementasi; fixture unit bukan data penelitian |
| `corpora/` | Paket development/anotasi terkurasi yang bisa ikut Git |

Path modul berada di critic_agent/ kecuali disebut sebagai direktori root. Kandidat hanya dieksekusi di Docker; jangan memasang seluruh repo atau memakai host PHP sebagai fallback. Static pass bukan LOLOS. Test acuan/hasilnya tetap di luar prompt/feedback. Berhenti max3/byte-identical dipertahankan. Simpan kegagalan dan history asli.

Baca [PRD](../PRD_Critic_Agent_v1.3.md), [progres historis](progress.md), [batas MVP](spec-mvp.md), [harness resource](resource-harness.md) dan [evaluasi komponen](component-evaluation.md). Pembaruan dokumentasi ini tidak melakukan commit/push.
