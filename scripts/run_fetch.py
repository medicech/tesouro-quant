import sys
import os
import requests
import pandas as pd
import time
import json
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

# URL OFICIAL (CACHE BUSTING)
URL_OFICIAL = "https://www.tesourodireto.com.br/json/br/com/b3/tesourodireto/service/api/treasurybondsinfo.json"

def main():
    print("🚀 Iniciando Download do Tesouro Direto...")
    
    # Garante que a pasta existe
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # 1. TENTA BAIXAR COM HEADERS DE NAVEGADOR REAL
    try:
        # Cache Buster: Adiciona timestamp para não pegar arquivo velho
        timestamp = int(time.time())
        url = f"{URL_OFICIAL}?_={timestamp}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.tesourodireto.com.br/titulos/precos-e-taxas.htm",
            "Origin": "https://www.tesourodireto.com.br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        print(f"📡 Conectando em: {url}")
        response = requests.get(url, headers=headers, timeout=25, verify=True)
        
        if response.status_code != 200:
            print(f"❌ Erro HTTP {response.status_code}: {response.text[:200]}")
            sys.exit(1) # FORÇA O ERRO NO STREAMLIT

        data_json = response.json()
        lista_titulos = data_json.get("response", {}).get("TrsrBdTradgList", [])
        
        if not lista_titulos:
            print("❌ Erro: API retornou lista vazia (Provável Bloqueio ou Feriado).")
            # Dump para debug se precisar
            print(f"Conteúdo recebido: {str(data_json)[:500]}")
            sys.exit(1) # FORÇA O ERRO

        print(f"✅ Recebidos {len(lista_titulos)} títulos.")

        # 2. PROCESSAMENTO
        dados_processados = []
        for item in lista_titulos:
            try:
                trsr = item.get("TrsrBd", {})
                dados_processados.append({
                    "tipo_titulo": trsr.get("nm"),
                    "vencimento": pd.to_datetime(trsr.get("mtrtyDt")).replace(tzinfo=None),
                    "data_base": datetime.now(), # CARIMBO DE AGORA
                    "taxa_compra": float(trsr.get("anulInvstmtRate", 0.0)),
                    "pu_compra": float(trsr.get("untrInvstmtVal", 0.0)),
                    "taxa_venda": float(trsr.get("anulRedRate", 0.0)),
                    "pu_venda": float(trsr.get("untrRedVal", 0.0)),
                    "minimo_compra": float(trsr.get("minInvstmtAmt", 30.0)),
                    "indexador": "IPCA" if "IPCA" in trsr.get("nm", "").upper() else ("SELIC" if "SELIC" in trsr.get("nm", "").upper() else "PREFIXADO"),
                    "ano_vencimento": pd.to_datetime(trsr.get("mtrtyDt")).year
                })
            except: continue

        if not dados_processados:
            print("❌ Erro: Falha ao processar dados.")
            sys.exit(1)

        df = pd.DataFrame(dados_processados)

        # 3. SALVAMENTO (COM REMOÇÃO DE ANTIGOS PARA FORÇAR ATUALIZAÇÃO)
        # Remove arquivos antigos do dia para garantir que só tenha o novo
        for f in PROCESSED_DIR.glob("tesouro_catalogo_*.parquet"):
            try: os.remove(f)
            except: pass
        
        hoje_iso = datetime.now().date().isoformat()
        arquivo_saida = PROCESSED_DIR / f"tesouro_catalogo_{hoje_iso}.parquet"
        df.to_parquet(arquivo_saida, index=False)
        
        print(f"💾 ARQUIVO SALVO: {arquivo_saida}")
        
        # PROVA REAL NO LOG
        ipca_29 = df[df['tipo_titulo'].str.contains('IPCA+ 2029')]
        if not ipca_29.empty:
            print(f"🔍 PROVA: IPCA+ 2029 está pagando {ipca_29.iloc[0]['taxa_compra']}%")

    except Exception as e:
        print(f"❌ Erro Crítico: {str(e)}")
        sys.exit(1) # FORÇA O ERRO

if __name__ == "__main__":
    main()
