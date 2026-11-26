from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

KUNCI_PANEL = ["provinsi", "periode", "indikator"]
SERI_UTAMA = ("var1172", "var2153")


def _tambah_log(
    logs: list[dict[str, Any]],
    aturan: str,
    alasan: str,
    df_sebelum: pd.DataFrame,
    df_sesudah: pd.DataFrame,
) -> None:
    sebelum = len(df_sebelum)
    sesudah = len(df_sesudah)
    tidak_terpilih = max(sebelum - sesudah, 0)
    logs.append(
        {
            "tahap": "gold",
            "aturan": aturan,
            "alasan": alasan,
            "baris_sebelum": sebelum,
            "baris_sesudah": sesudah,
            "jumlah_baris_tidak_terpilih": tidak_terpilih,
        }
    )


def filter_seri_dan_provinsi(
    df: pd.DataFrame,
    logs: list[dict[str, Any]],
) -> pd.DataFrame:
    df_kerja = df.copy()
    df_kerja["_baris_silver"] = df_kerja.index

    mask_seri = df_kerja["seri_kode"].astype(str).isin(SERI_UTAMA)
    mask_prov = ~df_kerja["wilayah_kode"].astype(str).isin(["9999", "IDN", "0000"])
    hasil = df_kerja[mask_seri & mask_prov].copy()

    _tambah_log(
        logs=logs,
        aturan="filter_seri_utama_provinsi",
        alasan="Saring seri utama tingkat provinsi (var1172, var2153) dan keluarkan agregat nasional (9999).",
        df_sebelum=df_kerja,
        df_sesudah=hasil,
    )
    return hasil


def pilih_rincian_panel(
    df: pd.DataFrame,
    logs: list[dict[str, Any]],
    rincian_diizinkan: tuple[str, ...] = ("total",),
) -> pd.DataFrame:
    if "rincian" not in df.columns:
        _tambah_log(
            logs=logs,
            aturan="rincian_sebanding_panel",
            alasan="Kolom rincian tidak ada; seluruh baris dipertahankan.",
            df_sebelum=df,
            df_sesudah=df,
        )
        return df.copy()

    mask = df["rincian"].astype(str).str.strip().str.lower().isin(rincian_diizinkan)
    hasil = df[mask].copy()
    _tambah_log(
        logs=logs,
        aturan="rincian_sebanding_panel",
        alasan="Pilih rincian total untuk panel Gold; rincian jabatan ILO tetap disimpan di Silver.",
        df_sebelum=df,
        df_sesudah=hasil,
    )
    return hasil


def pilih_periode_panel(
    df: pd.DataFrame,
    logs: list[dict[str, Any]],
    prioritas_jenis: tuple[str, ...] = ("tahun", "semester", "bulan"),
) -> pd.DataFrame:
    kunci_awal = ["wilayah_kode", "periode", "seri_kode"]
    if "jenis_periode" not in df.columns:
        _tambah_log(
            logs=logs,
            aturan="prioritas_jenis_periode",
            alasan="Kolom jenis_periode tidak ada; seluruh baris dipertahankan.",
            df_sebelum=df,
            df_sesudah=df,
        )
        return df.copy()

    peta_prio = {nama: idx for idx, nama in enumerate(prioritas_jenis)}
    df_kerja = df.copy()
    df_kerja["_prio_periode"] = (
        df_kerja["jenis_periode"].astype(str).str.strip().str.lower().map(peta_prio).fillna(99)
    )
    df_kerja = df_kerja.sort_values(by=["_prio_periode"], ascending=True)
    hasil = df_kerja.drop_duplicates(subset=kunci_awal, keep="first").drop(columns=["_prio_periode"])

    _tambah_log(
        logs=logs,
        aturan="prioritas_jenis_periode",
        alasan="Utamakan jenis_periode tahun lalu semester lalu bulan per sel.",
        df_sebelum=df,
        df_sesudah=hasil,
    )
    return hasil


def pilih_snapshot_panel(
    df: pd.DataFrame,
    logs: list[dict[str, Any]],
) -> pd.DataFrame:
    kunci_awal = ["wilayah_kode", "periode", "seri_kode"]
    df_kerja = df.copy()

    if "_berkas_raw" in df_kerja.columns:
        df_kerja["_is_csv"] = df_kerja["_berkas_raw"].astype(str).str.lower().str.endswith(".csv").astype(int)
        kolom_urut = ["_is_csv", "_berkas_raw"]
    else:
        kolom_urut = [k for k in ["_berkas_raw", "_sha256_raw"] if k in df_kerja.columns]

    if kolom_urut:
        df_kerja = df_kerja.sort_values(by=kolom_urut, ascending=False, na_position="last")

    hasil = df_kerja.drop_duplicates(subset=kunci_awal, keep="first").copy()
    if "_is_csv" in hasil.columns:
        hasil = hasil.drop(columns=["_is_csv"])

    _tambah_log(
        logs=logs,
        aturan="satu_nilai_per_sel_snapshot",
        alasan="Pilih satu baris kanonik (CSV) per sel; pertahankan outlier_ekstrem, status_obs, dan lineage Silver.",
        df_sebelum=df,
        df_sesudah=hasil,
    )
    return hasil


