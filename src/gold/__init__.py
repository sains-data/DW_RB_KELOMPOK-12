<<<<<<< HEAD
﻿from pathlib import Path
import pandas as pd

from .aturan_gold import bangun_gold_dari_silver
from . import rekonsiliasi_nasional as _rek
=======
"""Tahap 4-6 - Reshape, integrasi, dan penyimpanan ke Gold. Milik tim."""
from pathlib import Path
import pandas as pd

from .aturan_gold import bangun_gold_dari_silver
from .tabel_nasional import bangun_tabel_nasional_gold
>>>>>>> origin/main


<<<<<<< HEAD

def _bangun_panel_lebar(df_gold: pd.DataFrame) -> pd.DataFrame:
    kol_idx = [k for k in ["wilayah_kode", "nama_wilayah", "periode", "jenis_periode", "rincian"] if k in df_gold.columns]
    kol_seri = "seri_kode" if "seri_kode" in df_gold.columns else ("indikator" if "indikator" in df_gold.columns else None)
    kol_nilai = "nilai" if "nilai" in df_gold.columns else ("nilai_bersih" if "nilai_bersih" in df_gold.columns else None)
    if not kol_idx or not kol_seri or not kol_nilai:
        return df_gold.copy()
    lebar = df_gold.pivot_table(index=kol_idx, columns=kol_seri, values=kol_nilai, aggfunc="first").reset_index()
    lebar.columns.name = None
    return lebar


def _bangun_nasional(df_gold: pd.DataFrame) -> pd.DataFrame:
    if "wilayah_kode" not in df_gold.columns:
        return df_gold.copy()
    return df_gold[df_gold["wilayah_kode"] == 9999].copy()


def _bangun_rekonsiliasi(df_silver: pd.DataFrame, df_gold: pd.DataFrame, df_nasional: pd.DataFrame) -> pd.DataFrame:
    for nama_fungsi in [
        "bangun_rekonsiliasi_nasional",
        "rekonsiliasi_nasional",
        "bangun_rekonsiliasi",
        "jalankan",
    ]:
        fn = getattr(_rek, nama_fungsi, None)
        if callable(fn):
            try:
                res = fn(df_silver, df_gold, df_nasional)
            except TypeError:
                try:
                    res = fn(df_silver, df_gold)
                except TypeError:
                    try:
                        res = fn(df_gold)
                    except TypeError:
                        res = fn(df_silver)
            if isinstance(res, dict):
                for v in res.values():
                    if isinstance(v, pd.DataFrame):
                        return v
            if isinstance(res, pd.DataFrame):
                return res
    return df_nasional.copy()


def jalankan(df_silver: pd.DataFrame) -> pd.DataFrame:
    out_dir = Path("data/gold")
    out_dir.mkdir(parents=True, exist_ok=True)

=======
def jalankan(df_silver: pd.DataFrame) -> dict[str, pd.DataFrame]:
>>>>>>> origin/main
    df_gold, _ = bangun_gold_dari_silver(
        df_silver=df_silver,
        path_log="log-keputusan.csv",
    )
    df_gold.to_parquet(out_dir / "panel.parquet", index=False)

    df_lebar = _bangun_panel_lebar(df_gold)
    df_lebar.to_parquet(out_dir / "panel_lebar.parquet", index=False)

    df_nasional = _bangun_nasional(df_gold)
    df_nasional.to_parquet(out_dir / "nasional.parquet", index=False)

    df_rekonsiliasi = _bangun_rekonsiliasi(df_silver, df_gold, df_nasional)
    df_rekonsiliasi.to_parquet(out_dir / "rekonsiliasi.parquet", index=False)

<<<<<<< HEAD
    return df_gold
=======
    path_panel = Path("data/gold/panel.parquet")
    path_panel.parent.mkdir(parents=True, exist_ok=True)
    df_gold.to_parquet(path_panel, index=False)

    tabel_nasional, rekonsiliasi = bangun_tabel_nasional_gold(df_silver=df_silver)
    return {
        "panel": df_gold,
        "tabel_nasional_gold": tabel_nasional,
        "rekonsiliasi_nasional": rekonsiliasi,
    }
>>>>>>> origin/main
