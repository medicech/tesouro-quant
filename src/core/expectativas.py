from __future__ import annotations
from pathlib import Path
import pandas as pd

from core.config import PROCESSED_DIR

HIST_PATH = PROCESSED_DIR / "expectativas_historico.parquet"


def append_expectativas_history(df_new: pd.DataFrame) -> Path:
    """
    Histórico consolidado (data + indicador + ano).
    """
    if df_new is None or df_new.empty:
        return HIST_PATH

    df_new = df_new.copy()
    df_new["data"] = pd.to_datetime(df_new["data"])

    if HIST_PATH.exists():
        df_old = pd.read_parquet(HIST_PATH)
        df_old["data"] = pd.to_datetime(df_old["data"])
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all = (
        df_all.drop_duplicates(subset=["data", "indicador", "ano"])
        .sort_values(["data", "indicador", "ano"])
        .reset_index(drop=True)
    )

    df_all.to_parquet(HIST_PATH, index=False)
    return HIST_PATH


def load_expectativas_history() -> pd.DataFrame:
    if not HIST_PATH.exists():
        raise FileNotFoundError("Histórico de expectativas não existe. Rode: python scripts/run_fetch_expectativas.py")
    df = pd.read_parquet(HIST_PATH)
    df["data"] = pd.to_datetime(df["data"])
    return df


def latest_expectativas_date(df: pd.DataFrame) -> pd.Timestamp:
    if df is None or df.empty:
        return pd.NaT
    return pd.to_datetime(df["data"]).max()


def load_latest_expectativas_snapshot() -> pd.DataFrame:
    """
    Retorna o snapshot mais recente (última data disponível) de TODOS os indicadores/anos.
    """
    df = load_expectativas_history()
    last_date = latest_expectativas_date(df)
    if pd.isna(last_date):
        return df.iloc[0:0].copy()
    snap = df[df["data"] == last_date].copy().sort_values(["indicador", "ano"])
    return snap


def get_latest_focus_value(indicador: str, ano: int) -> tuple[pd.Timestamp, float | None]:
    """
    Retorna (data_ref, mediana) do snapshot mais recente para um indicador/ano.
    Ex: ("IPCA", 2026) -> (2026-01-16, 4.0211)
    """
    snap = load_latest_expectativas_snapshot()
    if snap.empty:
        return pd.NaT, None

    dff = snap[(snap["indicador"] == indicador) & (snap["ano"] == int(ano))]
    if dff.empty:
        return pd.to_datetime(snap["data"].max()), None

    data_ref = pd.to_datetime(dff["data"].iloc[0])
    val = float(dff["mediana"].iloc[0])
    return data_ref, val
