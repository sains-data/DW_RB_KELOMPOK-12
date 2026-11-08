# Kasus 12 — Upah dan pekerjaan informal

Klaster: C. Gender dan ketenagakerjaan  
Tujuan SDG: 8

Paket ini berisi data mentah (lapis Bronze) persis seperti diunduh dari sumbernya pada 17–20 Oktober 2026. Tugas kelompok adalah membangun pipeline yang mengubahnya menjadi tabel Silver (rapi, ber-provenans) lalu tabel Gold (panel siap analisis).

## Seri utama (tingkat provinsi)

| Sumber | Kode seri | Kode SDG | Satuan di katalog | Periode |
|---|---|---|---|---|
| bps | `var1172` | 8.5.1 | rupiah_per_jam | 2015 s.d. 2025 |
| bps | `var2153` | 8.3.1 | tidak_ada | 2018 s.d. 2025 |

## Pembanding nasional

| Sumber | Kode seri | Kode SDG | Periode |
|---|---|---|---|
| ilostat | `SDG_0851_SEX_OCU_NB` | 8.5.1 | 2007 s.d. 2023 |
| ilostat | `SDG_0831_SEX_ECO_RT` | 8.3.1 | 2016 s.d. 2023 |

Satuan dan nama di tabel ini berasal dari katalog awal dan belum tentu benar. Memeriksanya terhadap berkas mentah adalah bagian dari tugas.

## Hal yang perlu diperhatikan

- Upah dalam rupiah nominal; jelaskan apakah dan bagaimana Anda menyesuaikannya dengan inflasi.
- Upah ILO dalam mata uang dan rincian jabatan berbeda; samakan unit sebelum membandingkan.
- Distribusi upah antarprovinsi tidak simetris; pilih transformasi yang tepat.
- Jumlah provinsi berubah antarperiode (pemekaran). Petakan ke susunan 38 provinsi tahun 2025 dan dokumentasikan aturannya.
- Data mentah tidak memuat baris kosong. Missing value baru tampak setelah Anda membentuk grid lengkap wilayah × periode.

## Tahapan dan kaitannya dengan pertemuan

| Tahap | Pertemuan | Keluaran minimal |
|---|---|---|
| 1. Ekstraksi | X | Pembaca untuk tiap format (CSV, JSON, XLSX, SDMX); opsional tarik ulang lewat API dan bandingkan dengan snapshot |
| 2. Profil dan anomali | II–III | Statistik deskriptif, boxplot, z-score/IQR per seri |
| 3. Pembersihan | IV–VI | Strategi missing, penanganan outlier/patahan, deduplikasi, format periode dan wilayah |
| 4. Transformasi | VII, IX | Normalisasi/standarisasi, encoding rincian, reshape ke panel |
| 5. Penyimpanan | XI | Silver di SQL (PostgreSQL/SQLite) dan mentah sebagai dokumen; jelaskan pilihannya |
| 6. Integrasi | XII | Gabungkan seri utama dengan pembanding nasional; jelaskan selisihnya |
| 7. Skala | XIII | Proses arsip WDI 142 rilis (paket bersama) untuk seri pembanding Anda; bandingkan pandas vs DuckDB/Dask |
| 8. Dokumentasi dan validasi | XIV–XV | Lineage tiap nilai ke berkas mentah (sha256), data dictionary, skema pandera/Great Expectations |

## Skema minimal tabel Silver kelompok

`sumber, seri_kode, wilayah_kode, nama_wilayah, periode, jenis_periode, rincian, nilai, satuan, _berkas_raw, _sha256_raw`. Satu baris = satu seri × wilayah × periode × rincian × berkas sumber. Jangan menggabungkan nilai dari sumber berbeda di Silver; rekonsiliasi dilakukan di Gold.

## Isi paket

- `data/raw/` — 10 berkas mentah, struktur folder `<sumber>/<snapshot>/...` dipertahankan.
- `MANIFEST.csv` — ukuran dan sha256 tiap berkas; pakai untuk kolom `_sha256_raw`.
- `LISENSI.md` — lisensi dan atribusi yang wajib dicantumkan.
- Arsip WDI 142 rilis untuk tahap 7 dibagikan terpisah sebagai `wdi-arsip-raw.zip`.

Format laporan dan jadwal mengikuti Buku Pedoman Capstone.
