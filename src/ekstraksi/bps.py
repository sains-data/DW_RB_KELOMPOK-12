from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from src.common.manifest import sha256_raw

RAW_DIR = Path("data/raw")

BERKAS_BPS_CSV = [
    "bps/2026-10-17/sdg8_upah.csv",
    "bps/2026-10-17/sdg8_informal.csv",
]

BERKAS_BPS_JSON = [
    "bps/2026-10-17/json/sdg8_upah.json",
    "bps/2026-10-17/json/sdg8_informal.json",
]


def _tempel_lineage(df: pd.DataFrame, berkas_relatif: str) -> pd.DataFrame:
    df = df.copy()
    df["sumber"] = "bps"
    df["_berkas_raw"] = berkas_relatif
    df["_sha256_raw"] = sha256_raw(berkas_relatif)
    return df


def _ke_peta_kode(daftar: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(daftar, list):
        return {"": {"label": "", "unit": None}}
    hasil: dict[str, dict[str, Any]] = {}
    for item in daftar:
        if isinstance(item, dict) and "val" in item:
            hasil[str(item["val"])] = {
                "label": str(item.get("label", "")),
                "unit": item.get("unit"),
            }
    return hasil if hasil else {"": {"label": "", "unit": None}}


def _urai_kunci_bps(
    kunci: str,
    peta_vervar: dict[str, dict[str, Any]],
    peta_var: dict[str, dict[str, Any]],
    peta_turvar: dict[str, dict[str, Any]],
    peta_tahun: dict[str, dict[str, Any]],
    peta_turtahun: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Memecah kunci gabungan datacontent BPS berdasarkan daftar kode (bukan posisi tetap)."""
    for kv, iv in peta_vervar.items():
        if not kunci.startswith(kv):
            continue
        sisa1 = kunci[len(kv) :]
        for kvar, ivar in peta_var.items():
            if not sisa1.startswith(kvar):
                continue
            sisa2 = sisa1[len(kvar) :]
            for ktv, itv in peta_turvar.items():
                if not sisa2.startswith(ktv):
                    continue
                sisa3 = sisa2[len(ktv) :]
                for kth, ith in peta_tahun.items():
                    if not sisa3.startswith(kth):
                        continue
                    ktth = sisa3[len(kth) :]
                    if ktth in peta_turtahun:
                        itth = peta_turtahun[ktth]
                        return {
                            "var_id": kvar,
                            "wilayah_id": kv,
                            "wilayah": iv["label"],
                            "turvar_id": ktv,
                            "turvar": itv["label"],
                            "tahun_id": kth,
                            "tahun": ith["label"],
                            "periode_id": ktth,
                            "periode": itth["label"],
                            "satuan": ivar["unit"],
                        }
    return {"kunci_mentah": kunci}


def _baca_halaman_json_bps(obj: dict[str, Any]) -> pd.DataFrame:
    datacontent = obj.get("datacontent")
    if not isinstance(datacontent, dict):
        return pd.DataFrame()

    peta_vervar = _ke_peta_kode(obj.get("vervar"))
    peta_var = _ke_peta_kode(obj.get("var"))
    peta_turvar = _ke_peta_kode(obj.get("turvar"))
    peta_tahun = _ke_peta_kode(obj.get("tahun"))
    peta_turtahun = _ke_peta_kode(obj.get("turtahun"))

    baris: list[dict[str, Any]] = []
    for kunci, nilai in datacontent.items():
        rekaman = _urai_kunci_bps(
            str(kunci),
            peta_vervar,
            peta_var,
            peta_turvar,
            peta_tahun,
            peta_turtahun,
        )
        rekaman["nilai"] = None if nilai is None else str(nilai)
        baris.append(rekaman)

    return pd.DataFrame(baris)


def baca_bps_csv(berkas_relatif: str) -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / berkas_relatif, dtype=str)
    return _tempel_lineage(df, berkas_relatif)


def baca_bps_json(berkas_relatif: str) -> pd.DataFrame:
    with (RAW_DIR / berkas_relatif).open("r", encoding="utf-8") as f:
        konten = json.load(f)

    if isinstance(konten, list):
        potongan = [_baca_halaman_json_bps(hal) for hal in konten if isinstance(hal, dict)]
        df = pd.concat(potongan, ignore_index=True) if potongan else pd.DataFrame()
    elif isinstance(konten, dict):
        df = _baca_halaman_json_bps(konten)
    else:
        df = pd.DataFrame()

    return _tempel_lineage(df, berkas_relatif)


def baca_semua_bps() -> list[pd.DataFrame]:
    hasil: list[pd.DataFrame] = []
    for berkas in BERKAS_BPS_CSV:
        hasil.append(baca_bps_csv(berkas))
    for berkas in BERKAS_BPS_JSON:
        hasil.append(baca_bps_json(berkas))
    return hasil