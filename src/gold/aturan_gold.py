from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

KUNCI_PANEL = ["wilayah_kode", "periode", "seri_kode"]


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


def pilih_rincian_panel(
    df: pd.DataFrame,
    logs: list[dict[str, Any]],
    rincian_diizinkan: tuple[str, ...] = ("total",),
) -> pd.DataFrame:
    """
    Memilih baris dengan rincian yang sebanding ('total') untuk panel Gold.
    Rincian detail seperti rincian jabatan ILO tetap disimpan di Silver.
    """
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
        alasan=(
            "Pilih rincian 'total' untuk panel Gold agar sebanding; "
            "rincian jabatan ILO dan kategori rincian lain tetap disimpan di Silver."
        ),
        df_sebelum=df,
        df_sesudah=hasil,
    )
    return hasil


def pilih_periode_panel(
    df: pd.DataFrame,
    logs: list[dict[str, Any]],
    prioritas_jenis: tuple[str, ...] = ("tahun", "semester", "bulan"),
) -> pd.DataFrame:
    """
    Menangani periode tahunan, semesteran, atau bulanan secara deterministik.
    Jika pada kunci yang sama ada lebih dari satu jenis periode, pilih prioritas tertinggi.
    """
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
    hasil = df_kerja.drop_duplicates(subset=KUNCI_PANEL, keep="first").drop(columns=["_prio_periode"])

    _tambah_log(
        logs=logs,
        aturan="prioritas_jenis_periode",
        alasan=(
            "Utamakan jenis_periode 'tahun' (lalu 'semester', 'bulan') bila terdapat "
            "lebih dari satu periode pada kunci wilayah_kode x periode x seri_kode."
        ),
        df_sebelum=df,
        df_sesudah=hasil,
    )
    return hasil


def pilih_snapshot_panel(
    df: pd.DataFrame,
    logs: list[dict[str, Any]],
) -> pd.DataFrame:
    """
    Memilih tepat satu baris per kunci wilayah_kode x periode x seri_kode
    jika terdapat beberapa snapshot/berkas dengan nilai berbeda.
    Kolom penanda Sprint 1 (outlier_ekstrem, status_obs) tetap dipertahankan.
    """
    df_kerja = df.copy()

    kolom_urut = [k for k in ["_berkas_raw", "_sha256_raw"] if k in df_kerja.columns]
    if kolom_urut:
        df_kerja = df_kerja.sort_values(by=kolom_urut, ascending=False, na_position="last")

    hasil = df_kerja.drop_duplicates(subset=KUNCI_PANEL, keep="first").copy()

    _tambah_log(
        logs=logs,
        aturan="satu_nilai_per_sel_snapshot",
        alasan=(
            "Pilih satu baris deterministik per sel wilayah_kode x periode x seri_kode "
            "bila ada beda snapshot/berkas; pertahankan outlier_ekstrem dan status_obs."
        ),
        df_sebelum=df,
        df_sesudah=hasil,
    )
    return hasil


def tambah_kolom_turunan_upah(
    df: pd.DataFrame,
    seri_upah: str = "var1172",
) -> pd.DataFrame:
    """
    Menambah kolom turunan di Gold tanpa mengubah upah nominal di Silver:
    - upah_riil: disiapkan di Gold (sama dengan nilai bila belum ada indeks harga terpisah)
    - log_upah: logaritma natural ln(nilai) untuk nilai positif pada seri upah
    """
    hasil = df.copy()
    if "seri_kode" in hasil.columns and "nilai" in hasil.columns:
        nilai_num = pd.to_numeric(hasil["nilai"], errors="coerce")
        adalah_upah = hasil["seri_kode"].astype(str) == seri_upah

        hasil["upah_riil"] = np.where(adalah_upah, nilai_num, np.nan)
        hasil["log_upah"] = np.where(adalah_upah & (nilai_num > 0), np.log(nilai_num), np.nan)

    return hasil


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
) -> tuple[pd.DataFrame, pd.DataFrame]:
    logs: list[dict[str, Any]] = []

    step1 = pilih_rincian_panel(df_silver, logs=logs)
    step2 = pilih_periode_panel(step1, logs=logs)
    step3 = pilih_snapshot_panel(step2, logs=logs)
    df_gold = tambah_kolom_turunan_upah(step3)

    duplikat = df_gold.duplicated(subset=KUNCI_PANEL, keep=False).sum()
    if duplikat > 0:
        raise ValueError(f"Masih ada {duplikat} baris duplikat pada kunci {KUNCI_PANEL}.")

    df_log = simpan_log_keputusan(logs, path_log=path_log)
    return df_gold, df_log
