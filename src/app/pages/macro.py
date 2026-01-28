import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# --- PATH CONFIGURATION ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
possible_roots = [Path(root_dir), Path(os.getcwd()), Path("/mount/src/tesouro-quant")]

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Macro Intelligence | Tesouro Quant", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PREMIUM FINTECH CSS (FROM PREVIOUS DESIGN) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #F0F2F6; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, h5, p, label, div { font-family: 'Inter', sans-serif !important; color: #333; }
    
    /* Hide standard menu */
    [data-testid="stSidebarNav"] { display: none !important; }
    
    /* Custom Sidebar */
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
    
    /* Inputs */
    .stSelectbox > div > div, .stMultiSelect > div > div, .stNumberInput > div > div {
        background-color: #FFFFFF; color: #333; border: 1px solid #E0E0E0; border-radius: 8px;
    }

    /* Tabs Clean Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
        border-bottom: 1px solid #E0E0E0;
        padding-bottom: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        color: #666;
        font-weight: 400;
        font-size: 14px;
        padding: 10px 0;
    }
    .stTabs [aria-selected="true"] {
        color: #002B49 !important;
        font-weight: 700 !important;
        border-bottom: 3px solid #002B49 !important;
    }

    /* Cards */
    .chart-card {
        background-color: white;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 20px;
    }

    /* Secondary Button (Voltar) */
    .secondary-btn button {
        background-color: transparent !important;
        color: #002B49 !important;
        border: 2px solid #002B49 !important;
        border-radius: 10px;
        font-weight: 600;
    }
    .secondary-btn button:hover { background-color: #E6EBF0 !important; }
    
    /* Info Box */
    .info-box {
        background-color: #E3F2FD;
        border: 1px solid #BBDEFB;
        border-radius: 8px;
        padding: 15px;
        color: #002B49;
        font-size: 14px;
        margin-top: 10px;
    }

</style>
""", unsafe_allow_html=True)

# --- DATA LOADING FUNCTION (CURRENT LOGIC) ---
def carregar_arquivo(nome_arquivo):
    for root in possible_roots:
        path = root / "data" / "processed" / nome_arquivo
        if path.exists(): return pd.read_parquet(path), path
        path_local = Path("data/processed") / nome_arquivo
        if path_local.exists(): return pd.read_parquet(path_local), path_local
    return pd.DataFrame(), None

# --- LOAD DATA ---
df_focus, _ = carregar_arquivo("focus_ipca.parquet")
df_titulos, _ = carregar_arquivo("tesouro_catalogo_2026-01-28.parquet")
if df_titulos.empty:
    try:
        p = Path("data/processed")
        files = sorted(list(p.glob("tesouro_catalogo_*.parquet")))
        if files: df_titulos = pd.read_parquet(files[-1])
    except: pass

# --- PREPARE DATA ---
if not df_titulos.empty:
    if 'vencimento' in df_titulos.columns: df_titulos['vencimento'] = pd.to_datetime(df_titulos['vencimento'])
    if 'data_base' in df_titulos.columns: df_titulos['data_base'] = pd.to_datetime(df_titulos['data_base'])
    else: df_titulos['data_base'] = pd.Timestamp.now()
    
    df_titulos['prazo_anos'] = (df_titulos['vencimento'] - df_titulos['data_base']).dt.days / 365.25

# --- SIDEBAR (PREVIOUS DESIGN) ---
def render_sidebar():
    with st.sidebar:
        st.markdown("<h3 style='color: #002B49;'>TESOURO QUANT</h3>", unsafe_allow_html=True)
        st.caption("Terminal Inteligente v1.0")
        st.markdown("---")
        st.page_link("streamlit_app.py", label="Home", icon="🏠")
        st.page_link("pages/titulos.py", label="Simulador", icon="📊")
        st.page_link("pages/carteira.py", label="Minha Carteira", icon="🛡️")
        st.page_link("pages/macro.py", label="Dados Macro", icon="🌐")
        st.page_link("pages/consultor.py", label="Consultor U AI", icon="🤖")
        st.markdown("---")

def render():
    render_sidebar()

    # --- HEADER ---
    c_back, c_title = st.columns([1, 5]) 
    with c_back:
        st.write("") 
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("⬅ Voltar"): st.switch_page("streamlit_app.py")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with c_title:
        st.markdown("<h1 style='margin-top: 0; font-size: 32px; color: #002B49;'>Macro Intelligence</h1>", unsafe_allow_html=True)
        st.caption("Análise técnica da Estrutura a Termo (ETTJ), Inflação Implícita e Boletim Focus.")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["📉 Curva de Juros (Nominal)", "🎈 Breakeven de Inflação", "🔮 Boletim Focus"])

    # --- TAB 1: CURVA DE JUROS (CURRENT LOGIC + NEW DESIGN) ---
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not df_titulos.empty:
            
            # CONTROL PANEL (Wrapped in styled container)
            st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #002B49; margin-bottom: 20px;'>⚙️ Painel de Controle</h4>", unsafe_allow_html=True)
            
            # Row 1: Assumptions
            c_input1, c_input2 = st.columns(2)
            user_ipca = c_input1.number_input("IPCA Projetado (% a.a.)", value=4.0, step=0.1, help="Converte IPCA+ em Nominal")
            user_selic = c_input2.number_input("Selic Média (% a.a.)", value=10.0, step=0.25, help="Define retorno do Tesouro Selic")
            
            st.markdown("<hr style='margin: 20px 0; border: 0; border-top: 1px solid #E0E0E0;'>", unsafe_allow_html=True)
            
            # Row 2: Filters
            c_filt1, c_filt2 = st.columns(2)
            
            # Filter 1: Indexer
            all_indexes = df_titulos['indexador'].unique()
            sel_indexes = c_filt1.multiselect("1. Filtrar Família", all_indexes, default=['PREFIXADO', 'IPCA'])
            
            # Filter 2: Specific Titles
            df_step1 = df_titulos[df_titulos['indexador'].isin(sel_indexes)]
            all_titles = sorted(df_step1['tipo_titulo'].unique())
            
            default_titles = [t for t in all_titles if "Renda+" not in t and "Educa+" not in t]
            sel_titles = c_filt2.multiselect("2. Selecionar Títulos Específicos", all_titles, default=default_titles)
            st.markdown("</div>", unsafe_allow_html=True) # End Control Panel

            # --- CHART PROCESSING ---
            df_chart = df_step1[df_step1['tipo_titulo'].isin(sel_titles)].copy()

            def calcular_nominal(row):
                taxa_fixa = float(row['taxa_compra'])
                idx = row['indexador']
                
                if idx == 'PREFIXADO':
                    return taxa_fixa, f"Prefixado: {taxa_fixa:.2f}%"
                elif idx == 'IPCA':
                    nominal = ((1 + taxa_fixa/100) * (1 + user_ipca/100) - 1) * 100
                    return nominal, f"Real: {taxa_fixa:.2f}% + IPCA: {user_ipca:.2f}%"
                elif idx == 'SELIC':
                    nominal = user_selic + taxa_fixa
                    return nominal, f"Selic: {user_selic:.2f}% + Spread: {taxa_fixa:.2f}%"
                return taxa_fixa, str(taxa_fixa)

            if not df_chart.empty:
                df_chart[['taxa_projetada', 'detalhe_taxa']] = df_chart.apply(
                    lambda x: pd.Series(calcular_nominal(x)), axis=1
                )

                st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
                fig = px.line(
                    df_chart.sort_values('prazo_anos'), 
                    x="vencimento", 
                    y="taxa_projetada", 
                    color="indexador",
                    markers=True,
                    title=f"<b>Curva Nominal</b> (IPCA {user_ipca}% | Selic {user_selic}%)",
                    labels={"taxa_projetada": "Taxa Nominal (% a.a.)", "vencimento": "Vencimento"},
                    color_discrete_map={"PREFIXADO": "#D32F2F", "IPCA": "#1976D2", "SELIC": "#388E3C"},
                    custom_data=['tipo_titulo', 'detalhe_taxa']
                )
                
                fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>%{x|%d/%m/%Y}<br>Taxa: %{y:.2f}%<br><i>%{customdata[1]}</i>")
                
                # Apply Premium Layout from previous design
                fig.update_layout(
                    height=500, 
                    hovermode="x unified",
                    template="plotly_white",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Inter", color="#333"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
                
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("Nenhum título selecionado.")
        else:
            st.error("Sem dados de títulos.")

    # --- TAB 2: BREAKEVEN ---
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Inflação Implícita")
        st.caption("Quanto o mercado precifica de inflação futura ao comparar títulos Prefixados vs IPCA+.")
        
        if not df_titulos.empty:
            try:
                df_pre = df_titulos[df_titulos['indexador'] == 'PREFIXADO'][['ano_vencimento', 'taxa_compra']].groupby('ano_vencimento').mean()
                df_ipca = df_titulos[df_titulos['indexador'] == 'IPCA'][['ano_vencimento', 'taxa_compra']].groupby('ano_vencimento').mean()
                
                df_break = df_pre.join(df_ipca, lsuffix='_pre', rsuffix='_ipca', how='inner')
                df_break['breakeven'] = (((1 + df_break['taxa_compra_pre']/100) / (1 + df_break['taxa_compra_ipca']/100)) - 1) * 100
                
                st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
                fig_break = px.bar(
                    df_break.reset_index(), 
                    x='ano_vencimento', 
                    y='breakeven', 
                    text_auto='.2f', 
                    title="<b>Inflação Implícita (%)</b>", 
                    color_discrete_sequence=['#CFA257'] # Using Gold/Mustard from design
                )
                
                # Premium Layout
                fig_break.update_layout(
                    height=500,
                    template="plotly_white",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Inter", color="#333"),
                    hovermode="x unified"
                )
                fig_break.update_xaxes(showgrid=False)
                fig_break.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
                
                st.plotly_chart(fig_break, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            except: st.warning("Dados insuficientes.")

    # --- TAB 3: FOCUS ---
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Expectativas de Mercado (Banco Central)")
        
        if not df_focus.empty:
            data_rel = pd.to_datetime(df_focus['Data'].max()).strftime('%d/%m/%Y')
            
            st.markdown(f"""
            <div style="background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #E0E0E0; display: inline-block; margin-bottom: 20px;">
                <span style="color: #666; font-size: 12px;">RELATÓRIO VIGENTE</span><br>
                <span style="color: #002B49; font-size: 18px; font-weight: bold;">{data_rel}</span>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                df_view = df_focus[df_focus['Indicador'].isin(['IPCA', 'Selic'])].copy()
                df_view = df_view[df_view['DataReferencia'].isin([2026, 2027, 2028, 2029])]
                
                if df_view.empty:
                    st.warning("O arquivo existe, mas não contém dados de IPCA/Selic para os próximos anos.")
                else:
                    pivoted = df_view.pivot_table(index='Indicador', columns='DataReferencia', values='Mediana', aggfunc='first')
                    
                    st.dataframe(
                        pivoted.style.format("{:.2f}%"), 
                        use_container_width=True
                    )
                    st.caption("Fonte: API Olinda/Bacen.")
            except Exception as e:
                st.error(f"Erro na tabela: {e}")
        else:
            st.warning("Dados do Focus não encontrados.")

if __name__ == "__main__":
    render()
