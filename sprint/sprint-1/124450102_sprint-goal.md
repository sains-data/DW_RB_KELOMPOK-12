# Sprint 1 (9-22 November 2026)

## Sprint Goal

Semua berkas mentah Kasus 12 (BPS dan ILOSTAT) terbaca dengan lineage, setiap seri punya satu satuan dan kode
SDG yang buktinya tercatat, dan Silver pertama (4 seri) lolos pemeriksa skema serta aturan validasi dasar,
sehingga Sprint 2 bisa langsung menyusun panel dan tabel rekonsiliasi.

## Definition of Done yang dipakai


- [x] `data/silver/silver.parquet` lolos `python -m src.common.skema` (4 seri, 39 wilayah, 6 berkas sumber),
      kunci tidak kembar, dan `python -m src.silver.cek` tanpa `GAGAL` (baris BPS tetap 1.362).
- [x] Satu satuan dan kode SDG per seri, bukti sumbernya tercatat di `docs/katalog_seri.csv`
      (`python -m src.silver.katalog` LOLOS); `var2153` dari `tidak_ada` menjadi `persen`.
- [x] Tidak ada periode semesteran/bulanan yang diratakan ke tahunan di Silver.
- [x] Keputusan baru dan koreksi katalog tercatat di `log-keputusan.csv`.
- [x] `results/124450102/metrics.json` di-commit dan bukti dikirim dari Papan Tim.
