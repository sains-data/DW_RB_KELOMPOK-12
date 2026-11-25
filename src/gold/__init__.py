from pathlib import Path
import pandas as pd
from .aturan_gold import bangun_gold_dari_silver


def jalankan(df_silver: pd.DataFrame) -> pd.DataFrame:
    df_gold, _ = bangun_gold_dari_silver(
        df_silver=df_silver,
        path_log="log-keputusan.csv",
    )

    path_out = Path("data/gold/panel.parquet")
    path_out.parent.mkdir(parents=True, exist_ok=True)
    df_gold.to_parquet(path_out, index=False)
    return df_gold
