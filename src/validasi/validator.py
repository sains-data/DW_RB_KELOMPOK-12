import sys
sys.path.append(r"D:\python_libs")

import pandas as pd
import pandera.pandas as pa  # Diperbarui sesuai anjuran pandera terbaru

# Skema validasi menggunakan pa.DataFrameSchema dan pa.Column
schema = pa.DataFrameSchema({
    "REF_AREA": pa.Column(str, nullable=False),
    "SEX": pa.Column(str, nullable=False),
    "TIME_PERIOD": pa.Column(int, pa.Check.ge(2000), nullable=False),
    "OBS_VALUE": pa.Column(float, nullable=True),
})

def hitung_metrics_validasi(df, status, failure_cases=None):
    jumlah_kolom = len(schema.columns)
    jumlah_check = sum(len(col.checks) for col in schema.columns.values())
    total_aturan = jumlah_kolom + jumlah_check
    jumlah_gagal = len(failure_cases) if failure_cases is not None else 0
    aturan_lolos = total_aturan if status == "BERHASIL" else max(total_aturan - jumlah_gagal, 0)

    metrics = {
        "status": status,
        "total_baris_diperiksa": len(df),
        "jumlah_kolom_divalidasi": jumlah_kolom,
        "jumlah_check_tambahan": jumlah_check,
        "total_aturan_dijalankan": total_aturan,
        "aturan_lolos": aturan_lolos,
        "jumlah_kasus_gagal": jumlah_gagal,
        "kolom_skema": list(schema.columns.keys()),
    }

    print("\n=== Metrics Aturan Validasi ===")
    for kunci, nilai in metrics.items():
        print(f"- {kunci}: {nilai}")

    return metrics

def validasi_data_silver(df):
    try:
        validated_df = schema.validate(df, lazy=True)
        print("Validasi data Silver BERHASIL: Data sesuai dengan skema ILOSTAT.")
        hitung_metrics_validasi(df, status="BERHASIL", failure_cases=None)
        return validated_df
    except pa.errors.SchemaErrors as err:
        print("Validasi data Silver GAGAL:")
        print(err.failure_cases)
        hitung_metrics_validasi(df, status="GAGAL", failure_cases=err.failure_cases)
        raise err

if __name__ == "__main__":
    file_path = "data/raw/ilostat/2026-10-20/data/DF_SDG_0851_SEX_OCU_NB.csv"
    df = pd.read_csv(file_path)
    validasi_data_silver(df)