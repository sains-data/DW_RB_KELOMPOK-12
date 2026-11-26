from pathlib import Path
import pandas as pd

from .aturan_gold import bangun_gold_dari_silver
from .tabel_nasional import bangun_tabel_nasional_gold


def jalankan(df_silver: pd.DataFrame) -> dict[str, pd.DataFrame]:
    df_panel, _ = bangun_gold_dari_silver(
        df_silver=df_silver,
        path_log="log-keputusan.csv",
    )

    path_out = Path("data/gold/panel.parquet")
    path_out.parent.mkdir(parents=True, exist_ok=True)
    df_panel.to_parquet(path_out, index=False)

    tabel_nasional = bangun_tabel_nasional_gold()
    return {
        "panel": df_panel,
        "tabel_nasional_gold": tabel_nasional,
    }