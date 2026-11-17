# Data dictionary – Kelompok 12

Satu tabel per keluaran (Silver dan setiap tabel Gold). Isi dari data nyata, bukan dari ingatan:
tipe, satuan, rentang, dan jumlah kosong dihitung ulang setiap kali pipeline berjalan.

## data/silver/silver.parquet

Satu baris = satu seri × wilayah × periode × rincian × berkas sumber. 2.265 baris: BPS 1.362 (CSV dan JSON), ILOSTAT 903. Nilai dari sumber berbeda tidak digabung di Silver.

| Kolom | Tipe | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal (berkas/aturan) | Keterangan |
|---|---|---|---|---|---|---|
| sumber | string | - | tidak | bps, ilostat | nama folder data/raw | Sumber data |
| seri_kode | string | kode seri | tidak | var1172, var2153, SDG_0851_SEX_OCU_NB, SDG_0831_SEX_ECO_RT | `var` + var_id (BPS); nama berkas tanpa awalan `DF_` (ILOSTAT) | Lihat katalog seri di bawah |
| wilayah_kode | int | kode BPS × 100 | tidak | 9999 (Indonesia) atau 1100–9700 (38 provinsi) | K-001 | ILOSTAT hanya 9999 (REF_AREA=IDN) |
| nama_wilayah | string | nama | tidak | 38 provinsi dan "Indonesia" | K-001 | Dipetakan dari kode, bukan dari nama |
| periode | string | YYYY | tidak | BPS 2015–2025; ILOSTAT 2007–2023 | kolom tahun (BPS), TIME_PERIOD (ILOSTAT) | Semua tahunan; tidak ada periode yang diratakan |
| jenis_periode | string | - | tidak | tahun | aturan periode Silver | Skema mengizinkan semester, triwulan, bulan; data saat ini hanya tahun |
| rincian | string | kode huruf kecil | tidak | BPS: `total`; ILOSTAT: 120 kombinasi (84 `sex_*_ocu_*`, 36 `sex_*_eco_*`) | K-012 | Disimpan apa adanya; pemilihan rincian sebanding dikerjakan di Gold |
| nilai | float | lihat satuan | tidak | rupiah_per_jam: 2.594–52.167; persen: 29,6–98,9 | kolom nilai (BPS), OBS_VALUE (ILOSTAT) | Baris tanpa nilai tidak disimpan |
| satuan | string | - | tidak | rupiah_per_jam, persen | docs/katalog_seri.csv | Satu satuan per seri |
| _berkas_raw | string | jalur relatif data/raw | tidak | 6 berkas | lineage | 4 berkas BPS (2 CSV, 2 JSON) dan 2 CSV ILOSTAT |
| _sha256_raw | string | sha256 heksadesimal | tidak | cocok dengan MANIFEST.csv | lineage | Diperiksa oleh `src/common/skema.py` |
| outlier_ekstrem | bool | - | tidak | True/False | K-007 | True hanya untuk provinsi ekstrem (IQR 1,5); selalu False untuk Indonesia dan ILOSTAT. Nilai tidak diubah |
| status_obs | string | kode status | ya | B (patahan seri) atau kosong | K-013 | Kosong untuk BPS dan ILOSTAT tanpa status; 144 baris ILOSTAT terisi |
| dim_sex | string | kode SDMX | ya | SEX_T, SEX_M, SEX_F | K-012 | Kosong untuk baris BPS |
| dim_ocu | string | kode SDMX | ya | 28 kode OCU_* | K-012 | Terisi hanya untuk SDG_0851_SEX_OCU_NB |
| dim_eco | string | kode SDMX | ya | 12 kode ECO_* | K-012 | Terisi hanya untuk SDG_0831_SEX_ECO_RT |

### Katalog seri (satuan dan kode SDG final)

| Seri | Sumber | Kode SDG | Satuan | Catatan |
|---|---|---|---|---|
| `var1172` | BPS | 8.5.1 | `rupiah_per_jam` | Upah rata-rata per jam pekerja, per provinsi; unit sumber "Rupiah/Jam" |
| `var2153` | BPS | 8.3.1 | `persen` | Proporsi lapangan kerja informal; unit sumber kosong, katalog awal `tidak_ada`, dikoreksi (K-002) |
| `SDG_0851_SEX_OCU_NB` | ILOSTAT | 8.5.1 | `rupiah_per_jam` | `UNIT_MEASURE=LC`, mata uang IDR; nominal |
| `SDG_0831_SEX_ECO_RT` | ILOSTAT | 8.3.1 | `persen` | `UNIT_MEASURE=PT`, `UNIT_MEASURE_TYPE=RT` |

Semua seri tahunan. Sumber bukti per seri: `docs/katalog_seri.csv`.

## data/gold/<tabel>.parquet

| Kolom | Tipe | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal (berkas/aturan) | Keterangan |
|---|---|---|---|---|---|---|