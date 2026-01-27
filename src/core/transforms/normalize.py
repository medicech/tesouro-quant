from __future__ import annotations
import pandas as pd


def _parse_vencimento(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, dayfirst=True, errors="coerce")


def _infer_indexador(tipo_titulo: str) -> str:
    t = (tipo_titulo or "").lower()
    if "selic" in t:
        return "SELIC"
    if "ipca" in t:
        return "IPCA"
    if "prefix" in t:
        return "PREFIXADO"
    return "OUTROS"


def _has_cupom(tipo_titulo: str) -> bool:
    t = (tipo_titulo or "").lower()
    return "juros semestrais" in t


def normalize_oferta(df_raw: pd.DataFrame) -> pd.DataFrame:
    required = [
        "Tipo Titulo",
        "Data Vencimento",
        "Data Base",
        "Taxa Compra Manha",
        "Taxa Venda Manha",
        "PU Compra Manha",
        "PU Venda Manha",
    ]
    missing = [c for c in required if c not in df_raw.columns]
    if missing:
        raise ValueError(f"Colunas faltando: {missing}. Colunas existentes: {df_raw.columns.tolist()}")

    df = df_raw.copy()

    df["Data Base"] = pd.to_datetime(df["Data Base"], dayfirst=True, errors="coerce")
    df["Data Vencimento"] = _parse_vencimento(df["Data Vencimento"])

    df["indexador"] = df["Tipo Titulo"].map(_infer_indexador)
    df["ano_vencimento"] = df["Data Vencimento"].dt.year

    # separar com/sem cupom
    df["cupom"] = df["Tipo Titulo"].map(_has_cupom)
    df["cupom_txt"] = df["cupom"].map(lambda x: "COM CUPOM" if x else "SEM CUPOM")

    # id do título (ex: IPCA_JS_2035, IPCA_STD_2035, SELIC_STD_2029, PRE_STD_2031)
    prefix = df["indexador"].map({"IPCA": "IPCA", "SELIC": "SELIC", "PREFIXADO": "PRE"}).fillna("OUTROS")
    suf = df["cupom"].map(lambda x: "JS" if x else "STD")
    df["id_titulo"] = prefix + "_" + suf + "_" + df["ano_vencimento"].astype("Int64").astype(str)

    # renomear colunas para padrão interno
    df = df.rename(
        columns={
            "Tipo Titulo": "tipo_titulo",
            "Taxa Compra Manha": "taxa_compra",
            "Taxa Venda Manha": "taxa_venda",
            "PU Compra Manha": "pu_compra",
            "PU Venda Manha": "pu_venda",
            "PU Base Manha": "pu_base",
            "Data Base": "data_base",
            "Data Vencimento": "data_vencimento",
        }
    )

    cols = [
        "data_base",
        "id_titulo",
        "indexador",
        "cupom_txt",
        "tipo_titulo",
        "data_vencimento",
        "taxa_compra",
        "taxa_venda",
        "pu_compra",
        "pu_venda",
        "pu_base",
    ]
    cols = [c for c in cols if c in df.columns]

    df = (
        df[cols]
        .drop_duplicates()
        .sort_values(["indexador", "cupom_txt", "data_vencimento"])
        .reset_index(drop=True)
    )

    return df
