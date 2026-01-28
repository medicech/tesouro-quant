import sys
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import re
from pathlib import Path

# --- CONFIGURAÇÃO DE CAMINHOS (CRÍTICO PARA NUVEM) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(root_dir, "src"))

try:
    from core.config import DATA_DIR
    PROCESSED_DIR = DATA_DIR / "processed"
except ImportError:
    DATA_DIR = Path(root_dir) / "data"
    PROCESSED_DIR = DATA_DIR / "processed"

# --- CONFIGURAÇÕES ---
URL_ALVO = "https://investidor10.com.br/tesouro-direto/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

# --- FUNÇÕES DE LIMPEZA ---
def clean_money(text):
    """Transforma 'R$ 1.234,56' em float 1234.56"""
    if not text: return 0.0
    clean = text.replace('R$', '').replace('.', '').replace(',', '.').strip()
    try: return float(clean)
    except: return 0.0

def clean_rate(text):
    """Transforma 'IPCA + 6,50%' em float 6.50"""
    if not text: return 0.0
    match = re.search(r'([\d,]+)%', text)
    if match:
        clean = match.group(1).replace(',', '.')
        return float(clean)
    clean = text.replace('%', '').replace(',', '.').strip()
    try: return float(clean)
    except: return 0.0

def main():
    print("🕵️‍♂️ Iniciando Scraping do Investidor10 (Produção)...")
    
    # Garante que a pasta existe
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    try:
        # 1. Requisição
        response = requests.get(URL_ALVO, headers=HEADERS, timeout=20)
        response.raise_for_status()
        
        # 2. Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tenta achar a tabela (id com erro de digitação do site ou classe genérica)
        table = soup.find('table', {'id': 'rankigns'})
        if not table:
            table = soup.find('table', {'class': 'table'})
            
        if not table:
            print("❌ Erro: Tabela não encontrada no HTML.")
            sys.exit(1) # Força erro no Streamlit

        rows = table.find('tbody').find_all('tr')
        print(f"✅ Encontradas {len(rows)} linhas.")
        
        dados_processados = []
        
        for tr in rows:
            cols = tr.find_all('td')
            if len(cols) < 6: continue
            
            # Mapeamento Investidor10:
            # 1: Nome | 2: Rentabilidade | 3: Mínimo | 4: Preço | 5: Vencimento
            nome = cols[1].get_text().strip()
            rentabilidade = cols[2].get_text().strip()
            minimo = cols[3].get_text().strip()
            preco = cols[4].get_text().strip()
            vencimento = cols[5].get_text().strip()
            
            if not nome or "Título" in nome: continue
            
            # Tratamento de Data
            try:
                dt_venc = pd.to_datetime(vencimento, dayfirst=True)
            except:
                continue

            # Classificação do Indexador (Essencial para os filtros do site)
            nome_upper = nome.upper()
            if "IPCA" in nome_upper or "RENDA+" in nome_upper or "EDUCA+" in nome_upper:
                indexador = "IPCA"
            elif "SELIC" in nome_upper:
                indexador = "SELIC"
            elif "PREFIXADO" in nome_upper:
                indexador = "PREFIXADO"
            else:
                indexador = "OUTROS"

            dados_processados.append({
                "tipo_titulo": nome,
                "vencimento": dt_venc,
                "data_base": datetime.now(),
                "taxa_compra": clean_rate(rentabilidade),
                "pu_compra": clean_money(preco),
                "minimo_compra": clean_money(minimo),
                "taxa_venda": 0.0, # Site não fornece fácil
                "pu_venda": 0.0,   # Site não fornece fácil
                "indexador": indexador,
                "ano_vencimento": dt_venc.year
            })

        if not dados_processados:
            print("❌ Erro: Nenhum dado extraído.")
            sys.exit(1)

        # 3. Limpeza e Salvamento
        # Remove arquivos antigos para o site não ler dado velho
        for f in PROCESSED_DIR.glob("tesouro_catalogo_*.parquet"):
            try: os.remove(f)
            except: pass

        df = pd.DataFrame(dados_processados)
        hoje_iso = datetime.now().date().isoformat()
        arquivo_saida = PROCESSED_DIR / f"tesouro_catalogo_{hoje_iso}.parquet"
        
        df.to_parquet(arquivo_saida, index=False)
        print(f"💾 SUCESSO! Salvo em: {arquivo_saida}")
        
        # Preview no Log do Streamlit
        print("📊 Amostra:")
        print(df[['tipo_titulo', 'taxa_compra', 'pu_compra']].head(3))

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
