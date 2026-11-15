"""Tahap 2 (profil dan anomali) untuk var1172 (upah per jam) dan var2153 (informalitas).

Tujuan: MENEMUKAN, bukan memperbaiki. Skrip ini hanya membaca tabel masukan dan menulis
ringkasan, daftar calon anomali, dan grafik. Tidak ada nilai yang diubah.

Pakai:
    python src/profil/profil_tahap2.py --silver reports/profil/tabel_profil_bps.csv
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SERI = {
    "var1172": "Upah rata-rata per jam (BPS, SDG 8.5.1)",
    "var2153": "Proporsi lapangan kerja informal (BPS, SDG 8.3.1)",
}
NASIONAL = "9999"
Z_AMBANG = 3.0          # |z| lintas provinsi dalam satu tahun
Z_DELTA_AMBANG = 3.0    # |z| perubahan antar-periode per provinsi
IQR_K = 1.5
PATAHAN_SHARE = 0.8     # >= 80% provinsi bergerak searah dan besar pada tahun yang sama
PATAHAN_BESAR = 0.15    # perubahan relatif dianggap besar bila > 15%


def baca_silver(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, dtype={"wilayah_kode": str})
    df["wilayah_kode"] = df["wilayah_kode"].astype(str)
    df["nilai"] = pd.to_numeric(df["nilai"], errors="coerce")
    df["seri_kode"] = df["seri_kode"].astype(str)
    return df


def pilih_seri(df: pd.DataFrame, kode: str) -> pd.DataFrame:
    return df[df["seri_kode"].str.contains(kode, case=False, regex=False)].copy()


def format_berkas(s: str) -> str:
    return "json" if "/json/" in s or s.lower().endswith(".json") else "csv"


def kanonik(d: pd.DataFrame):
    """Satu baris per kunci (wilayah, periode, rincian). Aturan: snapshot terbaru, lalu CSV.
    Mengembalikan (tabel kanonik, perbandingan csv vs json)."""
    d = d.copy()
    d["_fmt"] = d["_berkas_raw"].map(format_berkas)
    d["_snap"] = d["_berkas_raw"].str.extract(r"(\d{4}-\d{2}-\d{2})")[0]
    kunci = ["wilayah_kode", "periode", "rincian"]
    p = d.pivot_table(index=kunci + ["_snap"], columns="_fmt", values="nilai", aggfunc="first")
    if {"csv", "json"} <= set(p.columns):
        both = p.dropna(subset=["csv", "json"])
        cmp_ = {
            "kunci_di_kedua_format": len(both),
            "kunci_hanya_csv": int(p["json"].isna().sum()),
            "kunci_hanya_json": int(p["csv"].isna().sum()),
            "kunci_beda_nilai": int((~np.isclose(both["csv"], both["json"], rtol=1e-9, atol=1e-9)).sum()),
        }
    else:
        cmp_ = {"kunci_di_kedua_format": 0, "kunci_hanya_csv": int(len(p)), "kunci_hanya_json": 0, "kunci_beda_nilai": 0}
    d["_rank"] = d["_fmt"].map({"csv": 0, "json": 1})
    d = d.sort_values(["_snap", "_rank"], ascending=[False, True])
    return d.drop_duplicates(kunci, keep="first").drop(columns=["_fmt", "_snap", "_rank"]), cmp_


def tahun_dari(periode: pd.Series) -> pd.Series:
    return pd.to_numeric(periode.astype(str).str[:4], errors="coerce")


def anomali_seri(prov: pd.DataFrame, kode: str, total: str) -> list:
    out = []
    d = prov[prov["rincian"] == total].copy()
    # 1. ekstrem lintas provinsi per periode: z-score dan IQR (outlier asli -> ditandai saja)
    for per, g in d.groupby("periode"):
        if len(g) < 8:
            continue
        mu, sd = g["nilai"].mean(), g["nilai"].std(ddof=0)
        q1, q3 = g["nilai"].quantile([.25, .75])
        iqr = q3 - q1
        lo, hi = q1 - IQR_K * iqr, q3 + IQR_K * iqr
        for _, r in g.iterrows():
            z = (r["nilai"] - mu) / sd if sd > 0 else 0.0
            alasan = []
            if abs(z) >= Z_AMBANG:
                alasan.append(f"z={z:.2f} lintas provinsi")
            if r["nilai"] < lo or r["nilai"] > hi:
                alasan.append(f"di luar pagar IQR [{lo:.4g}; {hi:.4g}]")
            if alasan:
                out.append(dict(seri_kode=kode, jenis="ekstrem_lintas_provinsi", wilayah_kode=r["wilayah_kode"],
                                nama_wilayah=r["nama_wilayah"], periode=per, nilai=r["nilai"],
                                alasan="; ".join(alasan)))
    # 2. loncatan antar-periode per provinsi (galat input atau patahan)
    d = d.sort_values(["wilayah_kode", "periode"])
    d["delta_rel"] = d.groupby("wilayah_kode")["nilai"].pct_change()
    d["delta_abs"] = d.groupby("wilayah_kode")["nilai"].diff()
    for _, g in d.groupby("wilayah_kode"):
        x = g["delta_rel"].dropna()
        if len(x) < 4 or x.std(ddof=0) == 0:
            continue
        zz = (x - x.mean()) / x.std(ddof=0)
        for idx in zz[zz.abs() >= Z_DELTA_AMBANG].index:
            r = g.loc[idx]
            out.append(dict(seri_kode=kode, jenis="loncatan_antar_periode", wilayah_kode=r["wilayah_kode"],
                            nama_wilayah=r["nama_wilayah"], periode=r["periode"], nilai=r["nilai"],
                            alasan=f"perubahan {r['delta_rel']*100:+.1f}% dari periode sebelumnya (z={zz[idx]:.2f})"))
    # 3. calon patahan seri: hampir semua provinsi bergerak searah dan besar pada periode yang sama
    for per, g in d.dropna(subset=["delta_rel"]).groupby("periode"):
        if len(g) < 8:
            continue
        naik = (g["delta_rel"] > PATAHAN_BESAR).mean()
        turun = (g["delta_rel"] < -PATAHAN_BESAR).mean()
        if max(naik, turun) >= PATAHAN_SHARE:
            arah = "naik" if naik >= turun else "turun"
            out.append(dict(seri_kode=kode, jenis="calon_patahan_seri", wilayah_kode="semua", nama_wilayah="(serentak)",
                            periode=per, nilai=g["delta_rel"].median(),
                            alasan=f"{max(naik, turun)*100:.0f}% provinsi {arah} >{PATAHAN_BESAR*100:.0f}% (median {g['delta_rel'].median()*100:+.1f}%); cek metadata definisi"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--silver", default="data/silver/silver.parquet")
    ap.add_argument("--out", default="reports")
    a = ap.parse_args()
    out = Path(a.out)
    (out / "profil").mkdir(parents=True, exist_ok=True)
    (out / "gambar").mkdir(parents=True, exist_ok=True)

    df = baca_silver(Path(a.silver))
    ringkas, per_prov, prov_thn, rinci, cmp_rows, anom = [], [], [], [], [], []
    gambar = []

    for kode, judul in SERI.items():
        s = pilih_seri(df, kode)
        if s.empty:
            print(f"PERINGATAN: {kode} tidak ada di Silver", file=sys.stderr)
            continue
        n_mentah = len(s)
        s, cmp_ = kanonik(s)
        cmp_rows.append({"seri_kode": kode, "baris_silver": n_mentah, "baris_kanonik": len(s), **cmp_})
        s["tahun"] = tahun_dari(s["periode"])
        nas = s[s["wilayah_kode"] == NASIONAL]
        prov = s[s["wilayah_kode"] != NASIONAL]
        rincian_total = "total" if (s["rincian"] == "total").any() else s["rincian"].mode().iat[0]
        pt = prov[prov["rincian"] == rincian_total]

        satuan = ", ".join(sorted(s["satuan"].fillna("(kosong)").astype(str).unique()))
        ringkas.append(dict(
            seri_kode=kode, judul=judul, satuan=satuan, n_baris=len(s),
            periode_min=s["periode"].min(), periode_max=s["periode"].max(),
            jenis_periode=", ".join(sorted(s["jenis_periode"].fillna("(kosong)").astype(str).unique())),
            n_provinsi_unik=prov["wilayah_kode"].nunique(), ada_baris_indonesia=bool(len(nas)),
            n_rincian=s["rincian"].nunique(),
            kelengkapan_grid_total=round(len(pt) / (pt["wilayah_kode"].nunique() * pt["periode"].nunique()), 4) if len(pt) else np.nan,
            min=pt["nilai"].min(), q1=pt["nilai"].quantile(.25), median=pt["nilai"].median(),
            mean=pt["nilai"].mean(), q3=pt["nilai"].quantile(.75), max=pt["nilai"].max(),
            sd=pt["nilai"].std(), skew=pt["nilai"].skew(),
            nilai_nonpositif=int((pt["nilai"] <= 0).sum()), nilai_di_atas_100=int((pt["nilai"] > 100).sum()),
        ))
        for r_, g in s.groupby("rincian"):
            rinci.append(dict(seri_kode=kode, rincian=r_, n_baris=len(g), periode_min=g["periode"].min(), periode_max=g["periode"].max()))
        for per, g in prov.groupby("periode"):
            prov_thn.append(dict(seri_kode=kode, periode=per, n_provinsi=g["wilayah_kode"].nunique(),
                                 kode_provinsi=" ".join(sorted(g["wilayah_kode"].unique()))))
        gp = pt.groupby(["wilayah_kode", "nama_wilayah"])["nilai"].agg(["count", "min", "median", "mean", "max", "std"]).reset_index()
        gp["cv"] = gp["std"] / gp["mean"]
        gp.insert(0, "seri_kode", kode)
        per_prov.append(gp)
        anom += anomali_seri(prov, kode, rincian_total)

        # grafik 1: boxplot per periode (lintas provinsi)
        per_list = sorted(pt["periode"].unique())
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.boxplot([pt.loc[pt["periode"] == p, "nilai"] for p in per_list], tick_labels=per_list, whis=IQR_K)
        ax.set_title(f"{kode}: sebaran antarprovinsi per periode ({rincian_total})")
        ax.set_xlabel("Periode"); ax.set_ylabel(f"Nilai ({satuan})"); ax.tick_params(axis="x", rotation=45)
        fig.tight_layout(); f = out / "gambar" / f"{kode}_boxplot_periode.png"; fig.savefig(f, dpi=150); plt.close(fig); gambar.append(f)

        # grafik 2: deret waktu semua provinsi (abu), Indonesia dan provinsi anomali disorot
        fig, ax = plt.subplots(figsize=(10, 5))
        for _, g in pt.sort_values("periode").groupby("wilayah_kode"):
            ax.plot(g["periode"], g["nilai"], color="0.8", lw=0.8)
        if len(nas):
            n = nas[nas["rincian"] == rincian_total].sort_values("periode")
            ax.plot(n["periode"], n["nilai"], color="black", lw=2, label="Indonesia (9999)")
        ek = [x for x in anom if x["seri_kode"] == kode and x["jenis"] == "ekstrem_lintas_provinsi"]
        for kd in pd.Series([x["wilayah_kode"] for x in ek]).value_counts().head(5).index:
            g = pt[pt["wilayah_kode"] == kd].sort_values("periode")
            ax.plot(g["periode"], g["nilai"], lw=1.6, label=f"{g['nama_wilayah'].iat[0]} ({kd})")
        ax.set_title(f"{kode}: deret waktu per provinsi ({rincian_total})")
        ax.set_xlabel("Periode"); ax.set_ylabel(f"Nilai ({satuan})"); ax.tick_params(axis="x", rotation=45)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=8)
        fig.tight_layout(); f = out / "gambar" / f"{kode}_deret_waktu.png"; fig.savefig(f, dpi=150); plt.close(fig); gambar.append(f)

        # grafik 3: histogram untuk melihat kemencengan
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(pt["nilai"].dropna(), bins=30)
        ax.set_title(f"{kode}: distribusi nilai provinsi x periode (skew={pt['nilai'].skew():.2f})")
        ax.set_xlabel(f"Nilai ({satuan})"); ax.set_ylabel("Frekuensi")
        fig.tight_layout(); f = out / "gambar" / f"{kode}_histogram.png"; fig.savefig(f, dpi=150); plt.close(fig); gambar.append(f)

    R = pd.DataFrame(ringkas); P = pd.concat(per_prov) if per_prov else pd.DataFrame()
    PT = pd.DataFrame(prov_thn); RI = pd.DataFrame(rinci); C = pd.DataFrame(cmp_rows); A = pd.DataFrame(anom)
    for nama, t in [("ringkasan_seri", R), ("per_provinsi", P), ("provinsi_per_tahun", PT),
                    ("rincian_per_seri", RI), ("csv_vs_json", C), ("anomali", A)]:
        t.to_csv(out / "profil" / f"{nama}.csv", index=False)

    md = ["# Profil Tahap 2: var1172 dan var2153", "",
          "Dihasilkan oleh `src/profil/profil_tahap2.py`. Tujuan: menemukan, bukan memperbaiki. "
          "Tidak ada nilai yang diubah. Semua angka di bawah dapat dihasilkan ulang dengan skrip itu.", "",
          f"Ambang: |z| >= {Z_AMBANG} (lintas provinsi per periode dan perubahan antar-periode per provinsi); "
          f"pagar IQR {IQR_K}xIQR; calon patahan bila >= {PATAHAN_SHARE*100:.0f}% provinsi bergerak searah > {PATAHAN_BESAR*100:.0f}%.", "",
          "## Ringkasan per seri", "", R.round(3).to_markdown(index=False) if len(R) else "(kosong)", "",
          "## Uji silang CSV vs JSON", "", C.to_markdown(index=False) if len(C) else "(kosong)", "",
          "## Jumlah provinsi per periode", ""]
    if len(PT):
        md.append(PT.drop(columns="kode_provinsi").to_markdown(index=False))
    md += ["", "## Calon anomali (ditandai, tidak diubah)", ""]
    md.append(A.round(4).to_markdown(index=False) if len(A) else "Tidak ada calon anomali yang melewati ambang.")
    md += ["", "## Grafik", ""] + [f"- ![{g.stem}](gambar/{g.name})" for g in gambar]
    md += ["", "## Hal yang perlu diputuskan di log (bukan dikerjakan di tahap ini)", "",
           "- Satuan `var2153`: bandingkan besaran nilai dengan kolom `satuan` di atas.",
           "- Apakah `var1172` nominal atau riil, dan apakah ada patahan serentak (lihat `calon_patahan_seri`).",
           "- Provinsi baru hasil pemekaran (Kaltara, empat provinsi Papua): lihat tabel jumlah provinsi per periode."]
    (out / "profil-tahap2.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Selesai: {len(A)} calon anomali, {len(gambar)} grafik, ringkasan di {out/'profil-tahap2.md'}")


if __name__ == "__main__":
    main()

