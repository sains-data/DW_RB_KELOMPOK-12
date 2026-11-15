"""Grid provinsi x periode x rincian, kelengkapan panel, penanda ekstrem, dan uji silang format."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .wilayah import BERDIRI, INDONESIA, KODE_PROVINSI

EKSTENSI_KANONIK = ".csv"  # sumber kanonik Silver untuk grid; JSON dipakai sebagai uji silang


def pilih_kanonik(silver: pd.DataFrame) -> pd.DataFrame:
    return silver[silver["_berkas_raw"].str.endswith(EKSTENSI_KANONIK)]


def tandai_ekstrem(silver: pd.DataFrame, faktor: float = 1.5, min_provinsi: int = 8) -> pd.DataFrame:
    """Tandai provinsi ekstrem per seri x periode x berkas dengan aturan IQR. Tidak mengubah nilai.

    Upah (rupiah_per_jam) menceng, jadi IQR dihitung pada log(nilai); proporsi (persen) pada nilainya.
    Baris Indonesia (9999) tidak ikut dihitung dan tidak ditandai.
    """
    df = silver.copy()
    df["outlier_ekstrem"] = False
    prov = df["wilayah_kode"] != INDONESIA
    sub = df[prov].copy()
    positif = sub["nilai"] > 0
    sub["_x"] = np.where((sub["satuan"] == "rupiah_per_jam") & positif, np.log(sub["nilai"].where(positif)), sub["nilai"])
    kunci = ["seri_kode", "periode", "_berkas_raw"]
    g = sub.groupby(kunci)["_x"]
    q1 = g.transform(lambda s: s.quantile(0.25))
    q3 = g.transform(lambda s: s.quantile(0.75))
    n = g.transform("count")
    iqr = q3 - q1
    flag = ((sub["_x"] < q1 - faktor * iqr) | (sub["_x"] > q3 + faktor * iqr)) & (n >= min_provinsi)
    df.loc[sub.index, "outlier_ekstrem"] = flag.values
    return df


def bentuk_grid(silver: pd.DataFrame) -> pd.DataFrame:
    """Grid lengkap 38 provinsi x tahun (dari tahun pertama sampai terakhir seri itu) x rincian.

    Kolom `diharapkan` False untuk sel sebelum provinsi pemekaran berdiri; `nilai` kosong bila belum ada.
    Tahun sebelum seri terbit tidak masuk grid, jadi bukan missing.
    """
    s = pilih_kanonik(silver)
    s = s[s["wilayah_kode"] != INDONESIA]
    bagian = []
    for seri, d in s.groupby("seri_kode"):
        tahun = d["periode"].astype(int)
        rentang = [str(t) for t in range(tahun.min(), tahun.max() + 1)]
        rincian = sorted(d["rincian"].unique())
        idx = pd.MultiIndex.from_product(
            [[seri], KODE_PROVINSI, rentang, rincian],
            names=["seri_kode", "wilayah_kode", "periode", "rincian"],
        )
        g = idx.to_frame(index=False)
        g = g.merge(
            d[["seri_kode", "wilayah_kode", "periode", "rincian", "nilai"]],
            on=["seri_kode", "wilayah_kode", "periode", "rincian"],
            how="left",
        )
        bagian.append(g)
    grid = pd.concat(bagian, ignore_index=True)
    grid["diharapkan"] = grid.apply(lambda r: int(r["periode"]) >= BERDIRI.get(r["wilayah_kode"], 0), axis=1)
    return grid


def kelengkapan(grid: pd.DataFrame) -> pd.DataFrame:
    """Persen sel terisi per seri x periode (terhadap sel yang diharapkan, dan terhadap 38 provinsi)."""
    g = grid.assign(
        terisi=grid["nilai"].notna(),
        terisi_diharapkan=grid["nilai"].notna() & grid["diharapkan"],
    )
    t = g.groupby(["seri_kode", "periode"]).agg(
        sel_grid=("nilai", "size"),
        sel_diharapkan=("diharapkan", "sum"),
        sel_terisi=("terisi", "sum"),
        sel_terisi_diharapkan=("terisi_diharapkan", "sum"),
    ).reset_index()
    t["persen_terisi_diharapkan"] = (100 * t["sel_terisi_diharapkan"] / t["sel_diharapkan"]).round(1)
    t["persen_terisi_dari_38"] = (100 * t["sel_terisi"] / t["sel_grid"]).round(1)
    return t


def sel_kosong_diharapkan(grid: pd.DataFrame) -> pd.DataFrame:
    return grid[grid["nilai"].isna() & grid["diharapkan"]].copy()


def bandingkan_format(silver: pd.DataFrame) -> dict:
    """Uji silang CSV vs JSON BPS pada kunci yang sama (K-002 mengklaim keduanya sama)."""
    s = silver.copy()
    s["_stem"] = s["_berkas_raw"].map(lambda p: Path(p).stem)
    s["_fmt"] = s["_berkas_raw"].map(lambda p: Path(p).suffix.lower())
    kunci = ["_stem", "seri_kode", "wilayah_kode", "periode", "rincian"]
    a = s[s["_fmt"] == ".csv"][kunci + ["nilai"]]
    b = s[s["_fmt"] == ".json"][kunci + ["nilai"]]
    m = a.merge(b, on=kunci, how="outer", suffixes=("_csv", "_json"), indicator=True)
    sama = m["_merge"] == "both"
    beda = sama & ~np.isclose(m["nilai_csv"], m["nilai_json"], equal_nan=True)
    return {
        "baris_csv": len(a),
        "baris_json": len(b),
        "kunci_sama": int(sama.sum()),
        "hanya_csv": int((m["_merge"] == "left_only").sum()),
        "hanya_json": int((m["_merge"] == "right_only").sum()),
        "nilai_berbeda": int(beda.sum()),
    }