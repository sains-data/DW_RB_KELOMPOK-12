# AI_LOG — Kelompok 12

Satu baris per pemakaian AI yang bermakna (ChatGPT, Claude, Copilot, Bravais, dan sejenisnya).
Ringkas dan jujur; transkrip penuh tidak diminta. Yang dinilai bukan "pakai AI atau tidak",
melainkan "mengerti atau tidak" — isi kolom terakhir dengan apa yang Anda ubah dari keluarannya.

| Tanggal | Siapa (NIM) | Alat | Untuk apa | Apa yang diubah dari keluarannya |
|---|---|---|---|---|
| 2026-11-12 | 124450065 | Gemini | kerangka pembaca BPS, ILOSTAT, dan `ekstraksi.jalankan()` | sesuaikan parser JSON BPS ke format list multi-halaman agar kolom sejajar dengan CSV (`var_id`, `wilayah_id`, `satuan`), ubah pembaca ILOSTAT ke struktur `dataStructures` DSD & `dataflow.json` serta kamus kode `SEX`/`ECO`/`OCU`/`OBS_STATUS` |
| 2026-11-16 | 124450097 | Claude | kode src/silver (grid provinsi x periode, kelengkapan panel, penanda ekstrem) dan diagnosis galat pipeline | kode wilayah Papua diperbaiki sesuai data BPS (9500, 9600, 9700), jenis_periode diubah dari 'tahunan' ke 'tahun' sesuai skema.py, hasil celah Papua dan penanda ekstrem diperiksa sendiri terhadap reports/ |
