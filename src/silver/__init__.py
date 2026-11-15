"""Tahap 2-4 - Profil, pembersihan, dan penyeragaman ke Silver (pertemuan II-VII). Milik tim.

Keluaran: data/silver/silver.parquet dengan skema minimal di src/common/skema.py.
Satu baris = satu seri x wilayah x periode x rincian x berkas sumber. Nilai dari sumber berbeda
TIDAK digabung di sini. Setiap keputusan pembersihan dicatat di log-keputusan.csv.

Cakupan versi ini: seri BPS (var1172, var2153). Seri ILOSTAT masih perlu pembersih tersendiri.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import pandas as pd

from .grid import (
    bandingkan_format,
    bentuk_grid,
    kelengkapan,
    pilih_kanonik,
    sel_kosong_diharapkan,
    tandai_ekstrem,
)
from .wilayah import INDONESIA, NAMA_PROVINSI

# Sesuaikan nilai ini dengan yang diterima src/common/skema.py bila pemeriksa skema menolaknya.
JENIS_PERIODE_TAHUN = "tahun"

SATUAN_BAKU = {"1172": "rupiah_per_jam", "2153": "persen"}  # 2153: persen, lihat K-002

KOLOM_WAJIB = [
    "sumber", "seri_kode", "wilayah_kode", "nama_wilayah", "periode", "jenis_periode",
    "rincian", "nilai", "satuan", "_berkas_raw", "_sha256_raw",
]
JALUR_SILVER = Path("data/silver/silver.parquet")
JALUR_LAPORAN = Path("reports")


def _rincian(turvar: pd.Series) -> pd.Series:
    r = turvar.fillna("").str.strip().str.lower()
    r = r.where(r != "tidak ada", "total").where(r != "", "total")
    return r.str.replace(r"\s+", "_", regex=True)


def bangun_silver(mentah: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Ubah tabel panjang BPS hasil Tahap 1 menjadi Silver. Mengembalikan (silver, statistik)."""
    b = mentah[mentah["sumber"] == "bps"].copy()
    stat = {"baris_mentah_bps": len(b)}

    b["var_id"] = b["var_id"].astype(str).str.strip()
    tak_dikenal = sorted(set(b["var_id"]) - set(SATUAN_BAKU))
    if tak_dikenal:
        raise ValueError(f"var_id di luar var1172/var2153: {tak_dikenal}")

    # nilai: kosong atau tidak terbaca angka dibuang (Silver tidak menyimpan baris tanpa nilai)
    num = pd.to_numeric(b["nilai"], errors="coerce")
    stat["baris_nilai_kosong"] = int(b["nilai"].isna().sum())
    stat["baris_nilai_tak_terbaca"] = int((b["nilai"].notna() & num.isna()).sum())
    b = b.assign(nilai=num)[num.notna()].copy()

    # periode: hanya tahunan di kasus ini; jenis lain harus ditangani dulu, bukan dirata-rata diam-diam
    jenis = b["periode"].fillna("").str.strip().str.lower()
    if (jenis != "tahun").any():
        aneh = sorted(set(b.loc[jenis != "tahun", "periode"]))
        raise ValueError(f"Ada jenis periode selain 'Tahun': {aneh}. Tentukan aturan periode dulu.")
    b["periode"] = b["tahun"].astype(str).str.strip().str.extract(r"(\d{4})", expand=False)
    if b["periode"].isna().any():
        raise ValueError("Ada label tahun yang bukan empat digit.")
    b["jenis_periode"] = JENIS_PERIODE_TAHUN

    # wilayah: berdasarkan kode, bukan nama
    kode = pd.to_numeric(b["wilayah_id"], errors="coerce")
    sah = kode.isin(list(NAMA_PROVINSI) + [INDONESIA])
    if not sah.all():
        tak = b.loc[~sah, ["wilayah_id", "wilayah"]].drop_duplicates().to_dict("records")
        raise ValueError(f"Kode wilayah di luar 38 provinsi dan 9999: {tak}")
    b["wilayah_kode"] = kode.astype(int)
    b["nama_wilayah"] = b["wilayah_kode"].map({**NAMA_PROVINSI, INDONESIA: "Indonesia"})

    b["sumber"] = "bps"
    b["seri_kode"] = "var" + b["var_id"]
    b["rincian"] = _rincian(b["turvar"])
    b["satuan"] = b["var_id"].map(SATUAN_BAKU)

    # duplikat: sama persis -> satu baris; kunci sama tetapi nilai beda -> berhenti agar diputuskan manual
    kunci = ["seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw"]
    dup = b.duplicated(kunci, keep=False)
    if dup.any():
        beda = b[dup].groupby(kunci)["nilai"].nunique()
        if (beda > 1).any():
            raise ValueError(f"Kunci kembar dengan nilai berbeda:\n{beda[beda > 1]}")
    stat["baris_duplikat_dibuang"] = int(b.duplicated(kunci).sum())
    b = b.drop_duplicates(kunci, keep="last")

    silver = b[KOLOM_WAJIB].reset_index(drop=True)
    silver = tandai_ekstrem(silver)
    silver["periode"] = silver["periode"].astype(str)
    stat["baris_silver"] = len(silver)
    stat["baris_indonesia"] = int((silver["wilayah_kode"] == INDONESIA).sum())
    return silver, stat