def standarisasi_dan_turunan_panel(
    df: pd.DataFrame,
    deflator_ihk: dict[int, float] | None = None,
    sumber_deflator: str = "belum_tersedia_di_paket",
) -> pd.DataFrame:
    hasil = df.copy()

    hasil["provinsi"] = hasil["nama_wilayah"].astype(str).str.strip()
    hasil["periode"] = pd.to_numeric(hasil["periode"], errors="coerce").astype("Int64")
    hasil["indikator"] = hasil["seri_kode"].astype(str).str.strip()
    hasil["nilai"] = pd.to_numeric(hasil["nilai"], errors="coerce")

    peta_satuan = {
        "var1172": "rupiah_per_jam",
        "var2153": "persen",
    }
    hasil["satuan"] = hasil["indikator"].map(peta_satuan).fillna(hasil["satuan"])

    adalah_upah = hasil["indikator"] == "var1172"

    hasil["log_upah"] = np.where(
        adalah_upah & (hasil["nilai"] > 0),
        np.log(hasil["nilai"]),
        np.nan,
    )

    if deflator_ihk:
        indeks = hasil["periode"].map(deflator_ihk)
        hasil["upah_riil"] = np.where(
            adalah_upah & indeks.notna() & (indeks > 0),
            hasil["nilai"] / (indeks / 100.0),
            np.nan,
        )
        hasil["sumber_deflator"] = np.where(adalah_upah, sumber_deflator, None)
    else:
        hasil["upah_riil"] = np.nan
        hasil["sumber_deflator"] = np.where(adalah_upah, "belum_terdefinisi_butuh_IHK_WDI", None)

    kolom_utama = [
        "wilayah_kode",
        "provinsi",
        "periode",
        "indikator",
        "nilai",
        "satuan",
        "upah_riil",
        "sumber_deflator",
        "log_upah",
        "outlier_ekstrem",
        "status_obs",
        "_baris_silver",
        "_berkas_raw",
        "_sha256_raw",
    ]
    kolom_tersedia = [c for c in kolom_utama if c in hasil.columns]
    kolom_sisa = [c for c in hasil.columns if c not in kolom_tersedia]
    return hasil[kolom_tersedia + kolom_sisa].sort_values(KUNCI_PANEL).reset_index(drop=True)


def simpan_log_keputusan(
    logs_baru: list[dict[str, Any]],
    path_log: str | Path = "log-keputusan.csv",
) -> pd.DataFrame:
    path = Path(path_log)
    df_baru = pd.DataFrame(logs_baru)

    if path.exists() and path.stat().st_size > 0:
        df_lama = pd.read_csv(path)
        if "tahap" in df_lama.columns:
            df_lama = df_lama[df_lama["tahap"] != "gold"]
        df_all = pd.concat([df_lama, df_baru], ignore_index=True)
    else:
        df_all = df_baru

    path.parent.mkdir(parents=True, exist_ok=True)
    df_all.to_csv(path, index=False)
    return df_all


def bangun_gold_dari_silver(
    df_silver: pd.DataFrame,
    path_log: str | Path = "log-keputusan.csv",
    deflator_ihk: dict[int, float] | None = None,
    sumber_deflator: str = "belum_tersedia_di_paket",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    logs: list[dict[str, Any]] = []

    step0 = filter_seri_dan_provinsi(df_silver, logs=logs)
    step1 = pilih_rincian_panel(step0, logs=logs)
    step2 = pilih_periode_panel(step1, logs=logs)
    step3 = pilih_snapshot_panel(step2, logs=logs)
    df_gold = standarisasi_dan_turunan_panel(
        step3,
        deflator_ihk=deflator_ihk,
        sumber_deflator=sumber_deflator,
    )

    duplikat = df_gold.duplicated(subset=KUNCI_PANEL, keep=False).sum()
    if duplikat > 0:
        raise ValueError(f"Masih ada {duplikat} baris duplikat pada kunci {KUNCI_PANEL}.")

    df_log = simpan_log_keputusan(logs, path_log=path_log)
    return df_gold, df_log