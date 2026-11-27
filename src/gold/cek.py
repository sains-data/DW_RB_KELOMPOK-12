"""Pemeriksaan mandiri Tahap 4 (tidak mengubah data):  python -m src.gold.cek"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.manifest import baca
from src.gold.panel import KOLOM_NILAI, KOLOM_PANEL, KUNCI_PANEL, SERI_PANEL

JALUR_SILVER = Path("data/silver/silver.parquet")
JALUR_PANEL = Path("data/gold/panel_provinsi_sdg8.parquet")
JALUR_KOSONG = Path("reports/sel_kosong_grid.csv")


def periksa(silver: pd.DataFrame, panel: pd.DataFrame, kosong: pd.DataFrame | None, manifest: dict | None):
    gagal, info = [], []
    kurang = [k for k in KOLOM_PANEL if k not in panel.columns]
    if kurang:
        return [f"kolom panel tidak ada: {kurang}"], info

    # 1. kunci tidak kembar (juga untuk pasangan wilayah x periode x indikator)
    for kunci in (KUNCI_PANEL, ["wilayah_kode", "periode", "indikator"]):
        n = int(panel.duplicated(kunci).sum())
        if n:
            gagal.append(f"kunci kembar {kunci}: {n} baris")

    # 2. satu satuan per kolom nilai, tidak dicampur
    for seri, cfg in SERI_PANEL.items():
        x = panel[panel["seri_kode"] == seri]
        if set(x["satuan"]) != {cfg["satuan"]}:
            gagal.append(f"{seri}: satuan {sorted(set(x['satuan']))} != {cfg['satuan']}")
        lain = [k for k in KOLOM_NILAI if k != cfg["kolom"]]
        if x[lain].notna().any().any():
            gagal.append(f"{seri}: kolom {lain} terisi pada baris seri ini (satuan tercampur)")
    if panel.loc[panel["seri_kode"] != "var1172", ["upah_riil_rp_jam", "log_upah_nominal", "log_upah_riil"]].notna().any().any():
        gagal.append("kolom turunan upah terisi pada baris bukan upah")

    # 3. keterlacakan: tiap sel terisi menunjuk satu baris Silver yang cocok
    t = panel[panel["status_sel"] == "terisi"].reset_index(drop=True)
    if t["silver_row_id"].isna().any():
        gagal.append("ada sel terisi tanpa silver_row_id")
    else:
        ids = t["silver_row_id"].astype(int)
        if ids.min() < 0 or ids.max() >= len(silver):
            gagal.append("silver_row_id di luar rentang baris Silver")
        else:
            s = silver.iloc[ids].reset_index(drop=True)
            cocok = ((s["wilayah_kode"] == t["wilayah_kode"]) & (s["periode"].astype(str) == t["periode"])
                     & (s["seri_kode"] == t["seri_kode"]) & (s["sumber"] == "bps") & (s["rincian"] == "total")
                     & (s["satuan"] == t["satuan"]) & (s["_berkas_raw"] == t["silver_berkas_raw"])
                     & (s["_sha256_raw"] == t["silver_sha256_raw"]))
            nilai_gold = t["upah_nominal_rp_jam"].fillna(t["informal_persen"])
            cocok &= np.isclose(s["nilai"].astype(float), nilai_gold.astype(float))
            if not cocok.all():
                gagal.append(f"{int((~cocok).sum())} sel terisi tidak cocok dengan baris Silver asalnya")
            if ids.duplicated().any():
                gagal.append("dua sel Gold menunjuk baris Silver yang sama")
            if not s["_berkas_raw"].str.endswith(".csv").all():
                gagal.append("ada sel yang berasal dari berkas non-CSV (K-005 menetapkan CSV kanonik)")
    if manifest is not None:
        beda = [b for b, h in t[["silver_berkas_raw", "silver_sha256_raw"]].drop_duplicates().itertuples(index=False)
                if manifest.get(b) != h]
        if beda:
            gagal.append(f"sha256 berkas sumber tidak cocok dengan MANIFEST.csv: {beda[:3]}")

    # 4. sel kosong: tanpa silver_row_id, tanpa nilai, dan persis sama dengan laporan grid
    k = panel[panel["status_sel"] != "terisi"]
    if k["silver_row_id"].notna().any() or k[KOLOM_NILAI].notna().any().any():
        gagal.append("sel kosong memuat nilai atau silver_row_id (tidak boleh diimputasi)")
    if kosong is not None:
        a = set(zip(k["seri_kode"], k["wilayah_kode"], k["periode"]))
        b = set(zip(kosong["seri_kode"], kosong["wilayah_kode"].astype(int), kosong["periode"].astype(str)))
        if a != b:
            gagal.append(f"sel kosong Gold != reports/sel_kosong_grid.csv (hanya Gold: {len(a - b)}, hanya laporan: {len(b - a)})")

    # 5. penanda ekstrem dibawa dari Silver
    sil = silver[(silver["sumber"] == "bps") & silver["_berkas_raw"].str.endswith(".csv")
                 & (silver["wilayah_kode"] != 9999) & (silver["seri_kode"].isin(SERI_PANEL))]
    if int(panel["outlier_ekstrem"].sum()) != int(sil["outlier_ekstrem"].sum()):
        gagal.append(f"outlier Gold {int(panel['outlier_ekstrem'].sum())} != Silver {int(sil['outlier_ekstrem'].sum())}")

    info.append(f"baris Gold {len(panel)}; seri {panel['seri_kode'].nunique()}; terisi {len(t)}; kosong {len(k)}")
    info.append(f"outlier_ekstrem {int(panel['outlier_ekstrem'].sum())}; upah riil terisi {int(panel['upah_riil_rp_jam'].notna().sum())}")
    if panel["upah_riil_rp_jam"].notna().sum() == 0:
        info.append("PERINGATAN upah_riil_rp_jam kosong semua: berkas data/ref/ihk_tahunan.csv belum ada")
    return gagal, info


def main():
    silver = pd.read_parquet(JALUR_SILVER)
    panel = pd.read_parquet(JALUR_PANEL)
    kosong = pd.read_csv(JALUR_KOSONG) if JALUR_KOSONG.exists() else None
    try:
        manifest = baca()
    except FileNotFoundError:
        manifest = None
        print("PERINGATAN MANIFEST.csv tidak ada; lineage tidak diperiksa.")
    gagal, info = periksa(silver, panel, kosong, manifest)
    for i in info:
        print(i)
    for g in gagal:
        print(f"GAGAL  {g}")
    if gagal:
        sys.exit(1)
    print("\nLOLOS semua pemeriksaan. Perintah bukti artefak:")
    print(f"python -m src.common.hasil 124450102 seri_silver={silver['seri_kode'].nunique()} "
          f"rincian_dienkode={silver['rincian'].nunique()} baris_silver={len(silver)} "
          f"seri_panel={panel['seri_kode'].nunique()} baris_gold={len(panel)}")


if __name__ == "__main__":
    main()