import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# --- CONFIGURAÇÃO DE CAMINHOS (BLINDAGEM) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) # Volta até a raiz

# Tenta caminhos diferentes para garantir
possible_roots = [
    Path(root_dir),
    Path(os.getcwd()),
    Path("/mount/src/tesouro-quant")
]

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Macro Intelligence", page_icon="🌐", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F0F2F6; }
    .metric-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; }
    .big-num { font-size: 24px; font-weight: bold; color: #002B49; }
    .sub-text { font-size: 12px; color: #666; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE CARGA BLINDADA ---
def carregar_arquivo(nome_arquivo):
    """Busca o arquivo em todas as pastas possíveis"""
    for root in possible_roots:
        path = root / "data" / "processed" / nome_arquivo
        if path.exists():
            return pd.read_parquet(path), path
        
        # Tenta data/processed direto (local)
        path_local = Path("data/processed") / nome_arquivo
        if path_local.exists():
            return pd.read_parquet(path_local), path_local
            
    return pd.DataFrame(), None

# --- CARGA DE DADOS ---
# 1. Carrega Focus (Inflação)
df_focus, path_focus = carregar_arquivo("focus_ipca.parquet")

# 2. Carrega Curva de Juros (Do Catálogo Geral)
# Precisamos do catálogo para desenhar a curva
df_titulos, path_titulos = carregar_arquivo("tesouro_catalogo_2026-01-28.parquet") # Tenta data específica
if df_titulos.empty:
    # Se não achar com data fixa, tenta achar qualquer um
    # Logica de busca do mais recente
    try:
        for root in possible_roots:
            p = root / "data" / "processed"
            if p.exists():
                files = sorted(list(p.glob("tesouro_catalogo_*.parquet")))
                if files:
                    df_titulos = pd.read_parquet(files[-1])
                    break
    except: pass

# --- HEADER ---
c1, c2 = st.columns([1, 5])
with c1:
    if st.button("⬅ Voltar"): st.switch_page("streamlit_app.py")
with c2:
    st.title("Macro Intelligence")
    st.caption("Análise técnica da Estrutura a Termo (ETTJ), Inflação Implícita e Boletim Focus.")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📉 Curva de Juros (ETTJ)", "🎈 Breakeven de Inflação", "🔮 Boletim Focus"])

# --- TAB 1: CURVA DE JUROS ---
with tab1:
    if not df_titulos.empty:
        # Filtra Pre e IPCA
        df_curve = df_titulos[df_titulos['indexador'].isin(['PREFIXADO', 'IPCA'])].copy()
        
        if not df_curve.empty:
            fig = px.line(
                df_curve.sort_values('prazo_anos'), 
                x="vencimento", 
                y="taxa_compra", 
                color="indexador",
                markers=True,
                title="Estrutura a Termo da Taxa de Juros (ETTJ)",
                labels={"taxa_compra": "Taxa (% a.a.)", "vencimento": "Vencimento"},
                color_discrete_map={"PREFIXADO": "#D32F2F", "IPCA": "#1976D2"}
            )
            fig.update_layout(hovermode="x unified", height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Data base da curva
            data_base_str = pd.to_datetime(df_curve['data_base'].max()).strftime('%d/%m/%Y')
            st.info(f"📅 Data base da Curva: **{data_base_str}**")
        else:
            st.warning("Dados insuficientes para gerar a curva.")
    else:
        st.error("Não foi possível carregar os dados dos títulos.")

# --- TAB 2: BREAKEVEN ---
with tab2:
    st.markdown("### Inflação Implícita (Breakeven)")
    st.write("Quanto o mercado precifica de inflação futura ao comparar títulos Prefixados vs IPCA+.")
    
    if not df_titulos.empty:
        # Lógica simplificada de Breakeven (Matching por ano aproximado)
        df_pre = df_titulos[df_titulos['indexador'] == 'PREFIXADO'][['ano_vencimento', 'taxa_compra']].set_index('ano_vencimento')
        df_ipca = df_titulos[df_titulos['indexador'] == 'IPCA'][['ano_vencimento', 'taxa_compra']].set_index('ano_vencimento')
        
        # Cruzamento (Inner Join nos anos que tem os dois)
        df_break = df_pre.join(df_ipca, lsuffix='_pre', rsuffix='_ipca', how='inner')
        
        # Fórmula de Fisher: (1 + Pre) = (1 + Real) * (1 + Implicita)
        # Implicita = ((1 + Pre) / (1 + Real)) - 1
        df_break['breakeven'] = (((1 + df_break['taxa_compra_pre']/100) / (1 + df_break['taxa_compra_ipca']/100)) - 1) * 100
        
        fig_break = px.bar(
            df_break.reset_index(),
            x='ano_vencimento',
            y='breakeven',
            text_auto='.2f',
            title="Inflação Implícita por Vencimento",
            color_discrete_sequence=['#FFA000']
        )
        fig_break.update_traces(textposition='outside')
        fig_break.update_yaxes(title="Inflação Implícita (%)")
        st.plotly_chart(fig_break, use_container_width=True)
    else:
        st.warning("Sem dados para calcular Breakeven.")

# --- TAB 3: FOCUS (O PROBLEMA) ---
with tab3:
    st.markdown("### Expectativas de Mercado (Banco Central)")
    
    if not df_focus.empty:
        # Pega a data mais recente do arquivo carregado
        data_relatorio = pd.to_datetime(df_focus['Data'].max())
        data_fmt = data_relatorio.strftime('%d/%m/%Y')
        
        st.markdown(f"""
        <div style="background-color: white; padding: 15px; border-radius: 8px; border-left: 5px solid #002B49; margin-bottom: 20px;">
            <span style="font-size: 12px; font-weight: bold; color: #666; text-transform: uppercase;">Data do Relatório</span><br>
            <span style="font-size: 28px; font-weight: 800; color: #002B49;">{data_fmt}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Pivot table para exibição
        # Colunas: DataReferencia (2026, 2027...) | Linhas: Indicador (IPCA, Selic)
        try:
            # Filtra apenas o que interessa
            df_view = df_focus[df_focus['Indicador'].isin(['IPCA', 'Selic', 'PIB Total', 'Câmbio'])].copy()
            df_view = df_view[df_view['DataReferencia'].isin([2026, 2027, 2028])] # Próximos anos
            
            pivoted = df_view.pivot_table(index='Indicador', columns='DataReferencia', values='Mediana', aggfunc='first')
            st.dataframe(pivoted.style.format("{:.2f}"), use_container_width=True)
            
            st.caption("Fonte: API Olinda/Bacen. Mediana das expectativas de mercado.")
            
        except Exception as e:
            st.error(f"Erro ao processar tabela Focus: {e}")
            st.write(df_focus.head())
    else:
        st.error("⚠️ Arquivo do Boletim Focus não encontrado.")
        st.info("Vá até a Home e clique em 'Forçar Atualização' para baixar os dados.")