def _draf_log(stat: dict, nim: str, mulai: int) -> str:
    baris = []

    def tambah(tahap, seri, keputusan, alt, alasan, dampak):
        baris.append([f"K-{mulai + len(baris):03d}", pd.Timestamp.now().strftime("%Y-%m-%d"), nim,
                      tahap, seri, keputusan, alt, alasan, dampak])

    tambah("silver", "var1172;var2153",
           "Baris tanpa nilai (kosong atau bukan angka) tidak disimpan di Silver",
           "Mengisi nilai kosong dengan interpolasi atau 0",
           "Aturan baku: Silver tidak menyimpan baris tanpa nilai; celah dihitung di grid.",
           stat["baris_nilai_kosong"] + stat["baris_nilai_tak_terbaca"])
    if stat["baris_duplikat_dibuang"]:
        tambah("silver", "var1172;var2153",
               "Baris dengan kunci dan nilai identik dalam satu berkas dijadikan satu",
               "Membiarkan baris ganda", "Kunci unik Silver tidak boleh kembar.",
               stat["baris_duplikat_dibuang"])
    tambah("silver", "var1172;var2153",
           "Baris Indonesia (9999) disimpan terpisah dari 38 provinsi dan tidak ikut grid atau penanda ekstrem",
           "Menghitung Indonesia sebagai salah satu provinsi", "Indonesia adalah agregat nasional, bukan unit provinsi.",
           0)
    tambah("silver", "var1172;var2153",
           f"Provinsi ekstrem ditandai di kolom outlier_ekstrem dengan IQR 1,5 (log untuk upah) tanpa mengubah nilai; "
           f"{stat['outlier_ditandai']} baris di berkas CSV",
           "Menghapus atau winsorizing provinsi ekstrem", "Distribusi upah menceng; ekstrem asli bukan galat input.",
           0)
    tambah("gold", "var1172;var2153",
           f"Grid 38 provinsi x tahun dibentuk dari CSV BPS; sel sebelum provinsi pemekaran berdiri tidak dihitung missing "
           f"({stat['sel_kosong_diharapkan']} sel kosong yang diharapkan)",
           "Menghitung semua provinsi sejak tahun pertama seri sebagai missing", "Sesuai K-001: provinsi baru hanya berisi tahun sejak berdiri.",
           0)
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(baris)
    return buf.getvalue()


def jalankan(mentah: pd.DataFrame) -> pd.DataFrame:
    """Terima keluaran tahap 1, tulis dan kembalikan DataFrame Silver."""
    silver, stat = bangun_silver(mentah)

    grid = bentuk_grid(silver)
    lengkap = kelengkapan(grid)
    kosong = sel_kosong_diharapkan(grid)
    uji = bandingkan_format(silver)
    kan = pilih_kanonik(silver)
    stat["outlier_ditandai"] = int(kan["outlier_ekstrem"].sum())
    stat["sel_kosong_diharapkan"] = len(kosong)

    JALUR_SILVER.parent.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(JALUR_SILVER, index=False)
    JALUR_LAPORAN.mkdir(parents=True, exist_ok=True)
    lengkap.to_csv(JALUR_LAPORAN / "kelengkapan_panel.csv", index=False)
    kosong.drop(columns=["diharapkan"]).to_csv(JALUR_LAPORAN / "sel_kosong_grid.csv", index=False)

    print("=== SILVER BPS (TAHAP 2-4) ===")
    print(f"baris mentah BPS      : {stat['baris_mentah_bps']}")
    print(f"nilai kosong dibuang  : {stat['baris_nilai_kosong']} (tak terbaca angka: {stat['baris_nilai_tak_terbaca']})")
    print(f"duplikat dibuang      : {stat['baris_duplikat_dibuang']}")
    print(f"baris Silver          : {stat['baris_silver']} (baris Indonesia: {stat['baris_indonesia']})")
    print(f"uji silang CSV vs JSON: {uji}")
    print(f"outlier ditandai (CSV): {stat['outlier_ditandai']}")
    print(f"sel kosong diharapkan : {stat['sel_kosong_diharapkan']} -> reports/sel_kosong_grid.csv")
    print("Kelengkapan panel (persen terisi per tahun), disimpan di reports/kelengkapan_panel.csv:")
    print(lengkap.pivot(index="periode", columns="seri_kode", values="persen_terisi_diharapkan").to_string())
    print("\n--- DRAF BARIS log-keputusan.csv (periksa, sesuaikan, lalu tempel; K-005 dst. setelah log Anda) ---")
    print(_draf_log(stat, "124450065", 5))
    print("--- PERINTAH metrics.json ---")
    print(f"python -m src.common.hasil 124450065 baris_silver={stat['baris_silver']} "
          f"sel_kosong_grid={stat['sel_kosong_diharapkan']} outlier_ditandai={stat['outlier_ditandai']}")
    return silver