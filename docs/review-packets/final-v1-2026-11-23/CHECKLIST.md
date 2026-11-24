# Checklist peninjauan

Semua kotak sengaja kosong. Menyiapkan atau memverifikasi file tidak mencentang review manusia.

## Sebelum pemeriksaan

- [ ] Konfirmasikan pembuat manusia dan reviewer berbeda untuk setiap soal pada `forms/assignments.json`; tidak menyimpulkan penugasan dari nama tim di PRD.
- [ ] Catat bahwa bahan disiapkan AI dan keputusan belum disahkan.
- [ ] Periksa identitas paket, spesifikasi, suite, image serta hash ZIP/bahan.
- [ ] Baca PRD12.5–12.8, kontrak respons dan batas held-out/development.

## Untuk setiap358kasus

- [ ] `case_id` unik dalam soal dan rule benar-benar berasal dari kontrak.
- [ ] Fixture/payload, batas valid/invalid, tipe dan expected status/body/state masuk akal.
- [ ] Assertion PHP menilai perilaku yang dimaksud, termasuk identitas record dan keadaan database.
- [ ] Pemetaan internal/reference_only akurat; kasus acuan tambahan tetap dipertahankan.
- [ ] Dua kontrol positif sah dan mutasi/diff negatif menguji pelanggaran target; cocok dengan bukti aktual.
- [ ] Kegagalan target dibedakan dari error lingkungan/crash yang tidak menjelaskan assertion.
- [ ] Rationale ditulis setelah pemeriksaan; metadata manusia dan waktu benar.
- [ ] Perbedaan diperiksa silang dan diselesaikan atau dicatat unresolved, tanpa mengisi approved untuk kasus belum pasti.

## Review komponen16kasus, terpisah

- [ ] Pembuat label mengisi form miliknya; reviewer mengisi form sendiri sebelum membandingkan keputusan.
- [ ] Bukti acuan cocok dengan kode/spec dan keterbatasan suite development dipahami.
- [ ] Paparan prediksi/label draft terdahulu dicatat jujur; blind attestation hanya jika benar.
- [ ] Pelanggaran reference_only tetap masuk label kontrak penuh; kode duplikat ditandai.
- [ ] Keputusan belum pasti tetap uncertain/disputed; tidak mempromosikan label otomatis.
- [ ] Review sah mendahului prediksi komponen baru sebelum metrik reviewed-only dipakai.

## Sebelum freeze

- [ ] Semua form soal ditinjau silang; kasus ditolak/belum pasti sudah ditangani dengan versi baru bila perlu.
- [ ] P-06/K2, P-07, dan FR-20 memiliki keputusan manusia beserta bukti, tanpa persetujuan otomatis.
- [ ] Model/digest/options/seed/urutan/timeout/max3/aturan identik diputuskan dan diverifikasi aktual.
- [ ] Hash form yang selesai dihitung ulang pada manifest baru; form asli dan arsip lama tetap utuh.
- [ ] Gerbang protokol baru READY; seluruh20slot akan dijalankan dan dilaporkan tanpa memilih hasil terbaik.
