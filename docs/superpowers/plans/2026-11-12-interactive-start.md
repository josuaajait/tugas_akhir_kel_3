# Interactive Start Implementation Plan

**Goal** Menanyakan spesifikasi CRUD lalu menjalankan self-debugging dengan satu command.

**Architecture** Modul interactive.py mengumpulkan spec valid dan menjalankan persiapan serta run_resource. cli.py mendaftarkan start dan menggunakan ringkasan loop yang sama. Reuse validator, builder, Docker runner dan loop tanpa mengubah fingerprint suite.

**Tech Stack** Python stdlib, PHP lint, Docker, Ollama lokal.

**Spec** docs/superpowers/specs/2026-11-12-interactive-start-design.md, disetujui pengguna melalui percakapan.

## Constraints

- Kandidat dieksekusi hanya di Docker. Max3 dan byte-identical stopping tetap.
- Arsip sesi baru, output mentah dan kegagalan dipertahankan.
- Versi aplikasi/suite/resource templates tidak berubah.
- PRD, README dan handoff diperbarui sesuai perilaku implementasi.

## Review focus

Input invalid/duplikat/reserved, EOF/batal tanpa efek samping, build/readiness gagal sebelum model, sesi UUID dan image terpisah, serta path hasil dan exit status akhir.

## Tasks

- [x] Tulis dan jalankan tes gagal untuk wizard, pembatalan, orchestrasi kegagalan dan command start.
- [x] Implementasikan collect_spec dan start_interactive dengan arsip sesi dan builder/runner/loop yang ada.
- [x] Integrasikan start dan ringkasan hasil CLI, jalankan regresi terarah.
- [x] Update FR-01/02/05/14, skenario dan alur interaktif PRD, README dan handoff.
- [x] Jalankan seluruh unittest, doctor, smoke terminal, verifikasi fingerprint dan tinjau diff.

## Execution notes

Baseline sesi sebelumnya 148 tests OK di luar sandbox. Perubahan audit docs/progress.md dan docs/products-internal-assertion-audit.md sudah ada sebelum fitur ini. Implementasi dilakukan pada workspace pengguna saat ini sesuai permintaan melanjutkan pekerjaan. Tidak ada commit/push otomatis.

Verifikasi akhir 163 tests OK, termasuk 15 tes interaktif. Tes awal gagal karena command/modul belum tersedia, lalu lulus setelah implementasi. Reviewer menemukan pembatalan saat panggilan model yang meninggalkan loop RUNNING. Regresi membuktikan kegagalan tersebut, perbaikan menutup arsip sesi miliknya menjadi ERROR/user_cancelled dan mempertahankan session CANCELLED/130. Recheck reviewer tidak menemukan isu penting lain.

Smoke terminal dengan input books yang dikonfirmasi menghasilkan sesi tersimpan dan ERROR/prerequisites akibat endpoint Docker tidak tersedia, termasuk di luar sandbox. Ollama/Qwen terdeteksi di luar sandbox. Pengujian live penuh Docker/Qwen untuk command baru masih pending. Sumber versi/suite/runtime/generator/loop/component engine tetap identik menurut git diff. git diff --check bersih. Perubahan README dan panduan klien yang sudah ada dipertahankan.
