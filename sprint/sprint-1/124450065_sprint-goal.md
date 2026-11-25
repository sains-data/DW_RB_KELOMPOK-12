# Sprint 1 (9–22 November 2026) — Zoland Ryo Febriano (124450065)

**Peran:** Koordinator — Ekstraksi dan Lineage

## Sprint Goal

Semua berkas mentah Kasus 12 (BPS dan ILOSTAT) terbaca dengan lineage, setiap seri punya satu satuan dan kode
SDG yang buktinya tercatat, dan Silver pertama (4 seri) lolos pemeriksa skema serta aturan validasi dasar,
sehingga Sprint 2 bisa langsung menyusun panel dan tabel rekonsiliasi.

## Definition of Done yang dipakai

- [x] **Verifikasi `MANIFEST.csv` & Pembaca BPS (`src/ekstraksi/bps.py`, Tiket #1, PR #1):**
      Seluruh 10/10 berkas di `data/raw/` lolos pemeriksaan SHA-256 `MANIFEST.csv` (`0` salah); pembaca BPS mengurai 2 CSV (`sdg8_upah.csv` 393 baris, `sdg8_informal.csv` 288 baris) dan 2 JSON bersarang (`sdg8_upah.json` 393 baris, `sdg8_informal.json` 288 baris) dengan kolom `_berkas_raw` dan `_sha256_raw` terisi penuh.
- [x] **Pembaca ILOSTAT & Kamus DSD (`src/ekstraksi/ilostat.py`, Tiket #2, PR #1):**
      Mengurai 2 CSV SDMX (`DF_SDG_0831_SEX_ECO_RT.csv` 216 baris, `DF_SDG_0851_SEX_OCU_NB.csv` 687 baris) beserta 2 DSD JSON dan 1 metadata dataflow JSON dengan lineage `_berkas_raw` dan `_sha256_raw` lengkap.
- [x] **Penggabungan Tabel Mentah Ber-Lineage (`ekstraksi.jalankan()`, Tiket #3, PR #1):**
      Menyatukan seluruh pembaca BPS dan ILOSTAT menjadi satu tabel mentah terpadu sebanyak `2.265` baris dari 6 berkas data tanpa mengubah kolom asal dan dengan `0` null pada `_berkas_raw` maupun `_sha256_raw`.
- [x] **Kesiapan Silver & Metrik Anggota (`results/124450065/metrics.json`, PR #14):**
      `data/silver/silver.parquet` (`1.362` baris bersih, grid 38 provinsi × periode, 4 seri) lolos `python -m src.common.skema`, `python -m src.silver.cek`, dan `python -m src.silver.katalog`, serta `results/124450065/metrics.json` sudah di-commit.
- [x] **Koordinasi Sprint 1 di Papan Tim (Tiket #14):**
      `Tujuan sprint` (Sprint Goal) terisi di Papan Tim, `Log Sprint` seluruh 5/5 anggota terisi dan berstatus hijau (`🟢`) di Rekap Lampu, serta rekaman Demo Sprint 1 disiapkan untuk unggah sebelum batas waktu 22 Nov 2026.