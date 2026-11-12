from __future__ import annotations

import pandas as pd
from src.ekstraksi.bps import baca_semua_bps
from src.ekstraksi.ilostat import baca_semua_ilostat


def jalankan() -> pd.DataFrame:
    """Menggabungkan seluruh pembaca BPS dan ILOSTAT menjadi satu tabel panjang ber-lineage."""
    daftar_df: list[pd.DataFrame] = []
    daftar_df.extend(baca_semua_bps())
    daftar_df.extend(baca_semua_ilostat())

    df_mentah = pd.concat(daftar_df, ignore_index=True)

    ringkasan = (
        df_mentah.groupby(["sumber", "_berkas_raw"], dropna=False)
        .size()
        .reset_index(name="baris_mentah")
    )
    print("=== RINGKASAN EKSTRAKSI (TAHAP 1) ===")
    print(ringkasan.to_string(index=False))
    print(f"Total berkas data dibaca : {len(ringkasan)}")
    print(f"Total baris mentah       : {len(df_mentah)}")

    return df_mentah