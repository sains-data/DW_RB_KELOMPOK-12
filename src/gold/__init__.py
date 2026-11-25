from pathlib import Path
import pandas as pd
from .aturan_gold import bangun_gold_dari_silver

"""Tahap 4-6 - Reshape, integrasi, dan penyimpanan ke Gold. Milik tim."""

from src.gold.tabel_nasional import bangun_tabel_nasional_gold

def jalankan(df_silver: pd.DataFrame) -> pd.DataFrame:
    df_gold, _ = bangun_gold_dari_silver(
        df_silver=df_silver,
        path_log="log-keputusan.csv",
    )

    path_out = Path("data/gold/panel.parquet")
    path_out.parent.mkdir(parents=True, exist_ok=True)
    df_gold.to_parquet(path_out, index=False)
    return df_gold
  
def jalankan(silver=None):
    """Bangun tabel Gold dan kembalikan kamus {nama_tabel: DataFrame}."""
    tabel_nasional = bangun_tabel_nasional_gold()
    return {"tabel_nasional_gold": tabel_nasional}
