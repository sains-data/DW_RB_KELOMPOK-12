# Laporan Panel Gold (Sprint 2)

## 1. Ringkasan Panel Gold
- Berkas keluaran: `data/gold/panel.parquet`
- Seri utama tingkat provinsi: `var1172` (upah rata-rata per jam) dan `var2153` (proporsi lapangan kerja informal).

## 2. Audit Sel Ganda di Silver (Langkah 4)
- Baris data provinsi yang diaudit: `1324`
- Sel unik `(seri_kode, wilayah_kode, periode)`: `662`
- Sel dengan lebih dari 1 berkas: `662` (karena data BPS tersedia pada berkas CSV dan JSON)
- Sel dengan lebih dari 1 rincian: `0`

## 3. Aturan Satu Nilai per Sel (Mengapa)
- **Rincian `total`:** Dipilih agar perbandingan antarwilayah dan periode berada pada konsep agregat yang setara; rincian spesifik tetap dipertahankan di Silver.
- **Prioritas periode & snapshot deterministik:** Menjamin setiap sel `wilayah_kode x periode x seri_kode` menghasilkan tepat satu nilai yang konsisten setiap kali pipeline dijalankan ulang.

## 4. Sel Kosong & Penanda Anomali
- Sel kosong dipertahankan apa adanya agar tidak mendistorsi analisis statistik atau panel.
- Nilai observasi asli tidak diubah saat menandai anomali; informasi `outlier_ekstrem` dan `status_obs` tetap disimpan untuk pemeriksaan lanjutan.
