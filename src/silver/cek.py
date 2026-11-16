"""Pemeriksaan mandiri Sprint 1 (tidak mengubah data):  python -m src.silver.cek [jalur.parquet]"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from src.common.skema import KUNCI, periksa_silver

SERI_DIHARAPKAN = {"var1172", "var2153", "SDG_0851_SEX_OCU_NB", "SDG_0831_SEX_ECO_RT"}
BARIS_BPS_REFERENSI = 1362  # Silver BPS sebelum Sprint 1 (681 kunci x CSV dan JSON)


def main():
    jalur = Path(sys.argv[1] if len(sys.argv) > 1 else "data/silver/silver.parquet")
    df = pd.read_parquet(jalur)
    try:
        from src.common.manifest import baca
        manifest = baca()
    except FileNotFoundError:
        manifest = None
        print("PERINGATAN MANIFEST.csv tidak ada; lineage tidak diperiksa.")

    gagal = [f"skema: {s}" for s in periksa_silver(df, manifest)]
    if df.duplicated(KUNCI).any():
        gagal.append(f"kunci kembar: {int(df.duplicated(KUNCI).sum())} baris")
    seri = set(df["seri_kode"])
    if seri != SERI_DIHARAPKAN:
        gagal.append(f"seri tidak sesuai harapan. kurang: {sorted(SERI_DIHARAPKAN - seri)}, lebih: {sorted(seri - SERI_DIHARAPKAN)}")
    ilo = df[df["sumber"] == "ilostat"]
    if not ilo.empty and set(ilo["wilayah_kode"]) != {9999}:
        gagal.append(f"baris ILOSTAT punya wilayah_kode selain 9999: {sorted(set(ilo['wilayah_kode']))}")
    n_bps = int((df["sumber"] == "bps").sum())
    if n_bps != BARIS_BPS_REFERENSI:
        print(f"PERINGATAN baris BPS {n_bps} != {BARIS_BPS_REFERENSI}. Pastikan perubahan ini memang disengaja.")

    print(f"baris per sumber/seri:\n{df.groupby(['sumber', 'seri_kode']).size().to_string()}")
    print(f"rincian unik per sumber: {df.groupby('sumber')['rincian'].nunique().to_dict()}")
    print(f"status_obs: {df['status_obs'].value_counts(dropna=True).to_dict()}")
    for g in gagal:
        print(f"GAGAL  {g}")
    if gagal:
        sys.exit(1)
    print(f"\nLOLOS semua pemeriksaan. Perintah bukti artefak:\n"
          f"python -m src.common.hasil 124450102 seri_silver={df['seri_kode'].nunique()} "
          f"rincian_dienkode={df['rincian'].nunique()} baris_silver={len(df)}")


if __name__ == "__main__":
    main()