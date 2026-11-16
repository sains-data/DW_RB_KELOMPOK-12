
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .wilayah import INDONESIA

# Nama kolom pada CSV SDMX ILOSTAT. Bila hasil cek_ilo.py menunjukkan nama lain, ubah di sini.
KOL_WILAYAH = "REF_AREA"
KOL_WAKTU = "TIME_PERIOD"
KOL_NILAI = "OBS_VALUE"
KOL_STATUS = "OBS_STATUS"

KODE_WILAYAH_ILO = {"IDN": INDONESIA}  # ILOSTAT memakai ISO3; Silver memakai 9999 untuk Indonesia

# seri_kode = nama berkas tanpa awalan "DF_". `dimensi` = kolom yang membentuk `rincian`.
SERI_ILO = {
    "SDG_0851_SEX_OCU_NB": {"satuan": "rupiah_per_jam", "dimensi": ["SEX", "OCU"]},
    "SDG_0831_SEX_ECO_RT": {"satuan": "persen", "dimensi": ["SEX", "ECO"]},
}

POLA_PERIODE = [
    ("tahun", r"^\d{4}$"),
    ("semester", r"^\d{4}-S[12]$"),
    ("triwulan", r"^\d{4}-Q[1-4]$"),
    ("bulan", r"^\d{4}-(0[1-9]|1[0-2])$"),
]

# Kolom tambahan di luar skema minimal: kode dimensi mentah dan status observasi (mis. B = patahan seri)
KOLOM_TAMBAHAN = ["status_obs", "dim_sex", "dim_ocu", "dim_eco"]
KUNCI = ["seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw"]


def _seri_dari_berkas(berkas: str) -> str:
    nama = Path(berkas).stem
    return nama[3:] if nama.startswith("DF_") else nama


def _jenis_periode(periode: pd.Series) -> pd.Series:
    jenis = pd.Series(pd.NA, index=periode.index, dtype="object")
    for nama, pola in POLA_PERIODE:
        jenis = jenis.mask(periode.str.match(pola), nama)
    if jenis.isna().any():
        aneh = sorted(set(periode[jenis.isna()]))[:10]
        raise ValueError(f"Format periode ILOSTAT tidak dikenal: {aneh}. Tambahkan polanya di POLA_PERIODE.")
    return jenis


def _bersihkan_satu_seri(seri: str, d: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    cfg = SERI_ILO[seri]
    dimensi = cfg["dimensi"]
    perlu = [KOL_WILAYAH, KOL_WAKTU, KOL_NILAI, *dimensi]
    hilang = [k for k in perlu if k not in d.columns or d[k].isna().all()]
    if hilang:
        raise KeyError(f"{seri}: kolom {hilang} tidak ada di data mentah. Jalankan cek_ilo.py, lalu "
                       f"sesuaikan KOL_* atau SERI_ILO di src/silver/ilostat.py.")
    for k in dimensi:
        if d[k].isna().any():
            raise ValueError(f"{seri}: kolom dimensi {k} punya {int(d[k].isna().sum())} sel kosong.")

    stat = {}
    num = pd.to_numeric(d[KOL_NILAI], errors="coerce")
    stat["ilo_nilai_kosong"] = int(d[KOL_NILAI].isna().sum())
    stat["ilo_nilai_tak_terbaca"] = int((d[KOL_NILAI].notna() & num.isna()).sum())
    d = d.assign(_nilai=num)[num.notna()].copy()

    kode = d[KOL_WILAYAH].astype(str).str.strip().str.upper().map(KODE_WILAYAH_ILO)
    if kode.isna().any():
        tak = sorted(set(d.loc[kode.isna(), KOL_WILAYAH]))
        raise ValueError(f"{seri}: REF_AREA di luar {list(KODE_WILAYAH_ILO)}: {tak}")

    out = pd.DataFrame(index=d.index)
    out["sumber"] = "ilostat"
    out["seri_kode"] = seri
    out["wilayah_kode"] = kode.astype(int)
    out["nama_wilayah"] = "Indonesia"
    out["periode"] = d[KOL_WAKTU].astype(str).str.strip()
    out["jenis_periode"] = _jenis_periode(out["periode"])
    bagian = [d[k].astype(str).str.strip().str.lower() for k in dimensi]
    rincian = bagian[0]
    for b in bagian[1:]:
        rincian = rincian + "_" + b
    out["rincian"] = rincian
    out["nilai"] = d["_nilai"].astype(float)
    out["satuan"] = cfg["satuan"]
    out["_berkas_raw"] = d["_berkas_raw"]
    out["_sha256_raw"] = d["_sha256_raw"]
    out["outlier_ekstrem"] = False  # penanda ekstrem hanya untuk provinsi; Indonesia (9999) tidak ikut

    status = d[KOL_STATUS].astype("string").str.strip() if KOL_STATUS in d.columns else pd.Series(pd.NA, index=d.index, dtype="string")
    out["status_obs"] = status.where(status.notna() & (status != ""), None).astype(object)
    for k in ("SEX", "OCU", "ECO"):
        out[f"dim_{k.lower()}"] = d[k].astype(str).str.strip() if k in dimensi else None

    dup = out.duplicated(KUNCI, keep=False)
    if dup.any():
        beda = out[dup].groupby(KUNCI)["nilai"].nunique()
        if (beda > 1).any():
            contoh = d.loc[out[dup].index].dropna(axis=1, how="all").head(6).to_string()
            raise ValueError(f"{seri}: kunci kembar dengan nilai berbeda. Kemungkinan ada dimensi lain "
                             f"yang belum masuk SERI_ILO['dimensi'] (jalankan cek_ilo.py). Contoh:\n{contoh}")
    stat["ilo_duplikat_dibuang"] = int(out.duplicated(KUNCI).sum())
    out = out.drop_duplicates(KUNCI, keep="last")
    return out.reset_index(drop=True), stat


def bangun_silver_ilostat(mentah: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Ubah baris ILOSTAT hasil Tahap 1 menjadi Silver. Mengembalikan (silver_ilo, statistik)."""
    m = mentah[mentah["sumber"] == "ilostat"].copy()
    if m.empty:
        raise ValueError("Tidak ada baris ILOSTAT pada keluaran ekstraksi.")
    m["seri_kode"] = m["_berkas_raw"].map(_seri_dari_berkas)
    tak = sorted(set(m["seri_kode"]) - set(SERI_ILO))
    if tak:
        raise ValueError(f"Seri ILOSTAT belum didaftarkan di SERI_ILO: {tak}")

    stat = {"baris_mentah_ilo": len(m), "ilo_nilai_kosong": 0, "ilo_nilai_tak_terbaca": 0,
            "ilo_duplikat_dibuang": 0}
    bagian = []
    for seri, d in m.groupby("seri_kode", sort=True):
        s, st = _bersihkan_satu_seri(seri, d)
        bagian.append(s)
        for k, v in st.items():
            stat[k] += v
    silver = pd.concat(bagian, ignore_index=True)
    stat["baris_silver_ilo"] = len(silver)
    stat["rincian_ilo"] = int(silver["rincian"].nunique())
    stat["status_obs_terisi"] = int(silver["status_obs"].notna().sum())
    return silver, stat