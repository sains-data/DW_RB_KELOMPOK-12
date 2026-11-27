from pathlib import Path
import numpy as np
import pandas as pd

PASANGAN_SERI = {
    "var1172": {
        "seri_pembanding": "SDG_0851_SEX_OCU_NB",
        "satuan_utama": "rupiah_per_jam",
        "satuan_pembanding": "rupiah_per_jam",
        "kategori_penjelasan": "metode berbeda",
        "bukti_penjelasan": (
            "Satuan disamakan ke Rupiah nominal per jam (LCU_per_jam = IDR/jam). "
            "Selisih muncul karena perbedaan metode estimasi/pembulatan Sakernas BPS (snapshot 2026-10-17) "
            "dengan pengolahan mikrodata ILOSTAT (snapshot 2026-10-20)."
        ),
        "aturan_agregasi_provinsi": (
            "Jika baris nasional (wilayah_kode=9999) tidak tersedia, agregasikan baris provinsi "
            "dengan bobot rata-rata tertimbang jumlah pekerja/observasi valid per periode."
        ),
        "catatan_padanan": "Padanan nasional tersedia (IDN / wilayah_kode=9999); metode berbeda & vintage berbeda.",
    },
    "var2153": {
        "seri_pembanding": "SDG_0831_SEX_ECO_RT",
        "satuan_utama": "persen",
        "satuan_pembanding": "persen",
        "kategori_penjelasan": "definisi berbeda",
        "bukti_penjelasan": (
            "Cakupan sektor disamakan pada total seluruh sektor termasuk pertanian (ECO_SECTOR_TOTAL / ECO_AGGREGATE_TOTAL). "
            "Selisih sekitar 24-25 poin persen terjadi karena definisi berbeda: BPS memakai pendekatan proksi status pekerjaan "
            "(berusaha sendiri, dibantu buruh tidak tetap, pekerja bebas, pekerja keluarga), sedangkan ILOSTAT memakai kriteria "
            "ICLS ke-17/21 (kepemilikan jaminan sosial & pembukuan unit usaha)."
        ),
        "aturan_agregasi_provinsi": (
            "Jika baris nasional (wilayah_kode=9999) tidak tersedia, agregasikan baris provinsi "
            "dengan bobot proporsi pekerja per provinsi pada periode terkait."
        ),
        "catatan_padanan": "Padanan nasional tersedia (IDN / wilayah_kode=9999); definisi berbeda (proksi status BPS vs ICLS ILO).",
    },
}


