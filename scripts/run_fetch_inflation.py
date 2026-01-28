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

URL_FOCUS = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais"

def main():
    print("🔮 Iniciando Atualização do FOCUS (IPCA + SELIC)...")
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    try:
        # Aumentei o top para 500 para garantir que pegue Selic e IPCA de todos os anos
        query = "?$filter=(Indicador eq 'IPCA' or Indicador eq 'Selic')&$top=500&$orderby=Data desc&$format=json"
        url = URL_FOCUS + query.replace(" ", "%20")
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
            
        data = response.json()
        valores = data.get('value', [])
        
        if not valores:
            print("❌ Erro: Lista vazia do Focus.")
            sys.exit(1)

        df = pd.DataFrame(valores)
        df['Data'] = pd.to_datetime(df['Data'])
        df['DataReferencia'] = pd.to_numeric(df['DataReferencia'], errors='coerce')
        
        # Pega a data mais recente
        ultima_divulgacao = df['Data'].max()
        
        # Filtra apenas dados dessa data (IPCA e SELIC)
        df_recente = df[df['Data'] == ultima_divulgacao].copy()
        
        print(f"✅ Focus Processado. Relatório: {ultima_divulgacao.strftime('%d/%m/%Y')}")
        unique_inds = df_recente['Indicador'].unique()
        print(f"   Indicadores encontrados: {unique_inds}")
        
        if 'Selic' not in unique_inds:
            print("⚠️ AVISO: Selic não foi encontrada no retorno da API!")

        arquivo_saida = PROCESSED_DIR / "focus_ipca.parquet"
        
        if arquivo_saida.exists():
            try: os.remove(arquivo_saida)
            except: pass
            
        df_recente.to_parquet(arquivo_saida, index=False)
        print(f"💾 SUCESSO! Salvo em: {arquivo_saida}")

    except Exception as e:
        print(f"❌ Erro Crítico Focus: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
