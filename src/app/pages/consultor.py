import pandas as pd
import os
from pathlib import Path
import streamlit as st

# --- FUNÇÃO DE CARREGAMENTO BLINDADA ---
# O cache impede que o Streamlit recarregue isso toda hora, 
# mas se der erro, limpe o cache com "Clear Cache" no menu.
@st.cache_data(ttl=300) # Atualiza a cada 5 min
def load_latest_catalog():
    """
    Busca o arquivo de catálogo mais recente na pasta data/processed.
    Usa o caminho relativo à raiz da execução do Streamlit.
    """
    try:
        # Pega o diretório onde o comando 'streamlit run' foi executado
        # O debug mostrou que é: /mount/src/tesouro-quant
        root_dir = Path(os.getcwd())
        
        # Monta o caminho exato onde o debug achou os arquivos
        processed_dir = root_dir / "data" / "processed"

        # Se não achar, tenta subir um nível (caso esteja rodando de dentro de src)
        if not processed_dir.exists():
            processed_dir = root_dir.parent / "data" / "processed"

        print(f"📍 [CATALOGO] Buscando em: {processed_dir}")
        
        if not processed_dir.exists():
            print("❌ Pasta não encontrada.")
            return pd.DataFrame()

        # Busca arquivos parquet de catálogo
        files = list(processed_dir.glob("tesouro_catalogo_*.parquet"))
        
        if not files:
            print("⚠️ Pasta existe, mas sem arquivos de catálogo.")
            return pd.DataFrame()

        # Ordena para pegar o último (mais recente: 2026-01-27 ganha de 26)
        latest_file = sorted(files)[-1]
        
        print(f"📖 Lendo arquivo: {latest_file.name}")
        df = pd.read_parquet(latest_file)
        
        # Garante conversão de datas
        if 'vencimento' in df.columns:
            df['vencimento'] = pd.to_datetime(df['vencimento'])
            
        return df

    except Exception as e:
        print(f"❌ Erro crítico ao ler catálogo: {e}")
        return pd.DataFrame()
