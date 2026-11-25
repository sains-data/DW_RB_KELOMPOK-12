"""Tahap 8 - Validasi dasar sementara agar pipeline berjalan."""


def jalankan(silver, gold):
    return {
        "status": "ok",
        "silver_rows": len(silver) if silver is not None else 0,
        "gold_keys": list(gold.keys()) if isinstance(gold, dict) else 0,
    }
