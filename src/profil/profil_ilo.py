import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_ILO = ROOT / "data/raw/ilostat/2026-10-20"
RAW_BPS = ROOT / "data/raw/bps/2026-10-17"
DOCS_DIR = ROOT / "docs"
LOG_PATH = ROOT / "log-keputusan.csv"


def load_codelist_labels(dsd_path: Path) -> dict[str, dict[str, str]]:
    """Ekstrak peta kode -> label dari file DSD SDMX JSON ILOSTAT."""
    data = json.loads(dsd_path.read_text(encoding="utf-8"))
    codelists = data.get("data", {}).get("codelists", [])
    mapping: dict[str, dict[str, str]] = {}
    for cl in codelists:
        cl_id = cl.get("id", "")
        codes = {}
        for item in cl.get("codes", []):
            cid = item.get("id", "")
            names = item.get("names", {})
            label = names.get("en") or item.get("name") or cid
            codes[cid] = label
        mapping[cl_id] = codes
    return mapping


def get_label(cl_map: dict[str, dict[str, str]], prefix: str, code: str) -> str:
    for cl_id, codes in cl_map.items():
        if prefix in cl_id and code in codes:
            return codes[code]
    return code


def format_years(years: list[int]) -> str:
    yrs = sorted(set(int(y) for y in years))
    if not yrs:
        return "-"
    return f"{min(yrs)}-{max(yrs)} ({len(yrs)} thn: {', '.join(map(str, yrs))})"


def classify_candidate(
    seri_kode: str,
    sex: str,
    dim_code: str,
    overlap_years: list[int],
    has_break: bool,
) -> tuple[str, str]:
    """Tentukan status kandidat pembanding seri utama BPS beserta alasan metodologis."""
    if seri_kode == "SDG_0851_SEX_OCU_NB":
        if sex == "SEX_T" and dim_code == "OCU_SKILL_TOTAL":
            alasan = (
                "Kandidat Utama: Agregat total seluruh pekerja & seluruh okupasi, satuan identik "
                "(IDR/Rupiah per jam), mencakup rentang terpanjang (2007-2023) dan beririsan 8 tahun "
                f"dengan BPS ({', '.join(map(str, overlap_years))}). Catatan: terdapat break in series "
                "metodologi ILO pada 2021 dan selisih level nominal akibat perbedaan cakupan status pekerja."
            )
            return "Kandidat Utama", alasan
        if sex == "SEX_T" and dim_code == "OCU_ISCO08_TOTAL":
            alasan = (
                "Kandidat Alternatif: Agregat total berbasis klasifikasi ISCO-08 dengan nilai identik "
                "dengan OCU_SKILL_TOTAL pada 2017-2023 (beririsan 6 tahun dengan BPS), namun tidak "
                "mencakup tahun 2015-2016."
            )
            return "Kandidat Alternatif", alasan
        if sex == "SEX_T" and dim_code == "OCU_ISCO88_TOTAL":
            alasan = (
                "Tidak Dipilih (Historis Terbatas): Klasifikasi ISCO-88 berhenti pada 2015 "
                "(hanya beririsan 1 tahun dengan seri BPS 2015-2025)."
            )
            return "Tidak Sebanding (Cakupan Waktu)", alasan
        alasan = (
            f"Tidak Sebanding (Sub-kelompok): Merupakan rincian berdasarkan jenis kelamin ({sex}) "
            f"dan/atau sub-kategori okupasi ({dim_code}), sedangkan seri utama BPS hanya menyajikan "
            "agregat total nasional."
        )
        return "Tidak Sebanding (Sub-kelompok)", alasan

    if seri_kode == "SDG_0831_SEX_ECO_RT":
        if sex == "SEX_T" and dim_code == "ECO_SECTOR_TOTAL":
            alasan = (
                "Kandidat Utama: Agregat total seluruh pekerja & seluruh sektor ekonomi, satuan identik "
                f"(persentase/PT), beririsan 4 tahun dengan BPS ({', '.join(map(str, overlap_years))}). "
                "Catatan: ILO tidak memiliki observasi 2020-2021 sehingga diperlukan verifikasi definisi "
                "pekerja informal ILO vs proksi status pekerjaan BPS."
            )
            return "Kandidat Utama", alasan
        if sex == "SEX_T" and dim_code == "ECO_AGGREGATE_TOTAL":
            alasan = (
                "Kandidat Alternatif (Duplikat Agregat): Menghasilkan nilai agregat total yang identik "
                "dengan ECO_SECTOR_TOTAL pada seluruh tahun tersedia (2016-2019, 2022-2023); cukup "
                "gunakan satu seri agregat untuk menghindari duplikasi."
            )
            return "Kandidat Alternatif", alasan
        alasan = (
            f"Tidak Sebanding (Sub-kelompok): Merupakan rincian jenis kelamin ({sex}) dan/atau "
            f"sektor ekonomi spesifik ({dim_code}), sedangkan tabel BPS sdg8_informal hanya "
            "memuat agregat total tanpa disaggregasi."
        )
        return "Tidak Sebanding (Sub-kelompok)", alasan

    return "Belum Dievaluasi", "Seri di luar cakupan pemetaan utama."


