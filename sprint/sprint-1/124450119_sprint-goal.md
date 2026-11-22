Sprint 1 (9–22 November 2026) — Yulia Kristine Malau (124450119)

Sprint Goal
Dokumentasi skema kolom Silver beserta contoh lineage tersusun jelas dan konsisten, serta integritas berkas mentah terhadap MANIFEST dan keseragaman data_hash antar-anggota tim terverifikasi, sehingga tim memiliki acuan data dan skema yang seragam untuk melangkah ke tahap berikutnya.

Definition of Done yang dipakai
- `docs/data-dictionary.md` memuat 5 atribut per kolom Silver (*Type*, *Unit*, *Definition*, *Source*, dan *Contoh Lineage Silver*) secara jelas dan dapat ditelusuri.
- Verifikasi kecocokan `data/raw` terhadap `MANIFEST.csv` dan konsistensi `data_hash` (`4cf78bc413433b9dc7941096d877ec111a713e3f2339d620f7bb7844173a95a7`) lintas seluruh berkas `results/<NIM>/metrics.json` (`124450049`, `124450065`, `124450097`, `124450102`, dan `124450119`) terkonfirmasi sama persis.
- Metrik acuan (`baris_mentah: 2265`, `null_lineage: 0`, `seri_data: 4` pada `results/124450119/metrics.json` serta `baris_silver: 1362`, `sel_kosong_grid: 16`, `outlier_ditandai: 24`, `seed: 0`, `Windows AMD64 Python 3.14.3`) tercatat dan selaras.
- `reports/individu/124450119.md` dan `results/124450119/metrics.json` sudah di-commit dan di-push ke cabang `124450119/kerja` di repositori `DW_RB_KELOMPOK-12`.