"""Tahap 4-6 - Reshape, integrasi, dan penyimpanan ke Gold. Milik tim.

Tahap 4 (modul ini): panel provinsi x periode x indikator untuk var1172 dan var2153 ->
data/gold/panel_provinsi_sdg8.parquet (panjang) dan panel_provinsi_sdg8_lebar.parquet (turunan).
Tabel nasional/rekonsiliasi (Tahap 6) tetap dibangun oleh tabel_nasional.py.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

import pandas as pd

from src.gold.tabel_nasional import bangun_tabel_nasional_gold
from src.silver import NIM

from .panel import bangun_panel, bentuk_lebar

KODE_LOG_MULAI_GOLD = 21  # <-- nomor K- berikutnya setelah K-020 di log-keputusan.csv
JALUR_PANEL = Path("data/gold/panel_provinsi_sdg8.parquet")
JALUR_LEBAR = Path("data/gold/panel_provinsi_sdg8_lebar.parquet")


def _draf_log(stat: dict, nim: str, mulai: int) -> str:
    """Draf baris log-keputusan.csv (13 kolom) untuk keputusan Tahap 4. Periksa dulu, lalu tempel di akhir log."""
    baris = []
    tgl = pd.Timestamp.now().strftime("%Y-%m-%d")

    def tambah(keputusan, alternatif, alasan, dampak, aturan="", sebelum="", sesudah="", tidak=""):
        baris.append([f"K-{mulai + len(baris):03d}", tgl, nim, "gold", "var1172;var2153", keputusan,
                      alternatif, alasan, dampak, aturan, sebelum, sesudah, tidak])

    tambah("Sumber kanonik CSV dipilih eksplisit sebelum aturan K-018 s.d. K-020, sehingga baris JSON tidak masuk panel",
           "Membiarkan pilih_periode_panel memilih CSV atau JSON lewat pengurutan yang tidak dijamin stabil",
           "K-005 menetapkan CSV kanonik; nilai CSV dan JSON identik tetapi keterlacakan harus menunjuk berkas yang sama setiap kali",
           stat["baris_bukan_kanonik"], "sumber_kanonik_csv", stat["baris_silver"],
           stat["baris_silver"] - stat["baris_bukan_kanonik"], stat["baris_bukan_kanonik"])
    tambah("Panel Gold memuat 38 provinsi (baris Indonesia 9999 dikeluarkan) pada grid sel yang diharapkan; "
           f"{stat['sel_kosong']} sel kosong (Papua 2022-2023) tetap menjadi baris dengan nilai kosong dan status_sel=belum_disurvei",
           "Membuang sel kosong dari panel, atau mengisinya dengan imputasi",
           "Mengikuti K-006 dan K-008: agregat nasional dipisah, nilai yang tidak pernah diamati tidak dikarang",
           stat["sel_kosong"], "grid_provinsi_periode", stat["baris_bps_pilihan"] - stat["baris_nasional_dikeluarkan"],
           stat["baris_gold"], "")
    tambah("Satuan tidak dicampur: upah nominal di kolom upah_nominal_rp_jam (rupiah_per_jam), proporsi informal di kolom "
           "informal_persen (persen); nilai asli tidak diubah, log_upah_nominal dan log_upah_riil ditambahkan sebagai kolom turunan",
           "Satu kolom nilai untuk kedua seri; menimpa nilai asli dengan hasil transformasi",
           "Besaran berbeda satuan tidak boleh berada dalam satu kolom; versi asli harus tetap ada",
           stat["baris_gold"], "satuan_per_kolom", "", "", "")
    if stat["ihk_ada"]:
        tambah(f"Upah riil = upah nominal x 100 / IHK (tahun dasar {stat['tahun_dasar']}=100) dari data/ref/ihk_tahunan.csv "
               f"(sha256 {stat['ihk_sha'][:12]}...); provinsi tanpa IHK sendiri memakai IHK nasional dan ditandai ihk_cakupan",
               "Mendeflasi di Silver; memakai nilai nominal sebagai upah riil",
               "K-009: deflasi ditunda ke Gold dengan sumber indeks tercatat",
               stat["riil_terisi"], "upah_riil_ihk")
    else:
        tambah("Upah riil belum dihitung: berkas IHK data/ref/ihk_tahunan.csv tidak tersedia, kolom upah_riil_rp_jam dibiarkan kosong",
               "Mengisi upah riil dengan angka nominal atau IHK karangan",
               "K-009 mewajibkan indeks harga bersumber; tanpa sumber, kolom dibiarkan kosong",
               0, "upah_riil_ihk")
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(baris)
    return buf.getvalue()


def jalankan(silver: pd.DataFrame) -> dict:
    """Bangun dan tulis Gold Tahap 4; kembalikan kamus {nama_tabel: DataFrame}."""
    panel, logs, stat = bangun_panel(silver)
    lebar = bentuk_lebar(panel)
    JALUR_PANEL.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(JALUR_PANEL, index=False)
    lebar.to_parquet(JALUR_LEBAR, index=False)
    tabel_nasional = bangun_tabel_nasional_gold()  # Tahap 6, membaca data/silver/silver.parquet

    from src.gold.deflator import JALUR_IHK
    from src.common.manifest import sha256
    stat["ihk_sha"] = sha256(JALUR_IHK) if stat["ihk_ada"] else ""

    print("=== GOLD: PANEL PROVINSI x PERIODE x INDIKATOR (TAHAP 4) ===")
    print(f"baris Silver masuk     : {stat['baris_silver']} (bukan CSV kanonik dilepas: {stat['baris_bukan_kanonik']})")
    for l in logs:
        print(f"aturan {l['aturan']:<28}: {l['baris_sebelum']} -> {l['baris_sesudah']} (tidak terpilih {l['jumlah_baris_tidak_terpilih']})")
    print(f"baris nasional (9999)  : {stat['baris_nasional_dikeluarkan']} dikeluarkan dari panel (K-006)")
    print(f"panel panjang          : {stat['baris_gold']} baris, {stat['seri_panel']} seri "
          f"(terisi {stat['sel_terisi']}, belum_disurvei {stat['sel_kosong']}) -> {JALUR_PANEL}")
    print(f"panel lebar (turunan)  : {len(lebar)} baris -> {JALUR_LEBAR}")
    if stat["ihk_ada"]:
        print(f"upah riil              : {stat['riil_terisi']} sel terisi (tahun dasar {stat['tahun_dasar']}=100)")
    else:
        print("PERINGATAN upah riil   : data/ref/ihk_tahunan.csv tidak ada; upah_riil_rp_jam dibiarkan kosong")
    print(f"tabel nasional (Tahap 6): {len(tabel_nasional)} baris")
    print("\n--- DRAF BARIS log-keputusan.csv (periksa, sesuaikan, lalu tempel di akhir log) ---")
    print(_draf_log(stat, NIM, KODE_LOG_MULAI_GOLD))
    print("--- PERINTAH metrics.json (sertakan metrik Sprint 1) ---")
    print(f"python -m src.common.hasil {NIM} seri_silver={int(silver['seri_kode'].nunique())} "
          f"rincian_dienkode={int(silver['rincian'].nunique())} baris_silver={len(silver)} "
          f"seri_panel={stat['seri_panel']} baris_gold={stat['baris_gold']}")
    return {"panel_provinsi_sdg8": panel, "panel_provinsi_sdg8_lebar": lebar,
            "tabel_nasional_gold": tabel_nasional}