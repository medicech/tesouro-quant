from __future__ import annotations

from pathlib import Path
import pandas as pd
import requests

# Selic Meta (BCB/SGS) — série 432
# (Se quiser mudar depois, é só trocar o código.)
SGS_SERIE_SELIC_META = 432
SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados?formato=json"


def fetch_sgs_serie(
    codigo: int,
    start: str | None = None,
    end: str | None = None,
    timeout: int = 60,
) -> pd.DataFrame:
    """
    Baixa uma série do SGS.
    Retorna DataFrame com colunas: data (datetime), valor (float).
    start/end opcionais em 'DD/MM/AAAA'.
    """
    url = SGS_URL.format(codigo=codigo)

    params = {}
    if start:
        params["dataInicial"] = start
    if end:
        params["dataFinal"] = end

    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()

    data = r.json()
    if not data:
        return pd.DataFrame(columns=["data", "valor"])

    df = pd.DataFrame(data)
    # SGS retorna colunas "data" e "valor" como strings
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = (
        df["valor"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )
    df = df.dropna(subset=["data", "valor"]).sort_values("data").reset_index(drop=True)
    return df


def fetch_selic_meta(
    start: str | None = None,
    end: str | None = None,
    timeout: int = 60,
) -> pd.DataFrame:
    """
    Selic Meta (SGS 432).
    """
    return fetch_sgs_serie(SGS_SERIE_SELIC_META, start=start, end=end, timeout=timeout)


def latest_value(df: pd.DataFrame) -> tuple[pd.Timestamp, float]:
    if df is None or df.empty:
        return pd.NaT, float("nan")
    d = df["data"].max()
    v = float(df.loc[df["data"] == d, "valor"].iloc[-1])
    return d, v


def save_selic_meta(df: pd.DataFrame, processed_dir: str | Path) -> Path:
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    out = processed_dir / "selic_meta_sgs.parquet"
    df.to_parquet(out, index=False)
    return out


def load_selic_meta(processed_dir: str | Path) -> pd.DataFrame:
    processed_dir = Path(processed_dir)
    f = processed_dir / "selic_meta_sgs.parquet"
    if not f.exists():
        return pd.DataFrame(columns=["data", "valor"])
    return pd.read_parquet(f)
