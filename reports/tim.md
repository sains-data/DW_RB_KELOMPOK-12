# Laporan tim — <Nama tim>, kasus <NN> <judul kasus>

Satu dokumen bersama, enam bagian. Angka harus dapat ditarik ulang dari `data/silver`, `data/gold`,
dan `log-keputusan.csv` yang sudah di-*commit*.

## Ringkasan
Kasus, seri yang ditangani, dan satu kalimat temuan utama tentang kualitas datanya.

## Data dan lineage
Sumber dan format mentah, jumlah berkas, cara `_berkas_raw`/`_sha256_raw` dibentuk, dan hasil tarik
ulang API (bila dilakukan): apa yang berubah sejak snapshot 17–20 Oktober 2026.

## Masalah data dan penanganannya

Seluruh temuan pada bagian ini ditarik langsung dari lapisan Silver (`data/silver/silver.parquet`, 1.362 baris), laporan kelengkapan panel (`reports/kelengkapan_panel.csv`), hasil profil Tahap 2 (`reports/profil/`), dan tercatat pada `log-keputusan.csv` (`K-001` s.d. `K-011`).

| Kategori Masalah | Temuan Utama & Angka Terverifikasi | Penanganan & Keputusan | Rujukan Log |
| :--- | :--- | :--- | :--- |
| **Celah panel (Missing)** | Ditemukan **16 sel grid kosong** pada susunan 38 provinsi × periode (kelengkapan turun dari **100,0%** menjadi **89,5%** pada tahun 2022–2023 di `var1172` dan `var2153`). Seluruh celah berasal dari 4 provinsi baru hasil pemekaran Papua (`9200` Papua Barat Daya, `9500` Papua Pegunungan, `9600` Papua Tengah, `9700` Papua Selatan) yang baru diterbitkan BPS mulai 2024. | Dibiarkan kosong (**tidak diimputasi** dan tidak digabung kembali ke provinsi induk) agar tidak menciptakan angka observasi buatan (`dampak_baris = 16`). | `K-001`, `K-008` |
| **Outlier asli** | Distribusi upah menceng kanan dan terdapat **24 observasi ekstrem** lintas provinsi (seperti tingkat upah per jam DKI Jakarta) pada uji $1{,}5 \times \text{IQR}$ (skala log untuk `var1172`, nilai asli untuk `var2153`). | **Ditandai, tidak dihapus atau di-winsorize.** Baris diberi penanda pada kolom `outlier_ekstrem` dengan mempertahankan nilai sumber apa adanya. | `K-007`, `K-011` |
| **Patahan seri** | Pada seri pembanding ILOSTAT (`SDG_0851_SEX_OCU_NB`), terdapat patahan seri resmi pada **2021** (`OBS_STATUS=B`) serta transisi klasifikasi jabatan ISCO-88 ($\le 2015$) ke ISCO-08 ($\ge 2017$). Pada seri BPS (`var1172`, `var2153`), tidak ditemukan patahan serentak lintas provinsi. | **Ditandai dan dijelaskan** pada metadata wajib saat pembandingan lintas sumber tanpa mengubah angka mentah. | `K-002`, `K-003`, `K-011` |
| **Revisi & deduplikasi** | Uji silang pada **681 kunci** BPS (`393` baris `var1172` dan `288` baris `var2153`) antara format CSV dan JSON snapshot `2026-10-17` menghasilkan **0 perbedaan nilai** dan **0 nilai tak terbaca**. | Ditetapkan aturan kunci `(seri_kode, wilayah_kode, periode, rincian)`: nilai identik memakai sumber kanonik CSV, sedangkan nilai berbeda antar-snapshot diperlakukan sebagai revisi dengan memilih snapshot terbaru. | `K-002`, `K-005`, `K-010` |
| **Koreksi katalog & struktur** | (1) Satuan `var2153` pada katalog awal belum eksplisit; (2) Baris agregat **Indonesia (`9999`)** tercampur dalam tabel wilayah; (3) Upah `var1172` masih dalam satuan **nominal (Rupiah/Jam)**; (4) Seri ILOSTAT memuat rincian sub-populasi dan duplikat agregat (`ECO_AGGREGATE_TOTAL`). | (1) Satuan `var2153` ditetapkan sebagai **persen**; (2) Indonesia (`9999`) dipisahkan dari grid 38 provinsi; (3) Deflasi inflasi ditunda ke lapisan Gold sebagai kolom tambahan; (4) Rincian ILOSTAT dikunci pada agregat total (`SEX_T + OCU_SKILL_TOTAL` dan `SEX_T + ECO_SECTOR_TOTAL`). | `K-002`, `K-003`, `K-004`, `K-006`, `K-009` |

## Integrasi dan rekonsiliasi
Seri utama vs pembanding nasional: selisih, penjelasannya (definisi, metode, vintage, granularitas),
dan hasil analisis revisi dari arsip WDI.

## Validasi dan reproduksibilitas
Skema validasi (aturan, hasil lolos/gagal), waktu `python pipeline.py` dari nol, perbandingan pandas
vs DuckDB/Dask, dan keterbatasan yang tersisa.

## Pembagian kerja
| Anggota | NIM | Komponen | Tugas sampingan | Bagian laporan yang ditulis |
|---|---|---|---|---|
