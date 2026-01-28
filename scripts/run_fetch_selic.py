import sys
import os
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

# --- CONFIGURAÇÃO DE PATH ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(root_dir, "src"))

try:
    from core.config import DATA_DIR
    PROCESSED_DIR = DATA_DIR / "processed"
except ImportError:
    DATA_DIR = Path(root_dir) / "data"
    PROCESSED_DIR = DATA_DIR / "processed"

# API DO BANCO CENTRAL (SGS - Série 11 - Selic Over)
URL_SELIC = "http://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/20?formato=json"

def main():
    print("🏦 Iniciando Atualização da SELIC...")
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    try:
        # 1. Baixar Dados
        response = requests.get(URL_SELIC, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Erro na API do BC: {response.status_code}")
            sys.exit(1) # FORÇA ERRO
            
        data = response.json()
        
        if not data:
            print("❌ Erro: API retornou lista vazia.")
            sys.exit(1)

        # 2. Processar
        df = pd.DataFrame(data)
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
        df['valor'] = pd.to_numeric(df['valor'])
        
        # Pega a última data disponível
        ultima_data = df['data'].max()
        ultimo_valor = df.loc[df['data'] == ultima_data, 'valor'].iloc[0]
        
        print(f"✅ Dados recebidos. Última Selic: {ultimo_valor}% ({ultima_data.strftime('%d/%m/%Y')})")
        
        # 3. Salvar (Sempre sobrescreve o arquivo meta)
        arquivo_saida = PROCESSED_DIR / "selic_meta_sgs.parquet"
        
        # Remove anterior se existir para garantir
        if arquivo_saida.exists():
            try: os.remove(arquivo_saida)
            except: pass
            
        df.to_parquet(arquivo_saida, index=False)
        print(f"💾 SUCESSO! Salvo em: {arquivo_saida}")

    except Exception as e:
        print(f"❌ Erro Crítico Selic: {e}")
        sys.exit(1) # FORÇA ERRO

if __name__ == "__main__":
    main()
