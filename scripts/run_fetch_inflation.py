import sys
import os
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DE CAMINHOS ---
# Garante que sabemos onde salvar (data/processed)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

try:
    from core.config import DATA_DIR
    PROCESSED_DIR = DATA_DIR / "processed"
except ImportError:
    from pathlib import Path
    DATA_DIR = Path(root_dir) / "data"
    PROCESSED_DIR = DATA_DIR / "processed"

# URL da API do Banco Central (Olinda)
URL_BASE = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais"

def main():
    print("🎈 Iniciando atualização: Boletim Focus (Inflação)...")
    
    # TRUQUE: Query String manual para garantir %20 em vez de + (Evita Erro 400)
    query = "?$filter=Indicador%20eq%20'IPCA'&$top=100&$orderby=Data%20desc&$format=json"
    url_completa = URL_BASE + query
    
    try:
        # Timeout de 15s para garantir
        response = requests.get(url_completa, timeout=15)
        response.raise_for_status() # Para se der erro 400/500
        
        data = response.json()
        valores = data.get('value', [])
        
        if not valores:
            print("❌ Erro: Dados vazios do BC.")
            return

        # Cria DataFrame
        df = pd.DataFrame(valores)
        
        # --- LIMPEZA CRÍTICA ---
        df['Data'] = pd.to_datetime(df['Data'])
        # Garante que o ano seja número (ex: 2026) e não texto
        df['DataReferencia'] = pd.to_numeric(df['DataReferencia'], errors='coerce')
        
        # Filtra apenas a expectativa MAIS RECENTE divulgada pelo BC
        ultima_data_divulgacao = df['Data'].max()
        df_recente = df[df['Data'] == ultima_data_divulgacao].copy()
        
        print(f"📅 Boletim Focus de: {ultima_data_divulgacao.strftime('%d/%m/%Y')}")
        
        # --- SALVAMENTO ---
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        arquivo_saida = PROCESSED_DIR / "focus_ipca.parquet"
        
        df_recente.to_parquet(arquivo_saida, index=False)
        
        print(f"✅ Sucesso! Expectativas salvas em: {arquivo_saida}")
        
        # Preview rápido no terminal
        ano_atual = datetime.now().year
        meta = df_recente[df_recente['DataReferencia'] == ano_atual]['Mediana'].iloc[0]
        print(f"📊 Preview: IPCA {ano_atual} = {meta}%")

    except Exception as e:
        print(f"❌ Erro ao buscar Focus: {e}")

if __name__ == "__main__":
    main()