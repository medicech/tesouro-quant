from __future__ import annotations
from pathlib import Path
import pandas as pd

from core.config import PROCESSED_DIR

def latest_catalog_path() -> Path:
    files = sorted(PROCESSED_DIR.glob("tesouro_catalogo_*.parquet"))
    if not files:
        raise FileNotFoundError(
            "Nenhum catálogo encontrado em data/processed. Rode: python scripts/run_fetch.py"
        )
    return files[-1]

def load_latest_catalog() -> pd.DataFrame:
    path = latest_catalog_path()
    df = pd.read_parquet(path)
    return df
