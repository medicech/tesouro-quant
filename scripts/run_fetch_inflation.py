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

# API OLINDA (Expectativas de Mercado)
URL_FOCUS = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais"

def main():
    print("🔮 Iniciando Atualização do FOCUS (Inflação)...")
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    try:
        # Query otimizada para pegar os últimos dados de IPCA
        # Top 100 garante que pegamos o último relatório mesmo se tiver sujeira
        query = "?$filter=Indicador eq 'IPCA'&$top=100&$orderby=Data desc&$format=json"
        url = URL_FOCUS + query.replace(" ", "%20") # Garante URL encoded
        
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Erro na API Olinda: {response.status_code}")
            sys.exit(1)
            
        data = response.json()
        valores = data.get('value', [])
        
        if not valores:
            print("❌ Erro: Lista vazia do Focus.")
            sys.exit(1)

        # 2. Processar
        df = pd.DataFrame(valores)
        df['Data'] = pd.to_datetime(df['Data'])
        df['DataReferencia'] = pd.to_numeric(df['DataReferencia'], errors='coerce')
        
        # Pega a data de divulgação mais recente (O "Hoje" do relatório)
        ultima_divulgacao = df['Data'].max()
        
        # Filtra apenas as previsões desse último relatório
        df_recente = df[df['Data'] == ultima_divulgacao].copy()
        
        print(f"✅ Focus Processado. Data do Relatório: {ultima_divulgacao.strftime('%d/%m/%Y')}")
        
        # Preview
        try:
            # Tenta mostrar a meta para 2026
            meta_26 = df_recente[df_recente['DataReferencia'] == 2026]['Mediana'].iloc[0]
            print(f"   Previsão IPCA 2026: {meta_26}%")
        except: pass

        # 3. Salvar
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
