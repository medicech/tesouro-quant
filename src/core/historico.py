from __future__ import annotations
from pathlib import Path
import pandas as pd

from core.config import PROCESSED_DIR


HIST_PATH = PROCESSED_DIR / "tesouro_historico.parquet"


def append_to_history(df_catalogo: pd.DataFrame) -> Path:
    """
    Adiciona o catálogo do dia no histórico consolidado.
    Evita duplicar (data_base + id_titulo).
    """
    df_new = df_catalogo.copy()
    df_new["data_base"] = pd.to_datetime(df_new["data_base"])
    df_new["data_vencimento"] = pd.to_datetime(df_new["data_vencimento"])

    if HIST_PATH.exists():
        df_old = pd.read_parquet(HIST_PATH)
        df_old["data_base"] = pd.to_datetime(df_old["data_base"])
        df_old["data_vencimento"] = pd.to_datetime(df_old["data_vencimento"])
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    # remove duplicatas
    df_all = df_all.drop_duplicates(subset=["data_base", "id_titulo"]).sort_values(
        ["data_base", "indexador", "cupom_txt", "data_vencimento"]
    )

    df_all.to_parquet(HIST_PATH, index=False)
    return HIST_PATH


def load_history() -> pd.DataFrame:
    if not HIST_PATH.exists():
        raise FileNotFoundError("Histórico ainda não existe. Rode: python scripts/run_fetch.py")
    return pd.read_parquet(HIST_PATH)
