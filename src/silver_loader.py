"""Pemuat awal lapisan Silver ke DuckDB untuk Kasus 12."""
import csv
import hashlib
from pathlib import Path
import duckdb

AKAR = Path(__file__).resolve().parent.parent
RAW = AKAR / "data" / "raw"
DDL = AKAR / "sql" / "schema_silver.sql"
DB_PATH = AKAR / "data" / "silver.duckdb"


def hitung_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def muat_bps(rel_path: str, seri_kode: str, default_satuan: str) -> list[tuple]:
    p = RAW / rel_path
    sha = hitung_sha256(p)
    baris = []
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            val = float(r["nilai"]) if r["nilai"] not in ("", None, "-") else None
            satuan = r["satuan"].strip() if r["satuan"].strip() else default_satuan
            baris.append((
                "bps",
                seri_kode,
                r["wilayah_id"].strip(),
                r["wilayah"].strip(),
                r["tahun"].strip(),
                r["periode"].strip().lower(),
                r["turvar"].strip(),
                val,
                satuan,
                rel_path,
                sha,
            ))
    return baris


def muat_ilostat(rel_path: str, seri_kode: str, dim_kedua: str) -> list[tuple]:
    p = RAW / rel_path
    sha = hitung_sha256(p)
    baris = []
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["REF_AREA"] != "IDN":
                continue
            val = float(r["OBS_VALUE"]) if r["OBS_VALUE"] not in ("", None) else None
            rincian = f"{r['SEX']}|{r[dim_kedua]}"
            satuan = f"{r['UNIT_MEASURE']}_mult{r['UNIT_MULT']}"
            baris.append((
                "ilostat",
                seri_kode,
                "IDN",
                "Indonesia",
                r["TIME_PERIOD"].strip(),
                "tahun" if r["FREQ"] == "A" else r["FREQ"].lower(),
                rincian,
                val,
                satuan,
                rel_path,
                sha,
            ))
    return baris


def main():
    con = duckdb.connect(str(DB_PATH))
    con.execute(DDL.read_text(encoding="utf-8"))
    con.execute("DELETE FROM silver_indikator")

    data = []
    data.extend(muat_bps("bps/2026-10-17/sdg8_upah.csv", "var1172", "Rupiah/Jam"))
    data.extend(muat_bps("bps/2026-10-17/sdg8_informal.csv", "var2153", "persen"))
    data.extend(muat_ilostat("ilostat/2026-10-20/data/DF_SDG_0851_SEX_OCU_NB.csv", "SDG_0851_SEX_OCU_NB", "OCU"))
    data.extend(muat_ilostat("ilostat/2026-10-20/data/DF_SDG_0831_SEX_ECO_RT.csv", "SDG_0831_SEX_ECO_RT", "ECO"))

    con.executemany(
        "INSERT INTO silver_indikator VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        data,
    )

    ringkasan = con.execute(
        "SELECT sumber, seri_kode, COUNT(*) AS jml_baris FROM silver_indikator GROUP BY 1, 2 ORDER BY 1, 2"
    ).fetchall()
    print("Muatan Silver pertama berhasil:")
    for s, k, n in ringkasan:
        print(f" - {s} | {k}: {n} baris")
    con.close()


if __name__ == "__main__":
    main()
