"""Adaptor Tahap 2: tabel hasil ekstraksi -> tabel masukan profil_tahap2.py.

Hanya MEMBACA hasil ekstraksi dan menerjemahkan nama kolom. Tidak memperbaiki nilai.
Baris yang nilainya tidak terbaca sebagai angka TIDAK dibuang diam-diam: dicatat di
reports/profil/nilai_tak_terbaca.csv (itu temuan), lalu dikeluarkan hanya dari tabel profil.

Pakai (dari akar repo, venv aktif):
    python src/profil/siapkan_tabel_profil.py
    python src/profil/profil_tahap2.py --silver reports/profil/tabel_profil_bps.csv
"""
import sys
from pathlib import Path

import pandas as pd

SERI = {"1172": "var1172", "2153": "var2153"}
OUT = Path("reports/profil")


def bangun(df: pd.DataFrame):
    d = df[(df["sumber"].astype(str).str.lower() == "bps") & (df["var_id"].astype(str).isin(SERI))].copy()
    d["var_id"] = d["var_id"].astype(str)
    nama = d["wilayah"].astype(str).str.upper()
    kode = d["wilayah_id"].astype(str)
    nasional = nama.str.contains("INDONESIA")
    tabel = pd.DataFrame({
        "seri_kode": d["var_id"].map(SERI),
        "wilayah_kode": kode.where(~nasional, "9999"),   # penanda nasional untuk skrip profil
        "nama_wilayah": d["wilayah"],
        "periode": d["tahun"].astype(str),
        "jenis_periode": d["periode"].astype(str),
        "rincian": d["turvar"].astype(str).replace({"Tidak ada": "total"}),
        "nilai": pd.to_numeric(d["nilai"], errors="coerce"),
        "satuan": d["satuan"],
        "_berkas_raw": d["_berkas_raw"],
        "_sha256_raw": d["_sha256_raw"],
    })
    tabel["nilai_mentah"] = d["nilai"].values
    rusak = tabel[tabel["nilai"].isna()]
    return tabel[tabel["nilai"].notna()].drop(columns="nilai_mentah"), rusak, nasional.sum()


def main():
    from src import ekstraksi

    hasil = ekstraksi.jalankan()
    df = hasil if hasattr(hasil, "columns") else hasil["ekstraksi"]
    tabel, rusak, n_nas = bangun(df)
    OUT.mkdir(parents=True, exist_ok=True)
    tabel.to_csv(OUT / "tabel_profil_bps.csv", index=False)
    rusak.to_csv(OUT / "nilai_tak_terbaca.csv", index=False)

    print("\n=== DIAGNOSTIK ADAPTOR (bukan perbaikan) ===")
    print("baris per seri_kode dan satuan:"); print(tabel.groupby(["seri_kode", "satuan"]).size().to_string())
    print("\nrincian (turvar) per seri:"); print(tabel.groupby("seri_kode")["rincian"].unique().to_string())
    print("\nrentang tahun per seri:"); print(tabel.groupby("seri_kode")["periode"].agg(["min", "max", "nunique"]).to_string())
    print("\njumlah wilayah per tahun (var1172, var2153):")
    print(tabel.groupby(["seri_kode", "periode"])["wilayah_kode"].nunique().unstack(0).to_string())
    print(f"\nbaris yang dikenali sebagai nasional (nama mengandung INDONESIA): {n_nas}")
    print(f"nilai tidak terbaca sebagai angka: {len(rusak)} baris -> reports/profil/nilai_tak_terbaca.csv")
    if len(rusak):
        print(rusak[["seri_kode", "wilayah_kode", "nama_wilayah", "periode", "nilai_mentah"]].head(15).to_string())
    print("\nwilayah unik (kode, nama):")
    print(tabel[["wilayah_kode", "nama_wilayah"]].drop_duplicates().sort_values("wilayah_kode").to_string(index=False))


if __name__ == "__main__":
    sys.path.insert(0, str(Path.cwd()))
    main()