def build_availability_table() -> pd.DataFrame:
    manifest = json.loads((RAW_BPS / "manifest_asal.json").read_text(encoding="utf-8"))
    bps_upah_years = sorted(int(y) for y in manifest["tabel"]["sdg8_upah"]["tahun"])
    bps_inf_years = sorted(int(y) for y in manifest["tabel"]["sdg8_informal"]["tahun"])

    configs = [
        {
            "seri_kode": "SDG_0851_SEX_OCU_NB",
            "seri_nama": "Rata-rata Upah Per Jam Pekerja (ILOSTAT)",
            "seri_bps_pembanding": "sdg8_upah (Upah Rata-Rata Per Jam Pekerja)",
            "csv_path": RAW_ILO / "data/DF_SDG_0851_SEX_OCU_NB.csv",
            "dsd_path": RAW_ILO / "dsd/SDG_0851_SEX_OCU_NB.json",
            "dim_col": "OCU",
            "dim_prefix": "OCU",
            "bps_years": bps_upah_years,
        },
        {
            "seri_kode": "SDG_0831_SEX_ECO_RT",
            "seri_nama": "Proporsi Pekerja Informal (ILOSTAT)",
            "seri_bps_pembanding": "sdg8_informal (Proporsi Lapangan Kerja Informal)",
            "csv_path": RAW_ILO / "data/DF_SDG_0831_SEX_ECO_RT.csv",
            "dsd_path": RAW_ILO / "dsd/SDG_0831_SEX_ECO_RT.json",
            "dim_col": "ECO",
            "dim_prefix": "ECO",
            "bps_years": bps_inf_years,
        },
    ]

    rows = []
    for cfg in configs:
        df = pd.read_csv(cfg["csv_path"])
        cl_map = load_codelist_labels(cfg["dsd_path"])
        dim_col = cfg["dim_col"]

        for (sex, dim_code), grp in df.groupby(["SEX", dim_col], sort=True):
            years = sorted(int(y) for y in grp["TIME_PERIOD"].dropna().unique())
            overlap = sorted(set(years).intersection(cfg["bps_years"]))
            notes = [
                str(n)
                for n in grp["NOTE_INDICATOR"].dropna().unique()
                if str(n).strip() and str(n).strip() != "nan"
            ]
            has_break = any("Break in series" in n for n in notes)
            status, alasan = classify_candidate(
                cfg["seri_kode"], sex, dim_code, overlap, has_break
            )

            unit_measure = grp["UNIT_MEASURE"].dropna().iloc[0]
            unit_type = grp["UNIT_MEASURE_TYPE"].dropna().iloc[0]
            unit_mult = int(grp["UNIT_MULT"].dropna().iloc[0])

            rows.append(
                {
                    "seri_ilo_kode": cfg["seri_kode"],
                    "seri_ilo_nama": cfg["seri_nama"],
                    "seri_bps_pembanding": cfg["seri_bps_pembanding"],
                    "kode_sex": sex,
                    "label_sex": get_label(cl_map, "SEX", sex),
                    "dimensi_rincian": dim_col,
                    "kode_rincian": dim_code,
                    "label_rincian": get_label(cl_map, cfg["dim_prefix"], dim_code),
                    "satuan": f"{unit_measure} ({unit_type}, 10^{unit_mult})",
                    "jumlah_observasi": len(grp),
                    "tahun_awal": min(years),
                    "tahun_akhir": max(years),
                    "daftar_tahun_ilo": ", ".join(map(str, years)),
                    "jumlah_tahun_ilo": len(years),
                    "tahun_irisan_bps": ", ".join(map(str, overlap)) if overlap else "-",
                    "jumlah_tahun_irisan": len(overlap),
                    "catatan_metodologi": " | ".join(notes) if notes else "-",
                    "status_kandidat": status,
                    "alasan_keterbandingan": alasan,
                }
            )

    out_df = pd.DataFrame(rows)
    # Urutkan agar Kandidat Utama & Alternatif muncul paling atas per seri
    priority = {
        "Kandidat Utama": 1,
        "Kandidat Alternatif": 2,
        "Tidak Sebanding (Cakupan Waktu)": 3,
        "Tidak Sebanding (Sub-kelompok)": 4,
    }
    out_df["_prio"] = out_df["status_kandidat"].map(priority).fillna(9)
    out_df = (
        out_df.sort_values(["seri_ilo_kode", "_prio", "kode_sex", "kode_rincian"])
        .drop(columns=["_prio"])
        .reset_index(drop=True)
    )
    return out_df


