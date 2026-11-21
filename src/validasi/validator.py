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

def validasi_data_silver(df):
    try:
        validated_df = schema.validate(df, lazy=True)
        print("Validasi data Silver BERHASIL: Data sesuai dengan skema ILOSTAT.")
        return validated_df
    except pa.errors.SchemaErrors as err:
        print("Validasi data Silver GAGAL:")
        print(err.failure_cases)
        raise err

if __name__ == "__main__":
    file_path = "data/raw/ilostat/2026-10-20/data/DF_SDG_0851_SEX_OCU_NB.csv"
    df = pd.read_csv(file_path)
    validasi_data_silver(df)