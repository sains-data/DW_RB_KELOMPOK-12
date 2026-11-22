# Laporan Persiapan Tahap 6: Rekonsiliasi Nasional (Kelompok 12)

## 1. Daftar Pasangan Rekonsiliasi & Catatan Keterbandingan

### Pasangan 1: Upah Rata-Rata per Jam (SDG 8.5.1)
* **Seri Utama (BPS):** `var1172` (Baris agregat Indonesia `wilayah_id=9999`, periode 2015–2025, satuan Rupiah/jam nominal).
* **Seri Pembanding (ILOSTAT):** `SDG_0851_SEX_OCU_NB` (Rincian `REF_AREA=IDN`, `SEX=SEX_T`, `OCU=OCU_SKILL_TOTAL`, satuan `UNIT_MEASURE=LC` mata uang lokal Rupiah/jam nominal, periode 2007–2023).
* **Periode Beririsan:** 2015–2023 (8 tahun terisi; data ILO tahun 2018 tidak tersedia di paket).
* **Catatan Keterbandingan:**
  * Kedua data sudah disamakan dalam satuan mata uang lokal (Rupiah/IDR) per jam dalam basis nominal sebelum dihitung selisihnya.
  * **Kategori Selisih:** **Metode** dan **Vintage** (perbedaan penimbang/pembulatan survei Sakernas serta perbedaan tanggal snapshot data antara BPS 17 Okt 2026 dan ILOSTAT 20 Okt 2026). Selisih dicatat dan tidak dihapus.

### Pasangan 2: Proporsi Lapangan Kerja Informal (SDG 8.3.1)
* **Seri Utama (BPS):** `var2153` (Baris agregat Indonesia `wilayah_id=9999`, periode 2018–2025, satuan persen `%`).
* **Seri Pembanding (ILOSTAT):** `SDG_0831_SEX_ECO_RT` (Rincian `REF_AREA=IDN`, `SEX=SEX_T`, `ECO=ECO_SECTOR_TOTAL` mencakup seluruh sektor termasuk pertanian, satuan `UNIT_MEASURE=PT` persen `%`, periode 2016–2023).
* **Periode Beririsan:** 2018–2023 (4 tahun terisi: 2018, 2019, 2022, 2023; data ILO tahun 2020–2021 tidak tersedia di paket).
* **Catatan Keterbandingan:**
  * Kedua data dibandingkan pada cakupan sektor yang seragam (seluruh sektor termasuk pertanian `ECO_SECTOR_TOTAL`).
  * **Kategori Selisih:** **Cakupan** dan **Definisi** (perbedaan operasionalisasi status pekerjaan informal antara tabulasi status pekerjaan Sakernas BPS dengan standar ICLS ILO). Selisih dicatat dan tidak dihapus.

## 2. Tabel Nasional Periode × Seri (Indonesia)

| periode | bps_var1172_upah | ilo_0851_upah_total | selisih_upah | kategori_upah | bps_var2153_informal | ilo_0831_informal_total | selisih_informal | kategori_informal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 | 11434.0 | 10338.45 | 1095.55 | metode / vintage | - | - | - |  |
| 2016 | 14068.0 | 12125.98 | 1942.02 | metode / vintage | - | 85.477 | - |  |
| 2017 | 14731.0 | 13924.58 | 806.42 | metode / vintage | - | 83.954 | - |  |
| 2018 | 15275.0 | - | - |  | 56.98 | 82.262 | -25.282 | cakupan / definisi |
| 2019 | 15823.0 | 14964.7 | 858.3 | metode / vintage | 55.88 | 80.343 | -24.463 | cakupan / definisi |
| 2020 | 17696.0 | 15835.27 | 1860.73 | metode / vintage | 60.47 | - | - |  |
| 2021 | 18089.0 | 16734.73 | 1354.27 | metode / vintage | 59.45 | - | - |  |
| 2022 | 17542.0 | 16232.45 | 1309.55 | metode / vintage | 59.31 | 80.158 | -20.848 | cakupan / definisi |
| 2023 | 19027.0 | 16316.96 | 2710.04 | metode / vintage | 59.11 | 80.938 | -21.828 | cakupan / definisi |
| 2024 | 19009.0 | - | - |  | 57.95 | - | - |  |
| 2025 | 20030.36 | - | - |  | 57.8 | - | - |  |
