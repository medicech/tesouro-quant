import sys
import os
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

# --- AJUSTE DE PATH (CRÍTICO PARA O DEPLOY) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(root_dir, "src"))

try:
    from core.config import DATA_DIR
    PROCESSED_DIR = DATA_DIR / "processed"
except ImportError:
    DATA_DIR = Path(root_dir) / "data"
    PROCESSED_DIR = DATA_DIR / "processed"

# URL DA API OFICIAL DO TESOURO (A FONTE DA VERDADE)
URL_OFICIAL = "https://www.tesourodireto.com.br/json/br/com/b3/tesourodireto/service/api/treasurybondsinfo.json"

def main():
    print("🏛️ Conectando na API Oficial do Tesouro Direto...")
    
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    try:
        # Headers para fingir ser um navegador comum e evitar bloqueios
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.tesourodireto.com.br/"
        }
        
        # Timeout curto para testar rápido
        response = requests.get(URL_OFICIAL, headers=headers, timeout=20, verify=True)
        response.raise_for_status()
        
        data_json = response.json()
        
        # A estrutura do JSON oficial é: response -> TrsrBdTradgList
        lista_titulos = data_json.get("response", {}).get("TrsrBdTradgList", [])
        
        if not lista_titulos:
            print("❌ Erro: API retornou lista vazia.")
            return

        print(f"✅ Recebidos {len(lista_titulos)} títulos da fonte oficial.")
        
        dados_processados = []
        
        for item in lista_titulos:
            try:
                # Mapeamento dos campos oficiais
                nome_titulo = item.get("TrsrBd", {}).get("nm")
                vencimento_str = item.get("TrsrBd", {}).get("mtrtyDt") # Vem como "2029-05-15T00:00:00"
                taxa_compra = item.get("TrsrBd", {}).get("anulInvstmtRate", 0.0)
                pu_compra = item.get("TrsrBd", {}).get("untrInvstmtVal", 0.0)
                taxa_venda = item.get("TrsrBd", {}).get("anulRedRate", 0.0)
                pu_venda = item.get("TrsrBd", {}).get("untrRedVal", 0.0)
                
                # Tratamento de Data
                if vencimento_str:
                    dt_venc = pd.to_datetime(vencimento_str).replace(tzinfo=None)
                else:
                    continue

                # Definição do Indexador
                nome_upper = nome_titulo.upper()
                if "IPCA" in nome_upper or "RENDA+" in nome_upper or "EDUCA+" in nome_upper:
                    indexador = "IPCA"
                elif "SELIC" in nome_upper:
                    indexador = "SELIC"
                elif "PREFIXADO" in nome_upper:
                    indexador = "PREFIXADO"
                else:
                    indexador = "OUTROS"

                dados_processados.append({
                    "tipo_titulo": nome_titulo,
                    "vencimento": dt_venc,
                    "data_base": datetime.now(),
                    "taxa_compra": float(taxa_compra),
                    "pu_compra": float(pu_compra),
                    "taxa_venda": float(taxa_venda),
                    "pu_venda": float(pu_venda),
                    "indexador": indexador,
                    "ano_vencimento": dt_venc.year
                })
            except Exception as e_item:
                print(f"⚠️ Erro ao processar item: {e_item}")
                continue

        # Salva o arquivo
        df = pd.DataFrame(dados_processados)
        
        # Garante que tem dados
        if df.empty:
            print("❌ Erro: DataFrame vazio após processamento.")
            return

        hoje_iso = datetime.now().date().isoformat()
        arquivo_saida = PROCESSED_DIR / f"tesouro_catalogo_{hoje_iso}.parquet"
        
        df.to_parquet(arquivo_saida, index=False)
        print(f"💾 SUCESSO! Arquivo Oficial Salvo: {arquivo_saida}")
        
        # Preview
        print(df[['tipo_titulo', 'taxa_compra', 'pu_compra']].head(3))

    except Exception as e:
        print(f"❌ Erro Crítico na API Oficial: {e}")

if __name__ == "__main__":
    main()
