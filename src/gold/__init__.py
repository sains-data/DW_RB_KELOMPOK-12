"""Tahap 4-6 - Reshape, integrasi, dan penyimpanan ke Gold. Milik tim."""

from src.gold.tabel_nasional import bangun_tabel_nasional_gold


def jalankan(silver=None):
    """Bangun tabel Gold dan kembalikan kamus {nama_tabel: DataFrame}."""
    tabel_nasional = bangun_tabel_nasional_gold()
    return {"tabel_nasional_gold": tabel_nasional}
