"""Tahap 4-6 - Reshape, integrasi, dan penyimpanan ke Gold. Milik tim."""
from pathlib import Path
import pandas as pd

from .aturan_gold import bangun_gold_dari_silver
from .tabel_nasional import bangun_tabel_nasional_gold


def jalankan(df_silver: pd.DataFrame) -> dict[str, pd.DataFrame]:
    df_gold, _ = bangun_gold_dari_silver(
        df_silver=df_silver,
        path_log="log-keputusan.csv",
    )

    path_panel = Path("data/gold/panel.parquet")
    path_panel.parent.mkdir(parents=True, exist_ok=True)
    df_gold.to_parquet(path_panel, index=False)

    tabel_nasional, rekonsiliasi = bangun_tabel_nasional_gold(df_silver=df_silver)
    return {
        "panel": df_gold,
        "tabel_nasional_gold": tabel_nasional,
        "rekonsiliasi_nasional": rekonsiliasi,
    }