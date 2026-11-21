"""Katalog seri Kasus 12: SATU satuan dan kode SDG per seri, lengkap dengan sumber buktinya.

    python -m src.silver.katalog

Menulis docs/katalog_seri.csv, memeriksa konsistensi dengan Silver (satu satuan per seri, besaran
nilai masuk akal, tidak ada periode sub-tahunan), dan mencetak draf baris log-keputusan.csv untuk
setiap koreksi katalog. Metadata di sini diisi manual dari bukti (bukti_katalog.txt); sisanya otomatis.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

import pandas as pd

from . import NIM

KODE_LOG_MULAI_KATALOG = 15  # <-- nomor K- berikutnya setelah log Anda (K-012..K-014 dipakai Sprint 1)
ISI = "ISI"                  # penanda yang HARUS diganti; pemeriksa menolak bila masih ada
RAW = Path("data/raw")
JALUR_SILVER = Path("data/silver/silver.parquet")
JALUR_KATALOG = Path("docs/katalog_seri.csv")

# Besaran wajar per satuan (batas lebar; hanya menangkap salah satuan/skala, bukan outlier biasa).
BATAS_WAJAR = {"rupiah_per_jam": (1_000, 200_000), "persen": (0, 100)}

# ---------------------------------------------------------------------------------------------
# ISI DARI BUKTI. Nilai awal di bawah adalah hipotesis dari dokumen konteks dan hasil cek_ilo.py:
# KONFIRMASI setiap baris dengan bukti_katalog.txt, ubah bila bukti berkata lain.
#   satuan       : satuan yang DITETAPKAN (satu per seri)
#   kode_sdg     : kode indikator SDG yang DITETAPKAN
#   bukti_sdg    : sumber kode SDG. Biarkan ISI: diisi OTOMATIS dari metadata berkas mentah (JSON BPS /
#                  dataflow ILOSTAT). Isi manual hanya bila metadata mentah tidak memuat kode SDG.
#   *_awal       : nilai di katalog awal (KASUS.md); beda dengan yang ditetapkan = koreksi.
#                  "-" = katalog awal tidak mencantumkan nilai itu (seri ILOSTAT tidak punya kolom satuan)
#   dilog        : {"satuan": "K-002"} bila koreksi itu sudah tercatat di log; tidak dibuat ulang
# ---------------------------------------------------------------------------------------------
KATALOG = {
    "var1172": dict(
        sumber="bps", berkas_bukti="bps/2026-10-17/json/sdg8_upah.json",
        kode_sdg="8.5.1", bukti_sdg="KASUS.md, tabel Seri utama (katalog awal); metadata JSON BPS tidak memuat nomor indikator (var.subj: Tujuan Pembangunan Berkelanjutan Edisi I); konsep sesuai dataflow ILOSTAT SDG indicator 8.5.1: Average hourly earnings of employees",
        satuan="rupiah_per_jam",
        alasan_satuan="Unit di metadata JSON dan CSV BPS 'Rupiah/Jam'; judul 'Upah Rata - Rata Per Jam Pekerja Menurut Provinsi'; nilai 8.525-42.354",
        kode_sdg_awal="8.5.1", satuan_awal="rupiah_per_jam", dilog={},
    ),
    "var2153": dict(
        sumber="bps", berkas_bukti="bps/2026-10-17/json/sdg8_informal.json",
        kode_sdg="8.3.1", bukti_sdg="KASUS.md, tabel Seri utama (katalog awal); metadata JSON BPS tidak memuat nomor indikator (var.subj: Tujuan Pembangunan Berkelanjutan Edisi I); konsep sesuai dataflow ILOSTAT SDG indicator 8.3.1: Proportion of informal employment",
        satuan="persen",
        alasan_satuan="Unit di metadata JSON dan CSV BPS kosong; judul 'Proporsi Lapangan Kerja Informal Menurut Provinsi' dan nilai 29,57-95,76 berada dalam 0-100",
        kode_sdg_awal="8.3.1", satuan_awal="tidak_ada", dilog={"satuan": "K-002"},
    ),
    "SDG_0851_SEX_OCU_NB": dict(
        sumber="ilostat", berkas_bukti="ilostat/2026-10-20/data/DF_SDG_0851_SEX_OCU_NB.csv",
        kode_sdg="8.5.1", bukti_sdg=ISI,
        satuan="rupiah_per_jam",
        alasan_satuan="UNIT_MEASURE=LC (mata uang lokal), NOTE_INDICATOR 'IDR: Indonesian rupiah', judul dataflow berupa hourly earnings",
        kode_sdg_awal="8.5.1", satuan_awal="-", dilog={},
    ),
    "SDG_0831_SEX_ECO_RT": dict(
        sumber="ilostat", berkas_bukti="ilostat/2026-10-20/data/DF_SDG_0831_SEX_ECO_RT.csv",
        kode_sdg="8.3.1", bukti_sdg=ISI,
        satuan="persen",
        alasan_satuan="UNIT_MEASURE=PT (persen), UNIT_MEASURE_TYPE=RT (rate); nilai 0-100",
        kode_sdg_awal="8.3.1", satuan_awal="-", dilog={},
    ),
}


def _judul_unit_bps(berkas: str, seri: str) -> tuple[str, str]:
    konten = json.loads((RAW / berkas).read_text(encoding="utf-8"))
    for h in (konten if isinstance(konten, list) else [konten]):
        for v in (h.get("var") or []) if isinstance(h, dict) else []:
            if str(v.get("val")) == seri.replace("var", ""):
                return str(v.get("label", "")), str(v.get("unit", ""))
    return "(var tidak ditemukan di JSON)", ""


def _judul_unit_ilo(berkas: str, seri: str) -> tuple[str, str]:
    judul = ""
    jalur = RAW / "ilostat/2026-10-20/metadata/dataflow.json"
    if jalur.exists():
        for it in json.loads(jalur.read_text(encoding="utf-8")).get("data", {}).get("dataflows", []):
            if seri in str(it.get("id", "")):
                judul = str(it.get("name") or it.get("names", {}).get("en", ""))
    df = pd.read_csv(RAW / berkas, dtype=str, usecols=lambda c: c in ("UNIT_MEASURE", "UNIT_MEASURE_TYPE", "UNIT_MULT"))
    unit = ";".join(f"{k}={'/'.join(sorted(df[k].dropna().unique()))}" for k in df.columns)
    return judul, unit


POLA_SDG = re.compile(r"\b(?:[1-9]|1[0-7])\.[1-9]\d?\.[1-9]\d?\b")


def _kode_sdg_sumber(k: dict, seri: str) -> tuple[set, str]:
    """Cari kode indikator SDG (pola 8.5.1) di metadata berkas mentah. Mengembalikan (himpunan kode, kutipan bukti)."""
    teks = []  # (berkas, isi teks metadata)
    if k["sumber"] == "bps":
        konten = json.loads((RAW / k["berkas_bukti"]).read_text(encoding="utf-8"))
        h0 = (konten if isinstance(konten, list) else [konten])[0]
        teks.append((k["berkas_bukti"], json.dumps({a: b for a, b in h0.items() if a != "datacontent"}, ensure_ascii=False)))
    else:
        for rel in ("ilostat/2026-10-20/metadata/dataflow.json", f"ilostat/2026-10-20/dsd/{seri}.json"):
            f = RAW / rel
            if not f.exists():
                continue
            data = json.loads(f.read_text(encoding="utf-8")).get("data", {})
            if "dataflows" in data:
                data = [x for x in data["dataflows"] if seri in str(x.get("id", ""))]
            teks.append((rel, json.dumps(data, ensure_ascii=False)))
    kode, kutipan = set(), ""
    for rel, isi in teks:
        for m in POLA_SDG.finditer(isi):
            kode.add(m.group())
            if not kutipan:
                kutipan = f"{rel}: ...{isi[max(0, m.start() - 40):m.end() + 20]}..."
    return kode, kutipan


def _draf_log(koreksi: list[list]) -> str:
    baris = []
    for i, (seri, bidang, awal, baru, bukti, alasan, dampak) in enumerate(koreksi):
        if awal == "-":
            keputusan = f"Satuan {baru!r} ditetapkan untuk seri (katalog awal tidak mencantumkan satuan); sumber: {bukti}"
            alternatif = "Membiarkan satuan seri tidak tercatat"
        else:
            keputusan = f"Koreksi katalog: {bidang} {awal!r} -> {baru!r}; sumber: {bukti}"
            alternatif = f"Mempertahankan {bidang} katalog awal ({awal!r})"
        baris.append([f"K-{KODE_LOG_MULAI_KATALOG + i:03d}", pd.Timestamp.now().strftime("%Y-%m-%d"), NIM,
                      "silver", seri, keputusan, alternatif, alasan, dampak])
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(baris)
    return buf.getvalue()


def main() -> int:
    if not JALUR_SILVER.exists():
        sys.exit("data/silver/silver.parquet belum ada. Jalankan pipeline Silver dulu.")
    silver = pd.read_parquet(JALUR_SILVER)
    masalah, baris_csv, koreksi = [], [], []
    KATALOG_PAKAI = {}

    ada = set(silver["seri_kode"])
    if ada != set(KATALOG):
        masalah.append(f"seri di Silver {sorted(ada)} tidak sama dengan KATALOG {sorted(KATALOG)}")

    for seri, k in KATALOG.items():
        k = dict(k)
        kode_src, kutipan = _kode_sdg_sumber(k, seri)
        if kode_src and k["kode_sdg"] not in kode_src:
            masalah.append(f"{seri}: metadata sumber menyebut kode SDG {sorted(kode_src)}, bukan '{k['kode_sdg']}'. "
                           f"Bila bukti kuat, ubah kode_sdg (dan catat sebagai koreksi, kode_sdg_awal tetap nilai katalog).")
        elif kode_src and k["bukti_sdg"] == ISI:
            k["bukti_sdg"] = kutipan
        KATALOG_PAKAI[seri] = k
        kosong = [f for f, v in k.items() if v == ISI]
        if kosong:
            masalah.append(f"{seri}: masih ada isian '{ISI}' pada {kosong}"
                           + (" (metadata mentah tidak memuat kode SDG: isi bukti_sdg manual, mis. 'KASUS.md, tabel Seri utama')"
                              if "bukti_sdg" in kosong else ""))
        d = silver[silver["seri_kode"] == seri]
        if d.empty:
            continue
        if set(d["satuan"]) != {k["satuan"]}:
            masalah.append(f"{seri}: satuan di Silver {sorted(set(d['satuan']))} != katalog '{k['satuan']}'. "
                           f"Ubah SATUAN_BAKU (BPS) atau SERI_ILO (ILOSTAT) di src/silver lalu jalankan ulang pipeline.")
        if set(d["jenis_periode"]) != {"tahun"}:
            masalah.append(f"{seri}: jenis_periode {sorted(set(d['jenis_periode']))}; Silver tidak boleh meratakan "
                           f"periode semesteran/bulanan ke tahunan")
        batas = BATAS_WAJAR.get(k["satuan"])
        if batas is None:
            masalah.append(f"{seri}: satuan '{k['satuan']}' belum punya batas di BATAS_WAJAR")
        elif not d["nilai"].between(*batas).all():
            masalah.append(f"{seri}: ada nilai di luar {batas} untuk satuan {k['satuan']} "
                           f"(min {d['nilai'].min():.2f}, max {d['nilai'].max():.2f})")

        judul, unit = (_judul_unit_bps if k["sumber"] == "bps" else _judul_unit_ilo)(k["berkas_bukti"], seri)
        baris_csv.append({
            "seri_kode": seri, "sumber": k["sumber"], "judul_sumber": judul, "kode_sdg": k["kode_sdg"],
            "bukti_sdg": k["bukti_sdg"], "satuan_sumber": unit, "satuan": k["satuan"],
            "alasan_satuan": k["alasan_satuan"], "berkas_bukti": k["berkas_bukti"],
            "n_baris": len(d), "nilai_min": round(d["nilai"].min(), 3),
            "nilai_median": round(d["nilai"].median(), 3), "nilai_maks": round(d["nilai"].max(), 3),
        })
        for bidang, awal_k in (("satuan", "satuan_awal"), ("kode_sdg", "kode_sdg_awal")):
            if k[awal_k] != ISI and k[awal_k] != k[bidang] and bidang not in k["dilog"]:
                koreksi.append([seri, bidang, k[awal_k], k[bidang],
                                k["bukti_sdg"] if bidang == "kode_sdg" else k["berkas_bukti"],
                                k["alasan_satuan"] if bidang == "satuan" else "Kode SDG disamakan dengan metadata sumber",
                                len(d)])

    if baris_csv:
        JALUR_KATALOG.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(baris_csv).to_csv(JALUR_KATALOG, index=False, encoding="utf-8")
        print(pd.DataFrame(baris_csv)[["seri_kode", "kode_sdg", "satuan", "satuan_sumber", "n_baris",
                                       "nilai_min", "nilai_median", "nilai_maks"]].to_string(index=False))
        print(f"\nDitulis: {JALUR_KATALOG}")
    for m in masalah:
        print(f"GAGAL  {m}")
    if masalah:
        return 1
    if koreksi:
        print("\n--- DRAF BARIS log-keputusan.csv: koreksi katalog (periksa lalu tempel di akhir log) ---")
        print(_draf_log(koreksi))
    else:
        print("\nTidak ada koreksi baru yang perlu dilog (semua *_awal sama dengan nilai ditetapkan, atau sudah dilog).")
    print("LOLOS  katalog seri konsisten dengan Silver")
    return 0


if __name__ == "__main__":
    sys.exit(main())