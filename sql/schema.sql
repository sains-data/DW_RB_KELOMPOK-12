-- DDL Lapisan Silver & Gold — Kasus 12 (Upah dan Pekerjaan Informal)
-- Engine: DuckDB
-- Lanjutan rancangan skema Sprint 1 (sql/schema_silver.sql)

-- 1. Tabel Silver (2.265 baris): tingkat provinsi x seri x periode x rincian x berkas
CREATE TABLE IF NOT EXISTS silver_indikator (
    sumber          VARCHAR(32)   NOT NULL,
    seri_kode       VARCHAR(64)   NOT NULL,
    wilayah_kode    BIGINT        NOT NULL,
    nama_wilayah    VARCHAR(128)  NOT NULL,
    periode         VARCHAR(16)   NOT NULL,
    jenis_periode   VARCHAR(16)   NOT NULL,
    rincian         VARCHAR(128)  NOT NULL,
    nilai           DOUBLE,
    satuan          VARCHAR(64)   NOT NULL,
    _berkas_raw     VARCHAR(255)  NOT NULL,
    _sha256_raw     CHAR(64)      NOT NULL,
    outlier_ekstrem BOOLEAN,
    status_obs      VARCHAR(64),
    dim_sex         VARCHAR(32),
    dim_ocu         VARCHAR(64),
    dim_eco         VARCHAR(64),
    PRIMARY KEY (sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)
);

-- 2. Tabel Panel Gold (681 baris): panel provinsi terdeduplikasi + variabel turunan (upah_riil, log_upah)
CREATE TABLE IF NOT EXISTS gold_panel (
    sumber          VARCHAR(32)   NOT NULL,
    seri_kode       VARCHAR(64)   NOT NULL,
    wilayah_kode    BIGINT        NOT NULL,
    nama_wilayah    VARCHAR(128)  NOT NULL,
    periode         VARCHAR(16)   NOT NULL,
    jenis_periode   VARCHAR(16)   NOT NULL,
    rincian         VARCHAR(128)  NOT NULL,
    nilai           DOUBLE,
    satuan          VARCHAR(64)   NOT NULL,
    _berkas_raw     VARCHAR(255)  NOT NULL,
    _sha256_raw     CHAR(64)      NOT NULL,
    outlier_ekstrem BOOLEAN,
    status_obs      VARCHAR(64),
    dim_sex         VARCHAR(32),
    dim_ocu         VARCHAR(64),
    dim_eco         VARCHAR(64),
    upah_riil       DOUBLE,
    log_upah        DOUBLE,
    PRIMARY KEY (sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)
);

-- 3. Tabel Nasional Gold (28 baris): perbandingan seri utama BPS vs pembanding ILOSTAT per periode
CREATE TABLE IF NOT EXISTS gold_tabel_nasional (
    periode                  BIGINT        NOT NULL,
    seri_utama               VARCHAR(64)   NOT NULL,
    nilai_utama              DOUBLE,
    satuan_utama             VARCHAR(64)   NOT NULL,
    seri_pembanding          VARCHAR(64)   NOT NULL,
    nilai_pembanding         DOUBLE,
    satuan_pembanding        VARCHAR(64)   NOT NULL,
    selisih_nilai            DOUBLE,
    kategori_penjelasan      VARCHAR(128),
    bukti_penjelasan         VARCHAR(512),
    metode_utama             VARCHAR(128),
    aturan_agregasi_provinsi VARCHAR(255),
    catatan_padanan          VARCHAR(512),
    _berkas_raw_utama        VARCHAR(255),
    _berkas_raw_pembanding   VARCHAR(255),
    _berkas_raw              VARCHAR(255),
    PRIMARY KEY (periode, seri_utama, seri_pembanding)
);

-- 4. Tabel Rekonsiliasi Gold (28 baris): audit selisih dan kategori penjelasan antar sumber
CREATE TABLE IF NOT EXISTS gold_rekonsiliasi (
    periode             BIGINT        NOT NULL,
    seri_utama          VARCHAR(64)   NOT NULL,
    nilai_seri_utama    DOUBLE,
    satuan_utama        VARCHAR(64)   NOT NULL,
    seri_pembanding     VARCHAR(64)   NOT NULL,
    nilai_pembanding    DOUBLE,
    satuan_pembanding   VARCHAR(64)   NOT NULL,
    selisih             DOUBLE,
    kategori_penjelasan VARCHAR(128),
    bukti_penjelasan    VARCHAR(512),
    _berkas_raw         VARCHAR(255),
    PRIMARY KEY (periode, seri_utama, seri_pembanding)
);
