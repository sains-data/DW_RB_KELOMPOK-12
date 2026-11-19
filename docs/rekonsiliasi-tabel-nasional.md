# Tugas #10 — Daftar Tabel Seri Utama, Pembanding Nasional, dan Pasangan Rekonsiliasi

**Kasus:** Kasus 12 — Upah dan Pekerjaan Informal (Klaster C: Gender dan Ketenagakerjaan, Tujuan SDG 8)

---

## 1. Daftar Tabel Seri Utama (Tingkat Provinsi — BPS)
*Snapshot: `2026-10-17`*

| Kode ID | Sumber | Kode Seri | Kode SDG | Berkas Data Utama (`data/raw/...`) | SHA-256 (CSV) | Periode | Satuan Katalog vs Aktual Berkas Mentah | Kolom Kunci & Dimensi Rincian |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **U-01** | `bps` | `var1172` (`var_id=1172`) | 8.5.1 | `bps/2026-10-17/sdg8_upah.csv` | `8b300477671616c97807fddf1fba72c8ce396a6dcc9048f650f1a9bbc41d948d` | 2015–2025 | Katalog: `rupiah_per_jam`<br>**Aktual:** `Rupiah/Jam` (kolom `satuan`) | `wilayah_id` (mis. `1100` ACEH), `tahun`, `turvar` (rincian variabel/gender) |
| **U-02** | `bps` | `var2153` (`var_id=2153`) | 8.3.1 | `bps/2026-10-17/sdg8_informal.csv` | `429887ef510e530874d2c1e382fde3b4984e38d94e3f07569da43891df0474fd` | 2018–2025 | Katalog: `tidak_ada`<br>**Aktual:** Kosong/NULL di CSV, nilai `59.44` mengonfirmasi **persen (`%`, skala 0–100)** | `wilayah_id`, `tahun`, `turvar` (rincian variabel/gender) |

---

## 2. Daftar Tabel Pembanding Nasional (ILOSTAT)
*Snapshot: `2026-10-20`*

| Kode ID | Sumber | Kode Seri | Kode SDG | Berkas Data Utama (`data/raw/...`) | SHA-256 (CSV) | Periode | Satuan Aktual Berkas Mentah | Kolom Kunci & Dimensi Rincian |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **P-01** | `ilostat` | `SDG_0851_SEX_OCU_NB` | 8.5.1 | `ilostat/2026-10-20/data/DF_SDG_0851_SEX_OCU_NB.csv` | `8de35e0462037775b72e7ac41bc7e4e59c129a8c59026531effcf4e46f8b1007` | 2007–2023 | `UNIT_MEASURE=LC` (*Local Currency*), `NOTE_INDICATOR=IDR: Indonesian rupiah`, `UNIT_MULT=0` (Rupiah nominal penuh per jam) | `REF_AREA=IDN`, `TIME_PERIOD`, `SEX` (`SEX_T`, dll.), `OCU` (`OCU_SKILL_TOTAL`, dll.) |
| **P-02** | `ilostat` | `SDG_0831_SEX_ECO_RT` | 8.3.1 | `ilostat/2026-10-20/data/DF_SDG_0831_SEX_ECO_RT.csv` | `61c59b5214390beb353baf69c2cffffce148357e84863f82352162fa8926b4f2` | 2016–2023 | `UNIT_MEASURE=PT` (*Percentage*, skala 0–100, contoh nilai `85.477`), `UNIT_MULT=0` | `REF_AREA=IDN`, `TIME_PERIOD`, `SEX` (`SEX_T`, dll.), `ECO` (`ECO_SECTOR_TOTAL`, dll.) |

---

## 3. Daftar Pasangan Rekonsiliasi (Untuk Lapis Gold)

> **Catatan Arsitektur:** Pada lapisan **Silver**, setiap seri disimpan terpisah dengan mempertahankan provenans (`_berkas_raw` dan `_sha256_raw`). Penggabungan dan rekonsiliasi antar sumber dilakukan pada lapisan **Gold**.

| ID Pasangan | Seri Utama | Seri Pembanding | Indikator SDG | Irisan Periode | Kunci Rekonsiliasi (*Join Keys*) | Hasil Verifikasi Keselarasan & Perbedaan | Aturan Resolusi & Penyelarasan |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REC-01** | `U-01` (`sdg8_upah.csv` / `var1172`) | `P-01` (`DF_SDG_0851_SEX_OCU_NB.csv`) | **SDG 8.5.1** (Rata-rata upah per jam) | 2015–2023 | `wilayah` (`IDN` / Indonesia), `tahun` (`TIME_PERIOD`), `rincian_gender` (`turvar` ↔ `SEX`) | 1. **Satuan sudah selaras:** Keduanya menggunakan **IDR nominal per jam** (`Rupiah/Jam` di BPS; `UNIT_MEASURE=LC` & `UNIT_MULT=0` di ILOSTAT).<br>2. **Cakupan Wilayah:** BPS mencakup provinsi & baris nasional (`wilayah_id` tertentu), sedangkan ILOSTAT hanya nasional (`IDN`).<br>3. **Dimensi Jabatan:** ILOSTAT memiliki rincian `OCU`. | 1. Filter baris nasional ("INDONESIA") pada seri BPS (atau hitung agregasi nasional) untuk disandingkan dengan `REF_AREA='IDN'`.<br>2. Filter `UNIT_MEASURE='LC'` dan `OCU='OCU_SKILL_TOTAL'` pada ILOSTAT.<br>3. Petakan `turvar` BPS (`Tidak ada` → `SEX_T`, serta kategori jenis kelamin jika tersedia). |
| **REC-02** | `U-02` (`sdg8_informal.csv` / `var2153`) | `P-02` (`DF_SDG_0831_SEX_ECO_RT.csv`) | **SDG 8.3.1** (Proporsi pekerjaan informal) | 2018–2023 | `wilayah` (`IDN` / Indonesia), `tahun` (`TIME_PERIOD`), `rincian_gender` (`turvar` ↔ `SEX`) | 1. **Satuan sudah selaras:** Keduanya dalam **persentase skala 0–100** (kolom `satuan` BPS kosong di mentah tetapi nilainya `59.44%`; ILOSTAT `UNIT_MEASURE=PT` nilainya `85.477%`).<br>2. **Cakupan Wilayah:** BPS tingkat provinsi & nasional vs ILOSTAT nasional.<br>3. **Dimensi Sektor:** ILOSTAT memiliki rincian `ECO`. | 1. Gunakan baris agregat nasional BPS untuk dibandingkan dengan `REF_AREA='IDN'`.<br>2. Isi nilai kolom `satuan` yang kosong pada BPS menjadi `persen` di lapisan Silver.<br>3. Filter `ECO='ECO_SECTOR_TOTAL'` pada ILOSTAT dan padankan kategori gender (`turvar` ↔ `SEX`). |