def write_markdown_report(avail_df: pd.DataFrame) -> None:
    bps_upah = pd.read_csv(RAW_BPS / "sdg8_upah.csv")
    bps_nat = bps_upah[bps_upah["wilayah_id"] == 9999][["tahun", "nilai"]].rename(
        columns={"tahun": "Tahun", "nilai": "BPS_Nasional_Rp_Jam"}
    )
    ilo_upah = pd.read_csv(RAW_ILO / "data/DF_SDG_0851_SEX_OCU_NB.csv")
    ilo_nat = ilo_upah[
        (ilo_upah["SEX"] == "SEX_T") & (ilo_upah["OCU"] == "OCU_SKILL_TOTAL")
    ][["TIME_PERIOD", "OBS_VALUE", "NOTE_INDICATOR"]].rename(
        columns={
            "TIME_PERIOD": "Tahun",
            "OBS_VALUE": "ILO_SKILL_TOTAL_Rp_Jam",
            "NOTE_INDICATOR": "Catatan_ILO",
        }
    )
    comp_upah = pd.merge(bps_nat, ilo_nat, on="Tahun", how="outer").sort_values("Tahun")
    comp_upah["Selisih_BPS_minus_ILO"] = (
        comp_upah["BPS_Nasional_Rp_Jam"] - comp_upah["ILO_SKILL_TOTAL_Rp_Jam"]
    ).round(2)

    kandidat = avail_df[
        avail_df["status_kandidat"].isin(["Kandidat Utama", "Kandidat Alternatif"])
    ]

    md_lines = [
        "# Profil Data ILOSTAT & Keterbandingan dengan Seri Utama BPS",
        "",
        "Dokumen ini merangkum ketersediaan data ILOSTAT (unduhan `2026-10-20`) untuk indikator SDG 8 Indonesia serta evaluasi keterbandingannya dengan data nasional BPS (`2026-10-17`).",
        "",
        "## 1. Ringkasan Seri dan Cakupan",
        "",
        "| Kode Seri ILO | Indikator | Seri Pembanding BPS | Total Rincian (SEX x Dimensi) | Rentang Tahun ILO | Irisan Tahun dengan BPS |",
        "| :--- | :--- | :--- | :---: | :---: | :---: |",
        "| `SDG_0851_SEX_OCU_NB` | Rata-rata upah per jam pekerja (`LC`, Rupiah/jam) | `sdg8_upah` (2015–2025) | 84 kombinasi (3 SEX × 28 OCU) | 2007–2023 (15 thn; absen 2011, 2018) | 2015–2017, 2019–2023 (8 thn) |",
        "| `SDG_0831_SEX_ECO_RT` | Proporsi lapangan kerja informal (`PT`, Persen) | `sdg8_informal` (2018–2025) | 36 kombinasi (3 SEX × 12 ECO) | 2016–2023 (6 thn; absen 2020–2021) | 2018–2019, 2022–2023 (4 thn) |",
        "",
        "## 2. Rincian Kandidat Sebanding dengan Seri Utama BPS",
        "",
        "Tabel lengkap seluruh 120 kombinasi `seri × periode × rincian` tersimpan di `docs/ketersediaan_ilo.csv`. Berikut adalah rincian yang terpilih sebagai kandidat pembanding seri nasional BPS:",
        "",
    ]

    for _, r in kandidat.iterrows():
        md_lines.extend(
            [
                f"### {r['seri_ilo_kode']} — `{r['kode_sex']}` + `{r['kode_rincian']}` ({r['status_kandidat']})",
                f"- **Seri BPS Pembanding:** {r['seri_bps_pembanding']}",
                f"- **Satuan:** {r['satuan']}",
                f"- **Tahun Tersedia ILO:** {r['daftar_tahun_ilo']}",
                f"- **Tahun Irisan dengan BPS:** {r['tahun_irisan_bps']} ({r['jumlah_tahun_irisan']} tahun)",
                f"- **Alasan & Catatan Metodologis:** {r['alasan_keterbandingan']}",
                "",
            ]
        )

    md_lines.extend(
        [
            "## 3. Perbandingan Nilai Agregat Nasional: BPS vs ILO (`SDG_0851`)",
            "",
            "Perbandingan antara angka nasional BPS (`wilayah_id = 9999`, INDONESIA) dan kandidat utama ILO (`SEX_T`, `OCU_SKILL_TOTAL`):",
            "",
            "| Tahun | BPS Nasional (Rp/Jam) | ILO `OCU_SKILL_TOTAL` (Rp/Jam) | Selisih (BPS - ILO) | Catatan Metodologi ILO |",
            "| :---: | :---: | :---: | :---: | :--- |",
        ]
    )

    for _, r in comp_upah.iterrows():
        yr = int(r["Tahun"])
        bps_v = f"{r['BPS_Nasional_Rp_Jam']:,.2f}" if pd.notna(r["BPS_Nasional_Rp_Jam"]) else "-"
        ilo_v = f"{r['ILO_SKILL_TOTAL_Rp_Jam']:,.2f}" if pd.notna(r["ILO_SKILL_TOTAL_Rp_Jam"]) else "-"
        diff_v = f"{r['Selisih_BPS_minus_ILO']:+,.2f}" if pd.notna(r["Selisih_BPS_minus_ILO"]) else "-"
        note_v = str(r["Catatan_ILO"]) if pd.notna(r["Catatan_ILO"]) else "-"
        md_lines.append(f"| {yr} | {bps_v} | {ilo_v} | {diff_v} | {note_v} |")

    md_lines.extend(
        [
            "",
            "## 4. Kesimpulan Kelayakan Pembandingan",
            "",
            "1. **Kelayakan Lintas Sumber:** Kedua seri ILO (`SEX_T` + `OCU_SKILL_TOTAL` dan `SEX_T` + `ECO_SECTOR_TOTAL`) layak digunakan sebagai pembanding tren makro nasional terhadap seri BPS karena memiliki satuan ukur yang sama (Rupiah/jam dan Persentase) serta sumber mikrodata dasar yang sama (Sakernas).",
            "2. **Batasan Agregasi:** Rincian berdasarkan jenis kelamin (`SEX_M`, `SEX_F`), tingkat keterampilan (`OCU_SKILL_L1..L3-4`), klasifikasi jabatan (`OCU_ISCO*`), maupun sektor ekonomi (`ECO_SECTOR_*`, `ECO_AGGREGATE_*`) tidak dapat dibandingkan langsung dengan tabel BPS saat ini karena tabel BPS hanya memuat angka agregat total.",
            "3. **Penanganan *Break in Series* & Kekosongan Tahun:** Analisis tren upah ILO wajib menandai patahan metodologi (*break in series*) pada tahun **2021**, sementara analisis informal ILO harus memperhitungkan ketiadaan data pada **2020–2021** (masa pandemi COVID-19).",
            "",
        ]
    )

    (DOCS_DIR / "profil_ilo.md").write_text("\n".join(md_lines), encoding="utf-8")


