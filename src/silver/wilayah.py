"""Susunan 38 provinsi tahun 2025 (kode BPS 2 digit x 100) dan Indonesia (9999).

Dipakai sebagai aturan pemetaan K-001: provinsi induk dibiarkan apa adanya, provinsi baru
hanya berisi tahun sejak berdiri. Penggabungan dilakukan berdasarkan KODE, bukan nama.
"""
from __future__ import annotations

INDONESIA = 9999

NAMA_PROVINSI = {
    1100: "Aceh", 1200: "Sumatera Utara", 1300: "Sumatera Barat", 1400: "Riau",
    1500: "Jambi", 1600: "Sumatera Selatan", 1700: "Bengkulu", 1800: "Lampung",
    1900: "Kepulauan Bangka Belitung", 2100: "Kepulauan Riau",
    3100: "DKI Jakarta", 3200: "Jawa Barat", 3300: "Jawa Tengah",
    3400: "DI Yogyakarta", 3500: "Jawa Timur", 3600: "Banten",
    5100: "Bali", 5200: "Nusa Tenggara Barat", 5300: "Nusa Tenggara Timur",
    6100: "Kalimantan Barat", 6200: "Kalimantan Tengah", 6300: "Kalimantan Selatan",
    6400: "Kalimantan Timur", 6500: "Kalimantan Utara",
    7100: "Sulawesi Utara", 7200: "Sulawesi Tengah", 7300: "Sulawesi Selatan",
    7400: "Sulawesi Tenggara", 7500: "Gorontalo", 7600: "Sulawesi Barat",
    8100: "Maluku", 8200: "Maluku Utara",
    9100: "Papua Barat", 9200: "Papua Barat Daya",
    9400: "Papua", 9500: "Papua Selatan", 9600: "Papua Tengah", 9700: "Papua Pegunungan",
}
KODE_PROVINSI = sorted(NAMA_PROVINSI)

# Tahun berdiri provinsi pemekaran (sel sebelum tahun ini tidak dihitung sebagai missing).
# Kalimantan Utara 2012; empat provinsi baru Papua 2022 (aturan baku bagian 5.1).
BERDIRI = {6500: 2012, 9200: 2022, 9500: 2022, 9600: 2022, 9700: 2022}

assert len(NAMA_PROVINSI) == 38