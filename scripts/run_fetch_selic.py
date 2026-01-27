from __future__ import annotations

from pathlib import Path
import pandas as pd

from core.config import DATA_DIR
from core.datasources.bcb_sgs import fetch_selic_meta, latest_value, save_selic_meta


def main():
    processed = Path(DATA_DIR) / "processed"

    # pega últimos 5 anos (bom pro baseline e pro app)
    hoje = pd.Timestamp.today()
    start = (hoje - pd.Timedelta(days=5 * 365)).strftime("%d/%m/%Y")

    print("Baixando Selic Meta (SGS 432)...")
    df = fetch_selic_meta(start=start)

    d, v = latest_value(df)
    print(f"Último ponto: {d.date()} | Selic Meta: {v:.2f}%")

    out = save_selic_meta(df, processed)
    print("Arquivo salvo:", out)

    print(df.tail(5))


if __name__ == "__main__":
    main()
