from __future__ import annotations
import numpy as np
import pandas as pd


def build_vertices(df: pd.DataFrame, modo: str = "Compra") -> pd.DataFrame:
    """
    Extrai vértices (prazo_anos x taxa) do catálogo para um recorte já filtrado.
    Retorna DataFrame com colunas: prazo_anos, taxa
    """
    taxa_col = "taxa_compra" if modo == "Compra" else "taxa_venda"

    out = df[["prazo_anos", taxa_col]].copy()
    out = out.rename(columns={taxa_col: "taxa"})
    out["prazo_anos"] = pd.to_numeric(out["prazo_anos"], errors="coerce")
    out["taxa"] = pd.to_numeric(out["taxa"], errors="coerce")
    out = out.dropna(subset=["prazo_anos", "taxa"])
    out = out.sort_values("prazo_anos")

    # se houver prazos repetidos, tira média (mais estável)
    out = out.groupby("prazo_anos", as_index=False)["taxa"].mean()

    return out


def interpolate_curve(vertices: pd.DataFrame, grid: np.ndarray) -> pd.DataFrame:
    """
    Interpola linearmente taxa(prazo) nos pontos de grid.
    - Para fora do intervalo dos vértices, fazemos extrapolação constante (flat).
      (defensável e simples para baseline)
    """
    if vertices.empty:
        return pd.DataFrame({"prazo_anos": grid, "taxa_interp": np.nan})

    x = vertices["prazo_anos"].to_numpy()
    y = vertices["taxa"].to_numpy()

    # numpy.interp faz linear e extrapola usando os extremos (flat)
    y_i = np.interp(grid, x, y)

    return pd.DataFrame({"prazo_anos": grid, "taxa_interp": y_i})


def build_ettj(df: pd.DataFrame, modo: str = "Compra", max_years: float = 40.0, step: float = 0.25) -> dict:
    """
    Constrói ETTJ:
    - vertices: DataFrame com prazos e taxas observadas
    - curve: DataFrame com prazos (grid) e taxa interpolada
    """
    vertices = build_vertices(df, modo=modo)
    grid = np.arange(0.0, max_years + 1e-9, step)
    grid = grid[grid > 0]  # remove 0

    curve = interpolate_curve(vertices, grid)

    return {"vertices": vertices, "curve": curve}
