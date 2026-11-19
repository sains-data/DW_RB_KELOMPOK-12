-- DDL Lapisan Silver — Kasus 12 (Upah dan Pekerjaan Informal)
-- Satu baris = satu seri x wilayah x periode x rincian x berkas sumber
-- Sumber berbeda tidak digabung di Silver; rekonsiliasi dilakukan di Gold.

CREATE TABLE IF NOT EXISTS silver_indikator (
    sumber          VARCHAR(32)   NOT NULL,
    seri_kode       VARCHAR(64)   NOT NULL,
    wilayah_kode    VARCHAR(16)   NOT NULL,
    nama_wilayah    VARCHAR(128)  NOT NULL,
    periode         VARCHAR(16)   NOT NULL,
    jenis_periode   VARCHAR(16)   NOT NULL,
    rincian         VARCHAR(128)  NOT NULL,
    nilai           DOUBLE,
    satuan          VARCHAR(64)   NOT NULL,
    _berkas_raw     VARCHAR(255)  NOT NULL,
    _sha256_raw     CHAR(64)      NOT NULL,
    PRIMARY KEY (sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)
);
