# Sprint 1 (9–22 November 2026) — Bunga Clarisa Sefa (124450097)

## Sprint Goal

Semua berkas mentah Kasus 12 terbaca dengan lineage, setiap seri punya satuan dan kode SDG yang buktinya
tercatat, dan Silver pertama lolos pemeriksa skema serta aturan validasi dasar, sehingga Sprint 2 bisa
langsung menyusun panel dan tabel rekonsiliasi.

## Definition of Done yang dipakai

- [x] Pembaca semua format mentah (BPS JSON/CSV, ILOSTAT CSV/JSON); tidak ada berkas MANIFEST terlewat.
- [x] Profil dan calon anomali per seri utama (`var1172`, `var2153`) dan pembanding (`SDG_0851_SEX_OCU_NB`, `SDG_0831_SEX_ECO_RT`); grafik di `reports/gambar/`.
- [x] Missing (`16` sel kosong pemekaran Papua), outlier (`24` observasi ekstrem), patahan seri, dan duplikat ditangani serta dicatat di `log-keputusan.csv` (`K-001` s.d. `K-011`) dan `reports/tim.md`.
- [x] `data/silver/silver.parquet` (`1.362` baris, grid 38 provinsi × periode) lolos `python -m src.common.skema`.
- [x] `results/124450097/metrics.json` dan `reports/tim.md` sudah di-commit ke cabang `124450097/kerja`.