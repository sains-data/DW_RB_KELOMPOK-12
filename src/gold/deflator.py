"""Deflator upah (Tahap 4, Gold): IHK tahunan -> upah riil. Upah nominal di Silver TIDAK berubah (K-009).

Masukan opsional: data/ref/ihk_tahunan.csv dengan kolom
    wilayah_kode  : kode provinsi (kode BPS x 100) atau 9999 untuk IHK nasional
    tahun         : empat digit
    ihk           : angka indeks apa adanya dari sumber (basis boleh apa saja)
    sumber        : keterangan sumber (judul tabel BPS + tanggal akses)
Aturan: tiap wilayah di-rebase sendiri sehingga IHK tahun dasar = 100. Provinsi tanpa deretan IHK
sendiri memakai IHK nasional (9999) dan ditandai ihk_cakupan = 'nasional'. Tanpa berkas ini upah
riil dibiarkan kosong (bukan diisi angka karangan) dan pipeline tetap berjalan dengan peringatan.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.silver.wilayah import INDONESIA

JALUR_IHK = Path("data/ref/ihk_tahunan.csv")
TAHUN_DASAR = 2022  # harga konstan 2022; ubah bila deretan IHK Anda memakai tahun lain
KOLOM_IHK = ["wilayah_kode", "tahun", "ihk", "sumber"]
KOLOM_HASIL = ["ihk_dasar100", "ihk_cakupan", "ihk_sumber"]


def muat_ihk(jalur: Path = JALUR_IHK) -> pd.DataFrame | None:
    """Baca dan periksa berkas IHK. None bila berkas tidak ada."""
    jalur = Path(jalur)
    if not jalur.exists():
        return None
    d = pd.read_csv(jalur)
    kurang = [k for k in KOLOM_IHK if k not in d.columns]
    if kurang:
        raise ValueError(f"{jalur}: kolom {kurang} tidak ada. Kolom wajib: {KOLOM_IHK}")
    d = d[KOLOM_IHK].copy()
    d["wilayah_kode"] = d["wilayah_kode"].astype(int)
    d["tahun"] = d["tahun"].astype(int)
    d["ihk"] = pd.to_numeric(d["ihk"], errors="raise")
    if (d["ihk"] <= 0).any():
        raise ValueError(f"{jalur}: ada nilai ihk <= 0")
    if d.duplicated(["wilayah_kode", "tahun"]).any():
        raise ValueError(f"{jalur}: ada pasangan (wilayah_kode, tahun) kembar")
    return d


def _rebase(ihk: pd.DataFrame, tahun_dasar: int) -> pd.DataFrame:
    dasar = ihk.loc[ihk["tahun"] == tahun_dasar].set_index("wilayah_kode")["ihk"]
    tanpa_dasar = sorted(set(ihk["wilayah_kode"]) - set(dasar.index))
    if tanpa_dasar:
        print(f"PERINGATAN IHK: wilayah {tanpa_dasar} tidak punya IHK tahun dasar {tahun_dasar}; deretan itu diabaikan.")
    ihk = ihk[ihk["wilayah_kode"].isin(dasar.index)].copy()
    ihk["ihk_dasar100"] = ihk["ihk"] / ihk["wilayah_kode"].map(dasar) * 100
    return ihk


def tambah_riil(panel: pd.DataFrame, ihk: pd.DataFrame | None, tahun_dasar: int = TAHUN_DASAR) -> pd.DataFrame:
    """Tambah ihk_dasar100, ihk_cakupan, ihk_sumber, upah_riil_rp_jam, log_upah_riil pada baris upah."""
    p = panel.copy()
    adalah_upah = p["seri_kode"] == "var1172"
    p["ihk_dasar100"] = np.nan
    p["ihk_cakupan"] = pd.Series(pd.NA, index=p.index, dtype="string")
    p["ihk_sumber"] = pd.Series(pd.NA, index=p.index, dtype="string")

    if ihk is not None and not ihk.empty:
        r = _rebase(ihk, tahun_dasar)
        prov = r[r["wilayah_kode"] != INDONESIA][["wilayah_kode", "tahun", "ihk_dasar100", "sumber"]]
        nas = r[r["wilayah_kode"] == INDONESIA][["tahun", "ihk_dasar100", "sumber"]]
        prov = prov.rename(columns={"ihk_dasar100": "_ihk_p", "sumber": "_sum_p"})
        nas = nas.rename(columns={"ihk_dasar100": "_ihk_n", "sumber": "_sum_n"})
        m = p.drop(columns=KOLOM_HASIL).merge(prov, on=["wilayah_kode", "tahun"], how="left")
        m = m.merge(nas, on="tahun", how="left")
        pakai_p = m["_ihk_p"].notna()
        pakai_n = ~pakai_p & m["_ihk_n"].notna()
        m["ihk_dasar100"] = m["_ihk_p"].where(pakai_p, m["_ihk_n"])
        cak = pd.Series(pd.NA, index=m.index, dtype="string")
        cak = cak.mask(pakai_p, "provinsi").mask(pakai_n, "nasional")
        m["ihk_cakupan"] = cak
        m["ihk_sumber"] = m["_sum_p"].where(pakai_p, m["_sum_n"]).astype("string")
        p = m.drop(columns=["_ihk_p", "_sum_p", "_ihk_n", "_sum_n"])
        adalah_upah = p["seri_kode"] == "var1172"

    for k in KOLOM_HASIL:  # IHK hanya relevan untuk baris upah
        p[k] = p[k].where(adalah_upah)
    p["upah_riil_rp_jam"] = p["upah_nominal_rp_jam"] * 100 / p["ihk_dasar100"]
    p["log_upah_riil"] = np.log(p["upah_riil_rp_jam"].where(p["upah_riil_rp_jam"] > 0))
    return p