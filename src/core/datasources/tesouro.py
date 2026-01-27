from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import pandas as pd
import requests

from core.config import RAW_DIR

TESOURO_PRECO_TAXA_URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv"
)

@dataclass(frozen=True)
class TesouroOferta:
    data_base: pd.Timestamp
    df_raw: pd.DataFrame


def fetch_precos_taxas_raw(timeout: int = 180) -> pd.DataFrame:
    print("Baixando CSV do Tesouro Transparente...")
    r = requests.get(TESOURO_PRECO_TAXA_URL, timeout=timeout)
    r.raise_for_status()
    print(f"Download ok. Tamanho: {len(r.content)/1024:.1f} KB")

    df = pd.read_csv(
        BytesIO(r.content),
        sep=";",
        decimal=",",
        encoding="utf-8",
        low_memory=False,
    )
    df.columns = [c.strip() for c in df.columns]
    return df


def latest_offer_raw(cache: bool = True) -> TesouroOferta:
    df = fetch_precos_taxas_raw()

    if "Data Base" not in df.columns:
        raise ValueError(f"Coluna 'Data Base' não encontrada. Colunas: {df.columns.tolist()}")

    df["Data Base"] = pd.to_datetime(df["Data Base"], dayfirst=True, errors="coerce")
    data_base = df["Data Base"].max()
    df_hoje = df[df["Data Base"] == data_base].copy()

    if cache:
        out = RAW_DIR / f"tesouro_oferta_raw_{data_base.date().isoformat()}.parquet"
        df_hoje.to_parquet(out, index=False)

    return TesouroOferta(data_base=data_base, df_raw=df_hoje)