def append_decision_log() -> None:
    new_entries = [
        {
            "tanggal": "2026-11-15",
            "tahap": "Profiling Data ILOSTAT",
            "keputusan": "Menetapkan rincian SEX_T + OCU_SKILL_TOTAL pada SDG_0851_SEX_OCU_NB sebagai kandidat utama pembanding sdg8_upah BPS",
            "alasan": "Satuan identik (IDR/jam), mencakup rentang tahun terpanjang (2007-2023) dengan menggabungkan seri ISCO-88 (<=2015) dan ISCO-08 (>=2017), serta beririsan 8 tahun dengan BPS (2015-2017, 2019-2023). Break in series 2021 dicatat sebagai metadata wajib.",
        },
        {
            "tanggal": "2026-11-15",
            "tahap": "Profiling Data ILOSTAT",
            "keputusan": "Menetapkan rincian SEX_T + ECO_SECTOR_TOTAL pada SDG_0831_SEX_ECO_RT sebagai kandidat utama pembanding sdg8_informal BPS",
            "alasan": "Satuan identik (persentase/PT) dan beririsan 4 tahun dengan BPS (2018-2019, 2022-2023). ECO_AGGREGATE_TOTAL ditandai sebagai kandidat alternatif duplikat, sementara rincian gender dan sektor disingkirkan dari pembandingan langsung karena BPS hanya menyediakan agregat total.",
        },
    ]
    new_df = pd.DataFrame(new_entries)
    if LOG_PATH.exists():
        existing = pd.read_csv(LOG_PATH)
        # Hindari duplikasi jika skrip dijalankan ulang
        existing = existing[
            ~existing["keputusan"].isin(new_df["keputusan"])
        ]
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df
    combined.to_csv(LOG_PATH, index=False, encoding="utf-8")


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    avail_df = build_availability_table()
    out_csv = DOCS_DIR / "ketersediaan_ilo.csv"
    avail_df.to_csv(out_csv, index=False, encoding="utf-8")
    write_markdown_report(avail_df)
    append_decision_log()

    print(f"Tersimpan: {out_csv} ({len(avail_df)} baris kombinasi seri x rincian)")
    print(f"Tersimpan: {DOCS_DIR / 'profil_ilo.md'}")
    print(f"Diperbarui: {LOG_PATH}")
    print("\nRingkasan Status Kandidat:")
    print(avail_df.groupby(["seri_ilo_kode", "status_kandidat"]).size().to_string())


if __name__ == "__main__":
    main()
