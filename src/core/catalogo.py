import pandas as pd
import os
from pathlib import Path
from core.config import DATA_DIR

def load_latest_catalog():
    """
    Busca o arquivo de catálogo mais recente na pasta processed,
    independente da data do nome do arquivo.
    Isso garante que o site funcione logo após o download.
    """
    try:
        processed = Path(DATA_DIR) / "processed"
        
        # Lista todos os arquivos que começam com 'tesouro_catalogo'
        files = list(processed.glob("tesouro_catalogo_*.parquet"))
        
        # Se não achou nada, tenta procurar sem o prefixo (caso antigo)
        if not files:
             files = list(processed.glob("*.parquet"))

        # Filtra apenas os que parecem ser catálogos válidos (evita ler selic/focus por engano)
        catalog_files = [f for f in files if "tesouro_catalogo" in f.name]

        if not catalog_files:
            print("⚠️ Aviso: Nenhum arquivo de catálogo encontrado na pasta processed.")
            return pd.DataFrame()

        # Ordena pelo nome (que contém a data YYYY-MM-DD) e pega o último (mais recente)
        latest_file = sorted(catalog_files)[-1]
        
        print(f"📖 Lendo arquivo de catálogo: {latest_file.name}")
        df = pd.read_parquet(latest_file)
        
        # Garante que as colunas de data estão como datetime
        if 'vencimento' in df.columns:
            df['vencimento'] = pd.to_datetime(df['vencimento'])
        
        return df

    except Exception as e:
        print(f"❌ Erro ao ler catálogo: {e}")
        return pd.DataFrame()
