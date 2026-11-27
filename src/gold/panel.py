"""Tahap 4 - Panel Gold provinsi x periode x indikator untuk seri utama var1172 dan var2153.

Satu baris = satu sel (provinsi, tahun, seri). Aturan sel memakai K-018..K-020 (aturan_gold.py):
rincian 'total', jenis periode 'tahun', satu baris per sel. Satuan tidak dicampur: tiap besaran punya
kolom sendiri (upah_nominal_rp_jam hanya terisi pada var1172, informal_persen hanya pada var2153).
Nilai asli dari Silver tidak diubah; log dan upah riil adalah kolom tambahan.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.silver.wilayah import BERDIRI, INDONESIA, KODE_PROVINSI, NAMA_PROVINSI

from .aturan_gold import pilih_periode_panel, pilih_rincian_panel, pilih_snapshot_panel
from .deflator import TAHUN_DASAR, muat_ihk, tambah_riil

EKSTENSI_KANONIK = ".csv"  # K-005: CSV kanonik, JSON hanya uji silang
KUNCI_PANEL = ["wilayah_kode", "periode", "seri_kode"]

SERI_PANEL = {
    "var1172": dict(indikator="upah_per_jam", satuan="rupiah_per_jam", kolom="upah_nominal_rp_jam"),
    "var2153": dict(indikator="proporsi_informal", satuan="persen", kolom="informal_persen"),
}
BATAS_WAJAR = {"rupiah_per_jam": (1_000, 200_000), "persen": (0, 100)}  # sama dengan katalog.py
KOLOM_NILAI = [v["kolom"] for v in SERI_PANEL.values()]

KOLOM_PANEL = [
    "wilayah_kode", "nama_wilayah", "periode", "tahun", "seri_kode", "indikator", "satuan",
    "upah_nominal_rp_jam", "informal_persen",
    "upah_riil_rp_jam", "log_upah_nominal", "log_upah_riil",
    "ihk_dasar100", "ihk_cakupan", "ihk_sumber",
    "status_sel", "outlier_ekstrem", "status_obs",
    "silver_row_id", "silver_berkas_raw", "silver_sha256_raw",
]


def _seleksi_silver(silver: pd.DataFrame) -> tuple[pd.DataFrame, list[dict], dict]:
    """Terapkan K-018..K-020 pada Silver. CSV kanonik dipilih eksplisit dulu agar pilihan CSV vs JSON deterministik."""
    s = silver.reset_index(drop=True).copy()
    s["silver_row_id"] = np.arange(len(s))  # urutan Silver tetap (diurutkan menurut kunci), jadi id stabil
    stat = {"baris_silver": len(s)}

    kan = s[s["_berkas_raw"].str.endswith(EKSTENSI_KANONIK)]
    stat["baris_bukan_kanonik"] = len(s) - len(kan)
    logs: list[dict] = []
    a = pilih_rincian_panel(kan, logs=logs)
    b = pilih_periode_panel(a, logs=logs)
    c = pilih_snapshot_panel(b, logs=logs)

    c = c[(c["sumber"] == "bps") & c["seri_kode"].isin(SERI_PANEL)]
    stat["baris_bps_pilihan"] = len(c)
    stat["baris_nasional_dikeluarkan"] = int((c["wilayah_kode"] == INDONESIA).sum())  # K-006
    c = c[c["wilayah_kode"] != INDONESIA]
    return c, logs, stat


def _periksa_satuan(d: pd.DataFrame) -> None:
    for seri, cfg in SERI_PANEL.items():
        x = d[d["seri_kode"] == seri]
        if x.empty:
            raise ValueError(f"Seri {seri} tidak ada di Silver terpilih.")
        if set(x["satuan"]) != {cfg["satuan"]}:
            raise ValueError(f"{seri}: satuan di Silver {sorted(set(x['satuan']))} != {cfg['satuan']}")
        lo, hi = BATAS_WAJAR[cfg["satuan"]]
        if not x["nilai"].between(lo, hi).all():
            raise ValueError(f"{seri}: ada nilai di luar {lo}..{hi} untuk satuan {cfg['satuan']}")


def _grid_diharapkan(d: pd.DataFrame) -> pd.DataFrame:
    """Sel provinsi x tahun yang diharapkan ada (tahun pertama..terakhir seri, mulai tahun provinsi berdiri)."""
    bagian = []
    for seri in SERI_PANEL:
        thn = d.loc[d["seri_kode"] == seri, "periode"].astype(int)
        g = pd.MultiIndex.from_product([KODE_PROVINSI, range(thn.min(), thn.max() + 1)],
                                       names=["wilayah_kode", "tahun"]).to_frame(index=False)
        g = g[g["tahun"] >= g["wilayah_kode"].map(BERDIRI).fillna(0)]
        g["seri_kode"] = seri
        bagian.append(g)
    return pd.concat(bagian, ignore_index=True)


def bangun_panel(silver: pd.DataFrame, tahun_dasar: int = TAHUN_DASAR, ihk: pd.DataFrame | None = None
                 ) -> tuple[pd.DataFrame, list[dict], dict]:
    """Bangun panel Gold (format panjang). Mengembalikan (panel, log aturan, statistik)."""
    d, logs, stat = _seleksi_silver(silver)
    _periksa_satuan(d)
    d = d.assign(tahun=d["periode"].astype(int))

    grid = _grid_diharapkan(d)
    p = grid.merge(
        d[["wilayah_kode", "tahun", "seri_kode", "nilai", "outlier_ekstrem", "status_obs",
           "silver_row_id", "_berkas_raw", "_sha256_raw"]],
        on=["wilayah_kode", "tahun", "seri_kode"], how="left", validate="one_to_one")
    for seri in SERI_PANEL:  # setiap observasi Silver harus jatuh di sel yang diharapkan
        n_silver = int((d["seri_kode"] == seri).sum())
        n_panel = int(p.loc[p["seri_kode"] == seri, "nilai"].notna().sum())
        if n_silver != n_panel:
            raise ValueError(f"{seri}: {n_silver} observasi Silver tetapi {n_panel} masuk grid (ada sel di luar grid).")

    p["nama_wilayah"] = p["wilayah_kode"].map(NAMA_PROVINSI)
    p["periode"] = p["tahun"].astype(str)
    p["indikator"] = p["seri_kode"].map({k: v["indikator"] for k, v in SERI_PANEL.items()})
    p["satuan"] = p["seri_kode"].map({k: v["satuan"] for k, v in SERI_PANEL.items()})
    for seri, cfg in SERI_PANEL.items():  # satu kolom nilai per satuan, tidak dicampur
        p[cfg["kolom"]] = p["nilai"].where(p["seri_kode"] == seri)
    p["log_upah_nominal"] = np.log(p["upah_nominal_rp_jam"].where(p["upah_nominal_rp_jam"] > 0))
    p["status_sel"] = np.where(p["nilai"].notna(), "terisi", "belum_disurvei")  # K-008: tidak diimputasi
    p["outlier_ekstrem"] = p["outlier_ekstrem"].fillna(False).astype(bool)
    p["status_obs"] = p["status_obs"].astype("string")
    p["silver_row_id"] = p["silver_row_id"].astype("Int64")
    p = p.rename(columns={"_berkas_raw": "silver_berkas_raw", "_sha256_raw": "silver_sha256_raw"})

    if ihk is None:
        ihk = muat_ihk()
    p = tambah_riil(p, ihk, tahun_dasar)
    p = p[KOLOM_PANEL].sort_values(["seri_kode", "wilayah_kode", "tahun"]).reset_index(drop=True)

    if p.duplicated(KUNCI_PANEL).any():
        raise ValueError(f"Kunci panel kembar: {int(p.duplicated(KUNCI_PANEL).sum())} baris")
    stat.update(
        baris_gold=len(p), seri_panel=int(p["seri_kode"].nunique()),
        sel_terisi=int((p["status_sel"] == "terisi").sum()),
        sel_kosong=int((p["status_sel"] != "terisi").sum()),
        riil_terisi=int(p["upah_riil_rp_jam"].notna().sum()),
        ihk_ada=ihk is not None, tahun_dasar=tahun_dasar,
    )
    return p, logs, stat


def bentuk_lebar(panel: pd.DataFrame) -> pd.DataFrame:
    """Turunan format lebar: satu baris = provinsi x tahun. Untuk analisis/SQL; sumber kebenaran tetap panel panjang."""
    u = panel[panel["seri_kode"] == "var1172"][
        ["wilayah_kode", "periode", "tahun", "upah_nominal_rp_jam", "upah_riil_rp_jam",
         "log_upah_nominal", "log_upah_riil"]]
    i = panel[panel["seri_kode"] == "var2153"][["wilayah_kode", "periode", "tahun", "informal_persen"]]
    w = u.merge(i, on=["wilayah_kode", "periode", "tahun"], how="outer")
    w["nama_wilayah"] = w["wilayah_kode"].map(NAMA_PROVINSI)
    kolom = ["wilayah_kode", "nama_wilayah", "periode", "tahun", "upah_nominal_rp_jam", "upah_riil_rp_jam",
             "log_upah_nominal", "log_upah_riil", "informal_persen"]
    return w[kolom].sort_values(["wilayah_kode", "tahun"]).reset_index(drop=True)