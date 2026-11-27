"""Satu perintah reproduksi tim: data mentah -> Silver -> Gold -> validasi -> SQL (DuckDB).

    python unduh_data.py --kasus <N>     # sekali, isi data/raw/
    python pipeline.py

Urutan tahap tidak diubah; isi tiap tahap di src/<tahap>/. Tahap 7 (skala, arsip WDI) ditulis
sebagai skrip terpisah di src/skala/ karena memakai unduhan tambahan.
"""
from pathlib import Path
import sys
import time

import duckdb

from src import ekstraksi, gold, silver, validasi
from src.common.manifest import periksa


def muat_ke_sql(db_path: str = "data/warehouse.duckdb", ddl_path: str = "sql/schema.sql") -> dict:
    """Bangun basis data DuckDB dari DDL, muat Parquet Silver & Gold, dan validasi jumlah baris."""
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()

    con = duckdb.connect(db_path)
    ddl_sql = Path(ddl_path).read_text(encoding="utf-8")
    con.execute(ddl_sql)

    pemetaan_tabel = {
        "silver_indikator": "data/silver/silver.parquet",
        "gold_panel": "data/gold/panel.parquet",
        "gold_tabel_nasional": "data/gold/tabel_nasional_gold.parquet",
        "gold_rekonsiliasi": "data/gold/rekonsiliasi_nasional.parquet",
    }

    print("\n=== VALIDASI JUMLAH BARIS: PARQUET vs SQL (DuckDB) ===")
    print(f"{'Tabel SQL':<24} | {'Berkas Parquet':<36} | {'Parquet':>7} | {'SQL':>7} | {'Status'}")
    print("-" * 92)

    ringkasan = {}
    for tabel, path_pq in pemetaan_tabel.items():
        con.execute(f"INSERT INTO {tabel} SELECT * FROM read_parquet('{path_pq}')")
        jml_pq = con.execute(f"SELECT COUNT(*) FROM read_parquet('{path_pq}')").fetchall()[0][0]
        jml_sql = con.execute(f"SELECT COUNT(*) FROM {tabel}").fetchall()[0][0]
        status = "MATCH" if jml_pq == jml_sql else "MISMATCH"
        print(f"{tabel:<24} | {path_pq:<36} | {jml_pq:>7} | {jml_sql:>7} | {status}")
        assert jml_pq == jml_sql, f"Jumlah baris tidak cocok pada {tabel}: Parquet={jml_pq}, SQL={jml_sql}"
        ringkasan[tabel] = jml_sql

    con.close()
    print("-" * 92)
    print(f"Basis data SQL terbentuk di: {db_path}\n")
    return ringkasan


def main():
    n, salah = periksa()
    if salah:
        sys.exit(f"data/raw tidak cocok dengan MANIFEST.csv ({len(salah)} berkas). Jalankan ulang unduh_data.py.")
    print(f"data/raw: {n} berkas cocok dengan MANIFEST.csv")
    for nama, langkah in [("ekstraksi", lambda h: ekstraksi.jalankan()),
                          ("silver", lambda h: silver.jalankan(h["ekstraksi"])),
                          ("gold", lambda h: gold.jalankan(h["silver"])),
                          ("validasi", lambda h: validasi.jalankan(h["silver"], h["gold"])),
                          ("sql", lambda h: muat_ke_sql())]:
        mulai = time.time()
        hasil[nama] = langkah(hasil)
        print(f"{nama:<10} selesai dalam {time.time() - mulai:.1f} s")
    print("Periksa skema minimal: python -m src.common.skema data/silver/silver.parquet")


hasil = {}

if __name__ == "__main__":
    main()