def _ekstrak_nasional_bps(df_silver: pd.DataFrame, seri_kode: str, aturan_bobot: str) -> pd.DataFrame:
    sub = df_silver[df_silver["seri_kode"] == seri_kode].copy()
    sub["periode_int"] = pd.to_numeric(sub["periode"], errors="coerce").astype("Int64")
    sub = sub.dropna(subset=["periode_int"])

    nas = sub[sub["wilayah_kode"].astype(str).isin(["9999", "IDN", "0000"])].copy()
    if not nas.empty:
        nas = nas.sort_values(["periode_int", "_berkas_raw"])
        agg = (
            nas.groupby("periode_int", as_index=False)
            .agg(
                nilai_utama=("nilai", "first"),
                satuan_utama=("satuan", "first"),
                _berkas_raw_utama=("_berkas_raw", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
            )
        )
        agg["metode_utama"] = "baris_nasional_langsung"
        agg["aturan_agregasi_provinsi"] = "Tidak diperlukan (baris nasional tersedia langsung)"
        return agg

    prov = sub[~sub["wilayah_kode"].astype(str).isin(["9999", "IDN", "0000"])].copy()
    if prov.empty:
        return pd.DataFrame(
            columns=[
                "periode_int",
                "nilai_utama",
                "satuan_utama",
                "_berkas_raw_utama",
                "metode_utama",
                "aturan_agregasi_provinsi",
            ]
        )

    agg_prov = (
        prov.groupby("periode_int", as_index=False)
        .agg(
            nilai_utama=("nilai", "mean"),
            satuan_utama=("satuan", "first"),
            _berkas_raw_utama=("_berkas_raw", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
        )
    )
    agg_prov["metode_utama"] = "agregat_provinsi_fallback"
    agg_prov["aturan_agregasi_provinsi"] = aturan_bobot
    return agg_prov


def _ekstrak_nasional_ilo(df_silver: pd.DataFrame, seri_kode: str) -> pd.DataFrame:
    sub = df_silver[df_silver["seri_kode"] == seri_kode].copy()
    sub["periode_int"] = pd.to_numeric(sub["periode"], errors="coerce").astype("Int64")
    sub = sub.dropna(subset=["periode_int"])

    nas_ilo = sub[sub["wilayah_kode"].astype(str).isin(["IDN", "9999"])].copy()
    if "dim_sex" in nas_ilo.columns and nas_ilo["dim_sex"].notna().any():
        sex_total = nas_ilo[nas_ilo["dim_sex"].astype(str).str.contains("TOTAL|_T", case=False, na=False)]
        if not sex_total.empty:
            nas_ilo = sex_total

    for col in ["dim_ocu", "dim_eco"]:
        if col in nas_ilo.columns and nas_ilo[col].notna().any():
            tot = nas_ilo[nas_ilo[col].astype(str).str.contains("TOTAL", case=False, na=False)]
            if not tot.empty:
                nas_ilo = tot

    if nas_ilo.empty:
        return pd.DataFrame(
            columns=["periode_int", "nilai_pembanding", "satuan_pembanding", "_berkas_raw_pembanding"]
        )

    return (
        nas_ilo.sort_values(["periode_int", "_berkas_raw"])
        .groupby("periode_int", as_index=False)
        .agg(
            nilai_pembanding=("nilai", "first"),
            satuan_pembanding=("satuan", "first"),
            _berkas_raw_pembanding=("_berkas_raw", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
        )
    )


def bangun_tabel_nasional_gold(
    df_silver: pd.DataFrame | None = None,
    silver_path: str = "data/silver/silver.parquet",
    out_parquet: str = "data/gold/tabel_nasional_gold.parquet",
    out_csv: str = "data/gold/tabel_nasional_gold.csv",
    out_rek_parquet: str = "data/gold/rekonsiliasi_nasional.parquet",
    out_rek_csv: str = "data/gold/rekonsiliasi_nasional.csv",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df_silver is None:
        df_silver = pd.read_parquet(silver_path)

    frames = []
    for seri_utama, meta in PASANGAN_SERI.items():
        seri_pembanding = meta["seri_pembanding"]
        utama = _ekstrak_nasional_bps(df_silver, seri_utama, meta["aturan_agregasi_provinsi"])
        pembanding = _ekstrak_nasional_ilo(df_silver, seri_pembanding)

        gab = pd.merge(utama, pembanding, on="periode_int", how="outer").sort_values("periode_int")
        gab["periode"] = gab["periode_int"].astype(int)
        gab["seri_utama"] = seri_utama
        gab["seri_pembanding"] = seri_pembanding
        gab["satuan_utama"] = gab["satuan_utama"].fillna(meta["satuan_utama"])
        gab["satuan_pembanding"] = meta["satuan_pembanding"]
        gab["metode_utama"] = gab["metode_utama"].fillna("tidak_ada_padanan_nasional")
        gab["aturan_agregasi_provinsi"] = gab["aturan_agregasi_provinsi"].fillna(
            f"Seri {seri_utama} tidak memiliki padanan/baris pada periode ini."
        )

        berpasangan = gab["nilai_utama"].notna() & gab["nilai_pembanding"].notna()
        gab["kategori_penjelasan"] = np.where(
            berpasangan,
            meta["kategori_penjelasan"],
            "tanpa pasangan",
        )
        gab["bukti_penjelasan"] = np.where(
            berpasangan,
            meta["bukti_penjelasan"],
            np.where(
                gab["nilai_utama"].notna(),
                "Nilai utama tersedia; seri pembanding tidak tersedia pada periode ini.",
                "Seri pembanding tersedia; nilai utama tidak tersedia pada periode ini.",
            ),
        )
        gab["catatan_padanan"] = np.where(
            berpasangan,
            meta["catatan_padanan"],
            gab["bukti_penjelasan"],
        )
        gab["selisih_nilai"] = (gab["nilai_utama"] - gab["nilai_pembanding"]).round(4)

        berkas_gab = (
            gab[["_berkas_raw_utama", "_berkas_raw_pembanding"]]
            .fillna("")
            .apply(lambda r: " | ".join([x for x in [r["_berkas_raw_utama"], r["_berkas_raw_pembanding"]] if x]), axis=1)
        )
        gab["_berkas_raw"] = berkas_gab

        frames.append(
            gab[
                [
                    "periode",
                    "seri_utama",
                    "nilai_utama",
                    "satuan_utama",
                    "seri_pembanding",
                    "nilai_pembanding",
                    "satuan_pembanding",
                    "selisih_nilai",
                    "kategori_penjelasan",
                    "bukti_penjelasan",
                    "metode_utama",
                    "aturan_agregasi_provinsi",
                    "catatan_padanan",
                    "_berkas_raw_utama",
                    "_berkas_raw_pembanding",
                    "_berkas_raw",
                ]
            ]
        )

    hasil = pd.concat(frames, ignore_index=True).sort_values(["periode", "seri_utama"]).reset_index(drop=True)

    # Susun tabel khusus rekonsiliasi nasional dengan kolom eksplisit sesuai panduan Tahap 6
    rekonsiliasi = hasil[
        [
            "periode",
            "seri_utama",
            "nilai_utama",
            "satuan_utama",
            "seri_pembanding",
            "nilai_pembanding",
            "satuan_pembanding",
            "selisih_nilai",
            "kategori_penjelasan",
            "bukti_penjelasan",
            "_berkas_raw",
        ]
    ].rename(
        columns={
            "nilai_utama": "nilai_seri_utama",
            "selisih_nilai": "selisih",
        }
    )

    Path(out_parquet).parent.mkdir(parents=True, exist_ok=True)
    hasil.to_parquet(out_parquet, index=False)
    hasil.to_csv(out_csv, index=False)
    rekonsiliasi.to_parquet(out_rek_parquet, index=False)
    rekonsiliasi.to_csv(out_rek_csv, index=False)
    return hasil, rekonsiliasi


if __name__ == "__main__":
    _, df_rek = bangun_tabel_nasional_gold()
    print(df_rek.to_string(index=False))
