# Data dictionary – Kelompok 12 

Satu tabel per keluaran (Silver dan setiap tabel Gold). Isi dari data nyata, bukan dari ingatan:
tipe, satuan, rentang, dan jumlah kosong dihitung ulang setiap kali pipeline berjalan.

## data/silver/silver.parquet

| Kolom | Tipe | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal (berkas/aturan) | Keterangan |
|---|---|---|---|---|---|---|
| sumber | string | - | tidak | bps, bnpb, wdi, who_gho, ilostat | nama folder data/raw | |
| wilayah_kode | int | kode BPS x 100 | tidak | 9999 atau 1100–9600 | log K-... | |
| ref_area | string | kode wilayah | tidak | kode area valid | kolom dataset raw | Wilayah atau negara pengamat |
| indicator | string | kode indikator | tidak | DF_SDG_0851_SEX_OCU_NB | kolom dataset raw | Indikator SDG 8.5.1 |
| sex | string | kategori | tidak | SEX_T, SEX_M, SEX_F | kolom dataset raw | Jenis kelamin |
| ocu | string | kategori | tidak | kode okupasi valid | kolom dataset raw | Klasifikasi okupasi/pekerjaan |
| time | int | tahun | tidak | >= 2000 | kolom dataset raw | Periode waktu / tahun pencatatan |
| obs_value | float | angka / rasio | tidak | >= 0 | kolom dataset raw | Nilai pengamatan indikator |

## data/gold/<tabel>.parquet

| Kolom | Tipe | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal (berkas/aturan) | Keterangan |
|---|---|---|---|---|---|---|
