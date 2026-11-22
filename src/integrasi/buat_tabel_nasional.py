import pandas as pd

# 1. Baca data mentah BPS
bps_upah = pd.read_csv("data/raw/bps/2026-10-17/sdg8_upah.csv")
bps_inf = pd.read_csv("data/raw/bps/2026-10-17/sdg8_informal.csv")

# Deteksi otomatis kolom wilayah/provinsi, tahun, dan nilai di CSV BPS
col_wil_u = [c for c in bps_upah.columns if c.lower() in ["wilayah", "provinsi", "nama_wilayah", "kode_wilayah", "region"]][0]
col_thn_u = [c for c in bps_upah.columns if c.lower() in ["tahun", "periode", "year"]][0]
col_val_u = [c for c in bps_upah.columns if c.lower() in ["nilai", "value", "var1172"]][0]

col_wil_i = [c for c in bps_inf.columns if c.lower() in ["wilayah", "provinsi", "nama_wilayah", "kode_wilayah", "region"]][0]
col_thn_i = [c for c in bps_inf.columns if c.lower() in ["tahun", "periode", "year"]][0]
col_val_i = [c for c in bps_inf.columns if c.lower() in ["nilai", "value", "var2153"]][0]

# Filter hanya baris nasional ("INDONESIA")
nas_var1172 = (
    bps_upah[bps_upah[col_wil_u].astype(str).str.upper().str.contains("INDONESIA")][[col_thn_u, col_val_u]]
    .rename(columns={col_thn_u: "periode", col_val_u: "bps_var1172_idr_jam"})
)

nas_var2153 = (
    bps_inf[bps_inf[col_wil_i].astype(str).str.upper().str.contains("INDONESIA")][[col_thn_i, col_val_i]]
    .rename(columns={col_thn_i: "periode", col_val_i: "bps_var2153_persen"})
)

# 2. Baca data pembanding ILOSTAT
ilo_upah = pd.read_csv("data/raw/ilostat/2026-10-20/data/DF_SDG_0851_SEX_OCU_NB.csv")
ilo_inf = pd.read_csv("data/raw/ilostat/2026-10-20/data/DF_SDG_0831_SEX_ECO_RT.csv")

# Filter ILO Upah: Indonesia (IDN), Total Sex, Total Jabatan (OCU), Mata Uang Lokal (LCU/IDR)
cond_upah = (
    (ilo_upah["REF_AREA"] == "IDN") &
    (ilo_upah["SEX"] == "SEX_T") &
    (ilo_upah["CLASSIF1"].astype(str).str.contains("TOTAL", na=False))
)
if "CUR_TYPE" in ilo_upah.columns:
    cond_upah = cond_upah & (ilo_upah["CUR_TYPE"] == "LCU")

nas_ilo_851 = (
    ilo_upah[cond_upah][["TIME_PERIOD", "OBS_VALUE"]]
    .rename(columns={"TIME_PERIOD": "periode", "OBS_VALUE": "ilo_0851_idr_jam"})
)

# Filter ILO Informal: Indonesia (IDN), Total Sex, Total Sektor (ECO_TOTAL = termasuk pertanian)
cond_inf = (
    (ilo_inf["REF_AREA"] == "IDN") &
    (ilo_inf["SEX"] == "SEX_T") &
    (ilo_inf["CLASSIF1"].astype(str).str.contains("TOTAL", na=False))
)
nas_ilo_831 = (
    ilo_inf[cond_inf][["TIME_PERIOD", "OBS_VALUE"]]
    .rename(columns={"TIME_PERIOD": "periode", "OBS_VALUE": "ilo_0831_persen"})
)

# Pastikan tipe data periode adalah integer
for df in [nas_var1172, nas_var2153, nas_ilo_851, nas_ilo_831]:
    df["periode"] = df["periode"].astype(int)

# 3. Gabungkan ke satu tabel periode x seri
tabel_nasional = (
    nas_var1172
    .merge(nas_ilo_851, on="periode", how="outer")
    .merge(nas_var2153, on="periode", how="outer")
    .merge(nas_ilo_831, on="periode", how="outer")
    .sort_values("periode")
    .reset_index(drop=True)
)

# Hitung kolom selisih (tidak menghapus baris)
tabel_nasional["selisih_851_idr"] = tabel_nasional["bps_var1172_idr_jam"] - tabel_nasional["ilo_0851_idr_jam"]
tabel_nasional["selisih_831_persen"] = tabel_nasional["bps_var2153_persen"] - tabel_nasional["ilo_0831_persen"]

# 4. Simpan ke repositori
tabel_nasional.to_csv("reports/tabel_nasional_periode_seri.csv", index=False)
print("=== TABEL NASIONAL PERIODE X SERI ===")
print(tabel_nasional.to_string(index=False))
