from __future__ import annotations

import sys
import os
from pathlib import Path
import pandas as pd

# --- AJUSTE DE PATH (CRÍTICO PARA O DEPLOY) ---
# Adiciona a pasta 'src' ao caminho do Python para ele achar o 'core'
current_dir = os.path.dirname(os.path.abspath(__file__)) # Pasta scripts/
root_dir = os.path.dirname(current_dir)                # Pasta raiz do projeto
sys.path.append(os.path.join(root_dir, "src"))         # Adiciona src/ ao path

# Agora as importações vão funcionar
try:
    from core.config import DATA_DIR
    from core.datasources.bcb_sgs import fetch_selic_meta, latest_value, save_selic_meta
except ImportError as e:
    print(f"❌ Erro Crítico de Importação: {e}")
    sys.exit(1)

def main():
    # Garante que a pasta processed existe (importante na primeira execução na nuvem)
    processed = Path(DATA_DIR) / "processed"
    os.makedirs(processed, exist_ok=True)

    # pega últimos 5 anos (bom pro baseline e pro app)
    hoje = pd.Timestamp.today()
    start = (hoje - pd.Timedelta(days=5 * 365)).strftime("%d/%m/%Y")

    print("Baixando Selic Meta (SGS 432)...")
    try:
        df = fetch_selic_meta(start=start)
        
        if df is None or df.empty:
            print("⚠️ Aviso: Nenhum dado retornado do BC.")
            return

        d, v = latest_value(df)
        print(f"Último ponto: {d.date()} | Selic Meta: {v:.2f}%")

        out = save_selic_meta(df, processed)
        print("Arquivo salvo:", out)

        print(df.tail(5))
        
    except Exception as e:
        print(f"❌ Erro ao baixar Selic: {e}")
        # Não damos exit(1) aqui para não travar o deploy inteiro se só a Selic falhar

if __name__ == "__main__":
    main()
