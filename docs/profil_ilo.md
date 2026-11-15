# Profil Data ILOSTAT & Keterbandingan dengan Seri Utama BPS

Dokumen ini merangkum ketersediaan data ILOSTAT (unduhan `2026-10-20`) untuk indikator SDG 8 Indonesia serta evaluasi keterbandingannya dengan data nasional BPS (`2026-10-17`).

## 1. Ringkasan Seri dan Cakupan

| Kode Seri ILO | Indikator | Seri Pembanding BPS | Total Rincian (SEX x Dimensi) | Rentang Tahun ILO | Irisan Tahun dengan BPS |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `SDG_0851_SEX_OCU_NB` | Rata-rata upah per jam pekerja (`LC`, Rupiah/jam) | `sdg8_upah` (2015–2025) | 84 kombinasi (3 SEX × 28 OCU) | 2007–2023 (15 thn; absen 2011, 2018) | 2015–2017, 2019–2023 (8 thn) |
| `SDG_0831_SEX_ECO_RT` | Proporsi lapangan kerja informal (`PT`, Persen) | `sdg8_informal` (2018–2025) | 36 kombinasi (3 SEX × 12 ECO) | 2016–2023 (6 thn; absen 2020–2021) | 2018–2019, 2022–2023 (4 thn) |

## 2. Rincian Kandidat Sebanding dengan Seri Utama BPS

Tabel lengkap seluruh 120 kombinasi `seri × periode × rincian` tersimpan di `docs/ketersediaan_ilo.csv`. Berikut adalah rincian yang terpilih sebagai kandidat pembanding seri nasional BPS:

### SDG_0831_SEX_ECO_RT — `SEX_T` + `ECO_SECTOR_TOTAL` (Kandidat Utama)
- **Seri BPS Pembanding:** sdg8_informal (Proporsi Lapangan Kerja Informal)
- **Satuan:** PT (RT, 10^0)
- **Tahun Tersedia ILO:** 2016, 2017, 2018, 2019, 2022, 2023
- **Tahun Irisan dengan BPS:** 2018, 2019, 2022, 2023 (4 tahun)
- **Alasan & Catatan Metodologis:** Kandidat Utama: Agregat total seluruh pekerja & seluruh sektor ekonomi, satuan identik (persentase/PT), beririsan 4 tahun dengan BPS (2018, 2019, 2022, 2023). Catatan: ILO tidak memiliki observasi 2020-2021 sehingga diperlukan verifikasi definisi pekerja informal ILO vs proksi status pekerjaan BPS.

### SDG_0831_SEX_ECO_RT — `SEX_T` + `ECO_AGGREGATE_TOTAL` (Kandidat Alternatif)
- **Seri BPS Pembanding:** sdg8_informal (Proporsi Lapangan Kerja Informal)
- **Satuan:** PT (RT, 10^0)
- **Tahun Tersedia ILO:** 2016, 2017, 2018, 2019, 2022, 2023
- **Tahun Irisan dengan BPS:** 2018, 2019, 2022, 2023 (4 tahun)
- **Alasan & Catatan Metodologis:** Kandidat Alternatif (Duplikat Agregat): Menghasilkan nilai agregat total yang identik dengan ECO_SECTOR_TOTAL pada seluruh tahun tersedia (2016-2019, 2022-2023); cukup gunakan satu seri agregat untuk menghindari duplikasi.

### SDG_0851_SEX_OCU_NB — `SEX_T` + `OCU_SKILL_TOTAL` (Kandidat Utama)
- **Seri BPS Pembanding:** sdg8_upah (Upah Rata-Rata Per Jam Pekerja)
- **Satuan:** LC (NB, 10^0)
- **Tahun Tersedia ILO:** 2007, 2008, 2009, 2010, 2012, 2013, 2014, 2015, 2016, 2017, 2019, 2020, 2021, 2022, 2023
- **Tahun Irisan dengan BPS:** 2015, 2016, 2017, 2019, 2020, 2021, 2022, 2023 (8 tahun)
- **Alasan & Catatan Metodologis:** Kandidat Utama: Agregat total seluruh pekerja & seluruh okupasi, satuan identik (IDR/Rupiah per jam), mencakup rentang terpanjang (2007-2023) dan beririsan 8 tahun dengan BPS (2015, 2016, 2017, 2019, 2020, 2021, 2022, 2023). Catatan: terdapat break in series metodologi ILO pada 2021 dan selisih level nominal akibat perbedaan cakupan status pekerja.

