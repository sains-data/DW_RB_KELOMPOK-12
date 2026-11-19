# Tugas #11 — Rancangan Skema SQL Silver dan Pemilihan Basis Data

## 1. Pilihan Basis Data: DuckDB
Untuk penyimpanan lapisan **Silver** (`data/silver.duckdb`), tim memilih **DuckDB** dengan pertimbangan berikut:
1. **Reproduksibilitas Tanpa Server (*Serverless / Embedded*):** Berjalan langsung dari satu berkas lokal tanpa perlu instalasi atau konfigurasi layanan server terpisah (berbeda dengan PostgreSQL), sehingga seluruh anggota tim dan pengujian klon bersih (*clean clone*) dapat mengeksekusinya secara identik.
2. **Performa Analitik Kolumnar (OLAP):** Lebih cepat dibanding SQLite untuk operasi agregasi, *window function*, pembentukan grid lengkap wilayah × periode, serta pemrosesan skala besar pada Tahap 7 (arsip WDI 142 rilis).
3. **Dukungan Tipe Data & SQL Standar:** Mendukung penuh tipe data presisi (`DOUBLE`, `CHAR(64)`, `VARCHAR`), kunci primer komposit, serta integrasi langsung dengan Python dan Pandas/Parquet.

## 2. Perbandingan Singkat: Tabel SQL Silver vs Dokumen JSON Mentah

| Aspek | Tabel SQL Terstruktur (Lapisan Silver — DuckDB) | Dokumen JSON Mentah (Lapisan Bronze) |
| :--- | :--- | :--- |
| **Struktur & Validasi Skema** | Skema ketat (*schema-on-write*) dengan tipe kolom eksplisit dan kunci primer komposit untuk mencegah duplikasi baris. | Fleksibel (*schema-less*), struktur bersarang (*nested*) berbeda antara BPS (`sdg8_upah.json`) dan ILOSTAT (`dataflow.json`). |
| **Kueri & Pembersihan** | Efisien untuk *filtering*, pengecekan *missing value* pada grid wilayah × periode, dan audit provenans (`_sha256_raw`). | Sulit di-kueri lintas sumber secara langsung; membutuhkan *parsing* berulang setiap kali analisis dijalankan. |
| **Peran dalam Pipeline** | Menyimpan data bersih yang terstandardisasi per sumber untuk siap direkonsiliasi ke lapisan Gold. | Menyimpan arsip autentik apa adanya dari sumber asli sebagai jejak audit (*lineage*) yang tidak boleh diubah. |

## 3. Definisi Kunci Primer & Tipe Kolom (`sql/schema_silver.sql`)
* **Kunci Primer Komposit:** `(sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)` — menjamin keunikan butir observasi tanpa menggabungkan nilai antar sumber yang berbeda.
* **Tipe Kolom:** `VARCHAR` untuk pengenal kategorikal, `DOUBLE` untuk `nilai` numerik (mengakomodasi nilai desimal dan `NULL`), serta `CHAR(64)` untuk `_sha256_raw` sesuai panjang hash SHA-256.
