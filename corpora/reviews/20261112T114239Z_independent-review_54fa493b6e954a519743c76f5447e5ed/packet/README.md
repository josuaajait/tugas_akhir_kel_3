# Paket pemeriksaan label independen

Penugasan diberikan pengguna pada 12 November 2026. Mikhael Josua Roganda bertindak sebagai pembuat label dan Johannes Sitorus sebagai peninjau. Penugasan ini belum merupakan bukti pemeriksaan selesai.

Untuk setiap R001–R016, baca kode PHP, spesifikasi dan bukti acuan. Tentukan correct/problematic/uncertain, alasan dan lokasi pelanggaran. Cantumkan coverage internal_covered/reference_only berdasarkan matriks cakupan versi yang dinilai. Bukti acuan merupakan observasi development dengan suite lama; tinjau kelemahan suite pada audit products dan jangan menganggap semua test lulus sebagai bukti lengkap kebenaran.

Mikhael mengisi author-decisions.json. Johannes terlebih dahulu mengisi reviewer-decisions.json secara independen. Isi waktu pemeriksaan yang sebenarnya dan catat paparan prediksi terdahulu pada previous_prediction_exposure. Setelah keduanya selesai, bandingkan keputusan dan isi decisions.json beserta alasan penyelesaian perbedaan. Keputusan belum pasti tetap uncertain/disputed. Nilai label, tanggal dan attestasi tidak boleh dibuat otomatis.

blinded_to_prediction hanya boleh true bila sesuai keadaan sebenarnya. Paket baru tidak menghapus paparan prediksi sebelumnya. Bila pernah melihat prediksi per kasus, pertahankan false dan diskusikan peninjau/kasus baru untuk memenuhi protokol reviewed-only. Pengetahuan atas draft AI juga perlu dicatat pada notes.

Kirim kembali formulir yang telah diperiksa melalui folder ini. Codex kemudian memvalidasi bukti, memindahkan keputusan ke salinan korpus baru dan menjalankan prediksi baru sesudah review. Paket ini belum mengesahkan label. Formulir kosong tidak disertai usulan label AI, prompt/feedback model atau prediksi Critic. File reference berisi hasil evaluator acuan yang memang merupakan bahan review.

Bagikan hanya direktori packet atau ZIP-nya kepada peninjau. Peta identitas kasus dan catatan provenance berada di direktori induk untuk pengelola eksperimen.
