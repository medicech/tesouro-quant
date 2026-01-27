import pandas as pd
import os
from pathlib import Path

# --- NAVEGAÇÃO RELATIVA (GPS BLINDADO) ---
# Descobre onde este arquivo (catalogo.py) está: src/core/
current_file_path = Path(__file__).resolve()
src_core_dir = current_file_path.parent
src_dir = src_core_dir.parent
root_dir = src_dir.parent

# Monta o caminho da pasta de dados: root/data/processed
PROCESSED_DIR = root_dir / "data" / "processed"

def load_latest_catalog():
    """
    Busca o arquivo de catálogo mais recente na pasta processed.
    BLINDADO: Usa caminhos absolutos baseados no arquivo atual.
    """
    print(f"📍 [DEBUG] Procurando dados em: {PROCESSED_DIR}")
    
    if not PROCESSED_DIR.exists():
        print("❌ [DEBUG] Erro Crítico: A pasta data/processed não existe no caminho esperado.")
        return pd.DataFrame()

    try:
        # Pega qualquer arquivo que comece com 'tesouro_catalogo' e termine com .parquet
        files = list(PROCESSED_DIR.glob("tesouro_catalogo_*.parquet"))
        
        if not files:
            print("⚠️ [DEBUG] Pasta encontrada, mas nenhum arquivo 'tesouro_catalogo' dentro dela.")
            # Debug: Lista o que tem lá para entender
            print(f"   Conteúdo da pasta: {[f.name for f in PROCESSED_DIR.glob('*')]}")
            return pd.DataFrame()

        # Ordena para pegar o último (mais recente)
        # Ex: dia 27 ganha do dia 26
        latest_file = sorted(files)[-1]
        
        print(f"📖 [DEBUG] Abrindo arquivo: {latest_file.name}")
        df = pd.read_parquet(latest_file)
        
        if df.empty:
            print("⚠️ [DEBUG] O arquivo abriu, mas o DataFrame está vazio!")
        else:
            print(f"✅ [DEBUG] Sucesso! Carregados {len(df)} títulos.")

        return df

    except Exception as e:
        print(f"❌ [DEBUG] Erro ao ler catálogo: {e}")
        return pd.DataFrame()

# Teste rápido se rodar o arquivo direto
if __name__ == "__main__":
    df = load_latest_catalog()
    print(df.head())
