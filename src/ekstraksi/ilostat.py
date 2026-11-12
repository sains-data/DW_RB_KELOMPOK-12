from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from src.common.manifest import sha256_raw

RAW_DIR = Path("data/raw")
DATAFLOW_JSON = "ilostat/2026-10-20/metadata/dataflow.json"

PASANGAN_ILOSTAT = [
    {
        "data": "ilostat/2026-10-20/data/DF_SDG_0831_SEX_ECO_RT.csv",
        "dsd": "ilostat/2026-10-20/dsd/SDG_0831_SEX_ECO_RT.json",
    },
    {
        "data": "ilostat/2026-10-20/data/DF_SDG_0851_SEX_OCU_NB.csv",
        "dsd": "ilostat/2026-10-20/dsd/SDG_0851_SEX_OCU_NB.json",
    },
]

# Kamus label SDMX ILOSTAT untuk dimensi utama kasus 12
KAMUS_SDMX_ILO: dict[str, dict[str, str]] = {
    "SEX": {
        "SEX_T": "Total",
        "SEX_M": "Male",
        "SEX_F": "Female",
    },
    "ECO": {
        "ECO_SECTOR_TOTAL": "Total",
        "ECO_SECTOR_AGR": "Agriculture",
        "ECO_SECTOR_NAG": "Non-agriculture",
        "ECO_SECTOR_IND": "Industry",
        "ECO_SECTOR_SER": "Services",
        "ECO_AGGREGATE_TOTAL": "Total",
        "ECO_AGGREGATE_AGR": "Agriculture",
        "ECO_AGGREGATE_MAN": "Manufacturing",
        "ECO_AGGREGATE_CON": "Construction",
        "ECO_AGGREGATE_MEL": "Mining and quarrying; electricity, gas and water supply",
        "ECO_AGGREGATE_MKT": "Market services",
        "ECO_AGGREGATE_PUB": "Non-market services",
    },
    "OCU": {
        "OCU_SKILL_TOTAL": "Total (Skill level)",
        "OCU_SKILL_L3-4": "Skill levels 3 and 4 (high)",
        "OCU_SKILL_L2": "Skill level 2 (medium)",
        "OCU_SKILL_L1": "Skill level 1 (low)",
        "OCU_SKILL_X": "Not elsewhere classified",
        "OCU_ISCO88_TOTAL": "Total (ISCO-88)",
        "OCU_ISCO08_TOTAL": "Total (ISCO-08)",
    },
    "OBS_STATUS": {
        "B": "Break in series",
    },
}


def _muat_metadata_dataflow() -> dict[str, str]:
    """Membaca judul resmi indikator dari metadata/dataflow.json."""
    jalur = RAW_DIR / DATAFLOW_JSON
    if not jalur.exists():
        return {}
    with jalur.open("r", encoding="utf-8") as f:
        konten = json.load(f)
    hasil: dict[str, str] = {}
    for item in konten.get("data", {}).get("dataflows", []):
        df_id = str(item.get("id", ""))
        nama = item.get("name") or item.get("names", {}).get("en", "")
        if df_id:
            hasil[df_id] = str(nama)
    return hasil


def _baca_struktur_dsd(berkas_dsd: str) -> dict[str, Any]:
    """Memvalidasi dan mengekstrak daftar ID dimensi dari berkas DSD JSON."""
    with (RAW_DIR / berkas_dsd).open("r", encoding="utf-8") as f:
        dsd = json.load(f)
    struktur = dsd.get("data", {}).get("dataStructures", [{}])[0]
    komponen = struktur.get("dataStructureComponents", {})
    dimensi = [d.get("id") for d in komponen.get("dimensionList", {}).get("dimensions", [])]
    return {
        "dsd_id": struktur.get("id", ""),
        "dsd_nama": struktur.get("name", ""),
        "dimensi": dimensi,
    }


def baca_ilostat_csv(berkas_data: str, berkas_dsd: str, peta_dataflow: dict[str, str]) -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / berkas_data, dtype=str)
    info_dsd = _baca_struktur_dsd(berkas_dsd)

    # Tambahkan label untuk dimensi yang terdefinisi di DSD tanpa menghapus kode mentahnya
    for dim in info_dsd["dimensi"]:
        if dim in df.columns and dim in KAMUS_SDMX_ILO:
            df[f"{dim}_LABEL"] = df[dim].map(KAMUS_SDMX_ILO[dim]).fillna(df[dim])

    if "OBS_STATUS" in df.columns:
        df["OBS_STATUS_LABEL"] = df["OBS_STATUS"].map(KAMUS_SDMX_ILO["OBS_STATUS"]).fillna(df["OBS_STATUS"])

    dsd_id = info_dsd["dsd_id"]
    df["judul_indikator_raw"] = peta_dataflow.get(dsd_id) or info_dsd["dsd_nama"]
    df["sumber"] = "ilostat"
    df["_berkas_raw"] = berkas_data
    df["_sha256_raw"] = sha256_raw(berkas_data)
    return df


def baca_semua_ilostat() -> list[pd.DataFrame]:
    peta_dataflow = _muat_metadata_dataflow()
    hasil: list[pd.DataFrame] = []
    for item in PASANGAN_ILOSTAT:
        hasil.append(baca_ilostat_csv(item["data"], item["dsd"], peta_dataflow))
    return hasil