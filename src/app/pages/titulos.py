import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys
from pathlib import Path

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Simulador - Tesouro Quant", page_icon="📊", layout="wide")

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
    .stAlert { padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE CARGA BLINDADA (LOCAL) ---
# Esta função está AQUI dentro para garantir que funcione mesmo se o 'core' falhar
def carregar_dados_blindado():
    try:
        # 1. Tenta descobrir o caminho da pasta data/processed
        # Baseado no seu debug: /mount/src/tesouro-quant/data/processed
        roots = [
            Path("data/processed"),
            Path("../data/processed"),
            Path(os.getcwd()) / "data" / "processed",
            Path("/mount/src/tesouro-quant/data/processed") # Caminho absoluto do servidor
        ]
        
        found_file = None
        for pasta in roots:
            if pasta.exists():
                files = list(pasta.glob("tesouro_catalogo_*.parquet"))
                if files:
                    found_file = sorted(files)[-1] # Pega o mais recente
                    break
        
        if found_file:
            return pd.read_parquet(found_file), str(found_file)
        
        return pd.DataFrame(), "Nenhum arquivo encontrado nas pastas padrão"
        
    except Exception as e:
        return pd.DataFrame(), f"Erro ao ler arquivo: {str(e)}"

# --- INTERFACE ---
st.title("📊 Simulador de Títulos")
st.markdown("Compare rentabilidades e calcule o preço justo.")

# --- TENTATIVA DE CARREGAMENTO ---
df, msg_debug = carregar_dados_blindado()

# --- ÁREA DE DEBUG (Caso dê erro) ---
if df.empty:
    st.error("⚠️ Nenhum dado encontrado.")
    
    with st.expander("🕵️‍♂️ Detalhes do Erro (Mostre isso para o suporte)", expanded=True):
        st.write(f"**Diretório Atual:** `{os.getcwd()}`")
        st.write(f"**Tentativa de carga:** {msg_debug}")
        st.write("---")
        st.write("**Verificação de Arquivos:**")
        # Lista o que tem na pasta data/processed para prova
        try:
            p = Path("data/processed")
            if p.exists():
                st.json([f.name for f in p.glob("*")])
            else:
                st.error("Pasta 'data/processed' não encontrada na raiz.")
        except:
            pass
    st.stop() # Para a execução aqui se não tiver dados

# --- SE CHEGOU AQUI, OS DADOS FORAM CARREGADOS! ---
# Conversão de tipos para garantir
if 'vencimento' in df.columns:
    df['vencimento'] = pd.to_datetime(df['vencimento'])

# Filtros Laterais
st.sidebar.header("Filtros")
tipos = st.sidebar.multiselect("Tipo de Título", options=df['indexador'].unique(), default=df['indexador'].unique())
df_filtrado = df[df['indexador'].isin(tipos)]

# Exibição Principal
if not df_filtrado.empty:
    st.subheader("📋 Títulos Disponíveis")
    
    # Tabela Formatada
    st.dataframe(
        df_filtrado[['tipo_titulo', 'vencimento', 'taxa_compra', 'pu_compra', 'indexador']].style.format({
            'taxa_compra': '{:.2f}%',
            'pu_compra': 'R$ {:.2f}',
            'vencimento': '{:%d/%m/%Y}'
        }),
        use_container_width=True,
        height=400
    )
    
    # Gráfico Rápido
    st.subheader("📈 Curva de Taxas")
    fig = px.scatter(
        df_filtrado, 
        x='vencimento', 
        y='taxa_compra', 
        color='indexador', 
        size='pu_compra',
        hover_data=['tipo_titulo'],
        title="Taxa x Vencimento"
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Nenhum título corresponde aos filtros selecionados.")
