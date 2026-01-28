import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime

# --- CONFIGURAÇÃO DE CAMINHOS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
possible_roots = [Path(root_dir), Path(os.getcwd()), Path("/mount/src/tesouro-quant")]

st.set_page_config(page_title="Macro Intelligence", page_icon="🌐", layout="wide")
st.markdown("<style>.stApp { background-color: #F0F2F6; }</style>", unsafe_allow_html=True)

# --- FUNÇÃO DE CARGA ---
def carregar_arquivo(nome_arquivo):
    for root in possible_roots:
        path = root / "data" / "processed" / nome_arquivo
        if path.exists(): return pd.read_parquet(path), path
        path_local = Path("data/processed") / nome_arquivo
        if path_local.exists(): return pd.read_parquet(path_local), path_local
    return pd.DataFrame(), None

# --- CARGA DADOS ---
df_focus, _ = carregar_arquivo("focus_ipca.parquet")
df_titulos, _ = carregar_arquivo("tesouro_catalogo_2026-01-28.parquet")
if df_titulos.empty:
    # Fallback para qualquer catalogo
    try:
        p = Path("data/processed")
        files = sorted(list(p.glob("tesouro_catalogo_*.parquet")))
        if files: df_titulos = pd.read_parquet(files[-1])
    except: pass

# --- PREPARAÇÃO DOS DADOS ---
if not df_titulos.empty:
    if 'vencimento' in df_titulos.columns: df_titulos['vencimento'] = pd.to_datetime(df_titulos['vencimento'])
    if 'data_base' in df_titulos.columns: df_titulos['data_base'] = pd.to_datetime(df_titulos['data_base'])
    else: df_titulos['data_base'] = pd.Timestamp.now()
    
    # Cria coluna prazo
    df_titulos['prazo_anos'] = (df_titulos['vencimento'] - df_titulos['data_base']).dt.days / 365.25
    
    # Cria rótulo amigável para o filtro
    df_titulos['label_filtro'] = df_titulos['tipo_titulo'] + " (" + df_titulos['vencimento'].dt.year.astype(str) + ")"

# --- HEADER ---
c1, c2 = st.columns([1, 5])
with c1:
    if st.button("⬅ Voltar"): st.switch_page("streamlit_app.py")
with c2:
    st.title("Macro Intelligence")
    st.caption("Análise Estrutural da Curva de Juros e Expectativas.")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📉 Curva de Juros (ETTJ)", "🎈 Breakeven de Inflação", "🔮 Boletim Focus"])

# --- TAB 1: CURVA DE JUROS COM FILTROS ---
with tab1:
    if not df_titulos.empty:
        # --- ÁREA DE FILTROS ---
        with st.expander("⚙️ Configurações do Gráfico (Filtros)", expanded=True):
            col_f1, col_f2 = st.columns(2)
            
            # 1. Filtro de Indexador
            all_indexes = df_titulos['indexador'].unique()
            sel_indexes = col_f1.multiselect("Indexadores", all_indexes, default=['PREFIXADO', 'IPCA'])
            
            # 2. Filtro de Títulos Específicos
            # Filtra primeiro pelo indexador escolhido
            df_step1 = df_titulos[df_titulos['indexador'].isin(sel_indexes)]
            all_titles = df_step1['tipo_titulo'].unique()
            
            # Sugere padrão: Remove Renda+ e Educa+ para não poluir, deixa só os principais
            default_titles = [t for t in all_titles if "Renda+" not in t and "Educa+" not in t]
            
            sel_titles = col_f2.multiselect("Selecionar Títulos", all_titles, default=default_titles)
        
        # --- GRÁFICO ---
        # Aplica filtros finais
        df_chart = df_step1[df_step1['tipo_titulo'].isin(sel_titles)].copy()
        
        if not df_chart.empty:
            fig = px.line(
                df_chart.sort_values('prazo_anos'), 
                x="vencimento", 
                y="taxa_compra", 
                color="indexador",
                text="taxa_compra", # Mostra o valor no ponto
                markers=True,
                title="Curva de Juros (ETTJ)",
                color_discrete_map={"PREFIXADO": "#D32F2F", "IPCA": "#1976D2", "SELIC": "#388E3C"}
            )
            fig.update_traces(textposition="top center", texttemplate='%{text:.2f}%')
            fig.update_layout(height=550, hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhum título selecionado.")
            
    else:
        st.error("Sem dados de títulos.")

# --- TAB 2: BREAKEVEN ---
with tab2:
    st.markdown("### Inflação Implícita")
    st.info("💡 Diferença de taxa entre Prefixados e IPCA+ de mesmo vencimento.")
    
    if not df_titulos.empty:
        # Lógica simplificada
        df_pre = df_titulos[df_titulos['indexador'] == 'PREFIXADO'][['ano_vencimento', 'taxa_compra']].groupby('ano_vencimento').mean()
        df_ipca = df_titulos[df_titulos['indexador'] == 'IPCA'][['ano_vencimento', 'taxa_compra']].groupby('ano_vencimento').mean()
        
        df_break = df_pre.join(df_ipca, lsuffix='_pre', rsuffix='_ipca', how='inner')
        df_break['breakeven'] = (((1 + df_break['taxa_compra_pre']/100) / (1 + df_break['taxa_compra_ipca']/100)) - 1) * 100
        
        fig_break = px.bar(
            df_break.reset_index(),
            x='ano_vencimento', y='breakeven',
            text_auto='.2f', title="Inflação Implícita (%)",
            color_discrete_sequence=['#FFA000']
        )
        st.plotly_chart(fig_break, use_container_width=True)

# --- TAB 3: FOCUS (AGORA COM SELIC) ---
with tab3:
    st.markdown("### Expectativas de Mercado (Banco Central)")
    
    if not df_focus.empty:
        data_rel = pd.to_datetime(df_focus['Data'].max()).strftime('%d/%m/%Y')
        st.success(f"📅 Relatório Vigente: **{data_rel}**")
        
        try:
            # Filtra indicadores (Agora Selic vai aparecer se o robô trouxe)
            df_view = df_focus[df_focus['Indicador'].isin(['IPCA', 'Selic'])].copy()
            df_view = df_view[df_view['DataReferencia'].isin([2026, 2027, 2028, 2029])]
            
            pivoted = df_view.pivot_table(index='Indicador', columns='DataReferencia', values='Mediana', aggfunc='first')
            
            st.dataframe(
                pivoted.style.format("{:.2f}%").background_gradient(cmap="Blues", axis=1), 
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Erro na tabela: {e}")
    else:
        st.warning("Dados do Focus não encontrados.")
