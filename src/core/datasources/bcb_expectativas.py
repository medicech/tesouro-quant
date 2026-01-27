from __future__ import annotations

from pathlib import Path
import pandas as pd
from bcb import Expectativas

from core.config import PROCESSED_DIR


def fetch_expectativas_anuais(
    indicadores: list[str] | None = None,
    anos: list[int] | None = None,
) -> pd.DataFrame:
    """
    Busca expectativas anuais (Focus/BCB via API Olinda).
    Retorna: data, mediana, indicador, ano

    Importante: NÃO filtramos ep.Data por ano, porque 'Data' é a data de coleta (ex: 2026-01-16),
    e a expectativa pode ser para DataReferencia=2027, 2028 etc.
    """
    if indicadores is None:
        indicadores = ["Selic", "IPCA"]

    if anos is None:
        ano_atual = pd.Timestamp.today().year
        anos = list(range(ano_atual, ano_atual + 11))

    em = Expectativas()
    ep = em.get_endpoint("ExpectativasMercadoAnuais")

    parts: list[pd.DataFrame] = []

    for ind in indicadores:
        for ano in anos:
            try:
                data = (
                    ep.query()
                    .filter(ep.Indicador == ind)
                    .filter(ep.DataReferencia == int(ano))
                    .select(ep.Data, ep.Mediana)
                    .collect()
                )
            except Exception:
                continue

            if data is None:
                continue

            if isinstance(data, pd.DataFrame):
                df = data.copy()
                if df.empty:
                    continue
            else:
                try:
                    if len(data) == 0:
                        continue
                except TypeError:
                    continue
                df = pd.DataFrame(data)

            df = df.rename(columns={"Data": "data", "Mediana": "mediana"})
            if "data" not in df.columns or "mediana" not in df.columns:
                continue

            df["indicador"] = ind
            df["ano"] = int(ano)
            parts.append(df[["data", "mediana", "indicador", "ano"]])

    if not parts:
        return pd.DataFrame(columns=["data", "mediana", "indicador", "ano"])

    out = pd.concat(parts, ignore_index=True)
    out["data"] = pd.to_datetime(out["data"], errors="coerce")
    out["mediana"] = pd.to_numeric(out["mediana"], errors="coerce")
    out = out.dropna(subset=["data", "mediana"]).copy()

    # dedupe: 1 linha por (data, indicador, ano)
    out = (
        out.groupby(["data", "indicador", "ano"], as_index=False)["mediana"]
        .mean()
        .sort_values(["indicador", "ano", "data"])
        .reset_index(drop=True)
    )

    return out


def latest_expectativas_snapshot(df: pd.DataFrame) -> tuple[pd.Timestamp, pd.DataFrame]:
    if df is None or df.empty:
        return pd.NaT, pd.DataFrame(columns=["data", "mediana", "indicador", "ano"])

    data_ref = df["data"].max()
    snap = df[df["data"] == data_ref].copy().sort_values(["indicador", "ano"])
    return data_ref, snap


# =========================
# LOADERS (para o Streamlit)
# =========================

def latest_snapshot_path() -> Path | None:
    """
    Procura o arquivo mais recente do tipo:
    data/processed/expectativas_snapshot_YYYY-MM-DD.parquet
    """
    pattern = "expectativas_snapshot_*.parquet"
    files = sorted(PROCESSED_DIR.glob(pattern))
    if not files:
        return None
    return files[-1]


def load_latest_snapshot() -> pd.DataFrame:
    """
    Carrega o snapshot mais recente salvo em parquet.
    Retorna colunas: data, indicador, ano, mediana
    """
    p = latest_snapshot_path()
    if p is None or not p.exists():
        return pd.DataFrame(columns=["data", "indicador", "ano", "mediana"])

    df = pd.read_parquet(p)
    # normaliza
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    if "mediana" in df.columns:
        df["mediana"] = pd.to_numeric(df["mediana"], errors="coerce")

    # garante ordem
    cols = [c for c in ["data", "indicador", "ano", "mediana"] if c in df.columns]
    df = df[cols].dropna(subset=["data", "indicador", "ano", "mediana"]).copy()
    df = df.sort_values(["indicador", "ano"]).reset_index(drop=True)
    return df


def load_historico() -> pd.DataFrame:
    """
    Carrega o histórico consolidado:
    data/processed/expectativas_historico.parquet
    """
    p = PROCESSED_DIR / "expectativas_historico.parquet"
    if not p.exists():
        return pd.DataFrame(columns=["data", "indicador", "ano", "mediana"])

    df = pd.read_parquet(p)
    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    if "mediana" in df.columns:
        df["mediana"] = pd.to_numeric(df["mediana"], errors="coerce")
    return df.dropna(subset=["data", "indicador", "ano", "mediana"]).copy()
