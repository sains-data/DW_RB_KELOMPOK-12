import pandas as pd
import numpy as np

# 1. Baca 4 file mentah
bps_upah = pd.read_csv("data/raw/bps/2026-10-17/sdg8_upah.csv")
bps_inf = pd.read_csv("data/raw/bps/2026-10-17/sdg8_informal.csv")
ilo_upah = pd.read_csv("data/raw/ilostat/2026-10-20/data/DF_SDG_0851_SEX_OCU_NB.csv")
ilo_inf = pd.read_csv("data/raw/ilostat/2026-10-20/data/DF_SDG_0831_SEX_ECO_RT.csv")

# 2. Ambil baris nasional BPS (wilayah_id == 9999)
b_upah = bps_upah[bps_upah["wilayah_id"] == 9999][["tahun", "nilai"]].rename(
    columns={"tahun": "periode", "nilai": "bps_var1172_upah"}
)
b_inf = bps_inf[bps_inf["wilayah_id"] == 9999][["tahun", "nilai"]].rename(
    columns={"tahun": "periode", "nilai": "bps_var2153_informal"}
)

# 3. Ambil baris nasional ILOSTAT (IDN, SEX_T, TOTAL)
i_upah = ilo_upah[
    (ilo_upah["REF_AREA"] == "IDN") &
    (ilo_upah["SEX"] == "SEX_T") &
    (ilo_upah["OCU"] == "OCU_SKILL_TOTAL")
][["TIME_PERIOD", "OBS_VALUE"]].rename(
    columns={"TIME_PERIOD": "periode", "OBS_VALUE": "ilo_0851_upah_total"}
)

i_inf = ilo_inf[
    (ilo_inf["REF_AREA"] == "IDN") &
    (ilo_inf["SEX"] == "SEX_T") &
    (ilo_inf["ECO"] == "ECO_SECTOR_TOTAL")
][["TIME_PERIOD", "OBS_VALUE"]].rename(
    columns={"TIME_PERIOD": "periode", "OBS_VALUE": "ilo_0831_informal_total"}
)

# 4. Gabungkan ke satu tabel periode x seri (2015 s.d. 2025)
df = pd.DataFrame({"periode": range(2015, 2026)})
df = df.merge(b_upah, on="periode", how="left")
df = df.merge(i_upah, on="periode", how="left")
df["selisih_upah"] = (df["bps_var1172_upah"] - df["ilo_0851_upah_total"]).round(2)
df["kategori_upah"] = np.where(df["selisih_upah"].notna(), "metode / vintage", "")

df = df.merge(b_inf, on="periode", how="left")
df = df.merge(i_inf, on="periode", how="left")
df["selisih_informal"] = (df["bps_var2153_informal"] - df["ilo_0831_informal_total"]).round(3)
df["kategori_informal"] = np.where(df["selisih_informal"].notna(), "cakupan / definisi", "")

# 5. Simpan CSV ke data/gold/
df.to_csv("data/gold/tabel_nasional_periode_seri.csv", index=False)

# 6. Buat tabel Markdown secara manual (aman tanpa butuh library tabulate)
df_str = df.fillna("-").astype(str)
header = "| " + " | ".join(df_str.columns) + " |"
sep = "| " + " | ".join(["---"] * len(df_str.columns)) + " |"
rows = ["| " + " | ".join(r) + " |" for r in df_str.values]
tabel_md = "\n".join([header, sep] + rows)

# 7. Tulis laporan lengkap ke reports/rekonsiliasi_tahap6.md
laporan = f"""# Laporan Persiapan Tahap 6: Rekonsiliasi Nasional (Kelompok 12)

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

{tabel_md}
"""

with open("reports/rekonsiliasi_tahap6.md", "w", encoding="utf-8") as f:
    f.write(laporan)

print("=== BERHASIL! TABEL NASIONAL PERIODE x SERI ===\n")
print(tabel_md)