### SDG_0851_SEX_OCU_NB — `SEX_T` + `OCU_ISCO08_TOTAL` (Kandidat Alternatif)
- **Seri BPS Pembanding:** sdg8_upah (Upah Rata-Rata Per Jam Pekerja)
- **Satuan:** LC (NB, 10^0)
- **Tahun Tersedia ILO:** 2017, 2019, 2020, 2021, 2022, 2023
- **Tahun Irisan dengan BPS:** 2017, 2019, 2020, 2021, 2022, 2023 (6 tahun)
- **Alasan & Catatan Metodologis:** Kandidat Alternatif: Agregat total berbasis klasifikasi ISCO-08 dengan nilai identik dengan OCU_SKILL_TOTAL pada 2017-2023 (beririsan 6 tahun dengan BPS), namun tidak mencakup tahun 2015-2016.

## 3. Perbandingan Nilai Agregat Nasional: BPS vs ILO (`SDG_0851`)

Perbandingan antara angka nasional BPS (`wilayah_id = 9999`, INDONESIA) dan kandidat utama ILO (`SEX_T`, `OCU_SKILL_TOTAL`):

| Tahun | BPS Nasional (Rp/Jam) | ILO `OCU_SKILL_TOTAL` (Rp/Jam) | Selisih (BPS - ILO) | Catatan Metodologi ILO |
| :---: | :---: | :---: | :---: | :--- |
| 2007 | - | 6,000.44 | - | IDR: Indonesian rupiah |
| 2008 | - | 6,384.46 | - | Break in series: Methodology revised | IDR: Indonesian rupiah |
| 2009 | - | 7,241.42 | - | IDR: Indonesian rupiah |
| 2010 | - | 7,661.67 | - | IDR: Indonesian rupiah |
| 2012 | - | 8,112.87 | - | IDR: Indonesian rupiah |
| 2013 | - | 9,585.01 | - | Break in series: Methodology revised | IDR: Indonesian rupiah |
| 2014 | - | 9,731.04 | - | IDR: Indonesian rupiah |
| 2015 | 11,434.00 | 10,338.45 | +1,095.55 | IDR: Indonesian rupiah |
| 2016 | 14,068.00 | 12,125.98 | +1,942.02 | IDR: Indonesian rupiah |
| 2017 | 14,731.00 | 13,924.58 | +806.42 | IDR: Indonesian rupiah |
| 2018 | 15,275.00 | - | - | - |
| 2019 | 15,823.00 | 14,964.70 | +858.30 | IDR: Indonesian rupiah |
| 2020 | 17,696.00 | 15,835.27 | +1,860.73 | IDR: Indonesian rupiah |
| 2021 | 18,089.00 | 16,734.73 | +1,354.27 | Break in series: Methodology revised | IDR: Indonesian rupiah |
| 2022 | 17,542.00 | 16,232.45 | +1,309.55 | IDR: Indonesian rupiah |
| 2023 | 19,027.00 | 16,316.96 | +2,710.04 | IDR: Indonesian rupiah |
| 2024 | 19,009.00 | - | - | - |
| 2025 | 20,030.36 | - | - | - |

## 4. Kesimpulan Kelayakan Pembandingan

1. **Kelayakan Lintas Sumber:** Kedua seri ILO (`SEX_T` + `OCU_SKILL_TOTAL` dan `SEX_T` + `ECO_SECTOR_TOTAL`) layak digunakan sebagai pembanding tren makro nasional terhadap seri BPS karena memiliki satuan ukur yang sama (Rupiah/jam dan Persentase) serta sumber mikrodata dasar yang sama (Sakernas).
2. **Batasan Agregasi:** Rincian berdasarkan jenis kelamin (`SEX_M`, `SEX_F`), tingkat keterampilan (`OCU_SKILL_L1..L3-4`), klasifikasi jabatan (`OCU_ISCO*`), maupun sektor ekonomi (`ECO_SECTOR_*`, `ECO_AGGREGATE_*`) tidak dapat dibandingkan langsung dengan tabel BPS saat ini karena tabel BPS hanya memuat angka agregat total.
3. **Penanganan *Break in Series* & Kekosongan Tahun:** Analisis tren upah ILO wajib menandai patahan metodologi (*break in series*) pada tahun **2021**, sementara analisis informal ILO harus memperhitungkan ketiadaan data pada **2020–2021** (masa pandemi COVID-19).
