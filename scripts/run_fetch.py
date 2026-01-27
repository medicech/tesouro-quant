import sys
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup # Biblioteca de Raspagem (Scraping)
from datetime import datetime
import re

# --- CONFIGURAÇÃO DE CAMINHOS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

try:
    from core.config import PROCESSED_DIR
except ImportError:
    from pathlib import Path
    DATA_DIR = Path(root_dir) / "data"
    PROCESSED_DIR = DATA_DIR / "processed"

def clean_text(text):
    """Limpa espaços extras e quebras de linha"""
    if not text: return ""
    return text.strip().replace('\n', '').replace('\t', '')

def parse_brl(text):
    """Converte 'R$ 1.234,56' para float 1234.56"""
    if not text: return 0.0
    clean = clean_text(text).replace('R$', '').replace('.', '').replace(',', '.')
    try:
        return float(clean)
    except:
        return 0.0

def parse_taxa(text):
    """Converte 'IPCA + 6,50%' para float 6.50"""
    if not text: return 0.0
    # Pega apenas a parte numérica percentual
    # Ex: "IPCA + 6,45%" -> pega "6,45"
    match = re.search(r'([\d,]+)%', text)
    if match:
        clean = match.group(1).replace(',', '.')
        return float(clean)
    
    # Se for só taxa (ex: "12,50%")
    clean = text.replace('%', '').replace(',', '.')
    try:
        return float(clean)
    except:
        return 0.0

def formatar_titulo_oficial(nome_site, vencimento):
    """
    Padroniza o nome do site Investidor10 para o nome Oficial do Tesouro.
    Lógica baseada no arquivo JS do GitHub.
    """
    nome_site = clean_text(nome_site)
    ano = vencimento.split('/')[-1] # Pega o ano (2029, 2035...)
    
    # Regras de normalização
    if "Selic" in nome_site:
        return f"Tesouro Selic {ano}"
    
    if "Prefixado" in nome_site:
        if "Juros Semestrais" in nome_site:
            return f"Tesouro Prefixado com Juros Semestrais {ano}"
        return f"Tesouro Prefixado {ano}"
        
    if "IPCA" in nome_site:
        if "Juros Semestrais" in nome_site:
            return f"Tesouro IPCA+ com Juros Semestrais {ano}"
        return f"Tesouro IPCA+ {ano}"
        
    if "Renda+" in nome_site:
        return f"Tesouro Renda+ Aposentadoria Extra {ano}"
        
    if "Educa+" in nome_site:
        return f"Tesouro Educa+ {ano}"

    # Fallback
    return f"{nome_site} {ano}"

def main():
    print("🕵️‍♂️ Iniciando Scraping do Investidor10 (Estratégia Alternativa)...")
    
    url = "https://investidor10.com.br/tesouro-direto/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # Para se der erro 404/500
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # O site usa uma tabela com id="rankigns" (sim, tem um erro de digitação no site deles, igual no JS)
        table = soup.find('table', {'id': 'rankigns'})
        
        if not table:
            # Tenta pegar pela classe se o ID mudar
            table = soup.find('table', {'class': 'table'})
            
        if not table:
            print("❌ Erro: Não encontrei a tabela de taxas no site.")
            return

        rows = table.find('tbody').find_all('tr')
        print(f"✅ Encontradas {len(rows)} ofertas.")
        
        dados_processados = []
        
        for tr in rows:
            cols = tr.find_all('td')
            if len(cols) < 6: continue
            
            # Mapeamento das colunas do site Investidor10:
            # 0: ? (icone)
            # 1: Nome do Título (ex: Tesouro IPCA+ 2029)
            # 2: Rentabilidade (ex: IPCA + 6,40%)
            # 3: Investimento Mínimo
            # 4: Preço Unitário
            # 5: Vencimento
            
            nome_bruto = cols[1].get_text()
            rentabilidade_txt = cols[2].get_text()
            preco_txt = cols[4].get_text()
            vencimento_txt = clean_text(cols[5].get_text())
            
            # Tratamento de Dados
            nome_oficial = formatar_titulo_oficial(nome_bruto, vencimento_txt)
            taxa_compra = parse_taxa(rentabilidade_txt)
            pu_compra = parse_brl(preco_txt)
            
            try:
                dt_venc = pd.to_datetime(vencimento_txt, dayfirst=True)
            except:
                continue

            # Define Indexador
            if "IPCA" in nome_oficial: indexador = "IPCA"
            elif "Selic" in nome_oficial: indexador = "SELIC"
            elif "Prefixado" in nome_oficial: indexador = "PREFIXADO"
            else: indexador = "OUTROS"
            
            dados_processados.append({
                "tipo_titulo": nome_oficial,
                "vencimento": dt_venc,
                "data_base": datetime.now(),
                "taxa_compra": taxa_compra,
                "pu_compra": pu_compra,
                "taxa_venda": 0.0, # Site não fornece taxa de venda fácil
                "pu_venda": 0.0,
                "indexador": indexador,
                "ano_vencimento": dt_venc.year
            })

        # Cria DataFrame e Salva
        df = pd.DataFrame(dados_processados)
        
        # Salva o arquivo
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        hoje_iso = datetime.now().date().isoformat()
        arquivo_saida = PROCESSED_DIR / f"tesouro_catalogo_{hoje_iso}.parquet"
        
        df.to_parquet(arquivo_saida, index=False)
        print(f"💾 Catalogo Atualizado Salvo: {arquivo_saida}")
        print("\n--- AMOSTRA (INVESTIDOR 10) ---")
        print(df[['tipo_titulo', 'vencimento', 'taxa_compra']].head())

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")

if __name__ == "__main__":
    main()