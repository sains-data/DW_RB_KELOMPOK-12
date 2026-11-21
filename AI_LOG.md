# AI_LOG — Kelompok 12

Satu baris per pemakaian AI yang bermakna (ChatGPT, Claude, Copilot, Bravais, dan sejenisnya).
Ringkas dan jujur; transkrip penuh tidak diminta. Yang dinilai bukan "pakai AI atau tidak",
melainkan "mengerti atau tidak" — isi kolom terakhir dengan apa yang Anda ubah dari keluarannya.

| Tanggal | Siapa (NIM) | Alat | Untuk apa | Apa yang diubah dari keluarannya |
|---|---|---|---|---|
| 2026-11-12 | 124450065 | Gemini | kerangka pembaca BPS, ILOSTAT, dan `ekstraksi.jalankan()` | sesuaikan parser JSON BPS ke format list multi-halaman agar kolom sejajar dengan CSV (`var_id`, `wilayah_id`, `satuan`), ubah pembaca ILOSTAT ke struktur `dataStructures` DSD & `dataflow.json` serta kamus kode `SEX`/`ECO`/`OCU`/`OBS_STATUS` |
| 2026-11-16 | 124450097 | Claude | kode src/silver (grid provinsi x periode, kelengkapan panel, penanda ekstrem) dan diagnosis galat pipeline | kode wilayah Papua diperbaiki sesuai data BPS (9500, 9600, 9700), jenis_periode diubah dari 'tahunan' ke 'tahun' sesuai skema.py, hasil celah Papua dan penanda ekstrem diperiksa sendiri terhadap reports/ |
| 2026-11-17 | 124450102 | Claude AI | verifikasi ulang output dan menjelaskan cara menangani error pada kode | Menjalankan cek_katalog.py dan membaca sendiri unit, judul, dan UNIT_MEASURE di JSON BPS dan CSV ILOSTAT; mengisi bukti_sdg var1172 dan var2153 secara manual karena metadata BPS tidak memuat nomor indikator; menempel draf log K-015 sampai K-017 setelah memeriksa isinya. |