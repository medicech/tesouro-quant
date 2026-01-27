from __future__ import annotations 

import sys
import os

# --- CORREÇÃO DE PATH ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '../..')))
sys.path.append(os.path.abspath(os.path.join(current_dir, '..')))
# ------------------------

import pandas as pd
import streamlit as st
import numpy as np
import plotly.graph_objects as go

from core.historico import load_history
from core.ettj import build_ettj
from core.expectativas import load_latest_expectativas_snapshot

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Macro Intelligence | Tesouro Quant", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PREMIUM FINTECH ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #F0F2F6; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, h5, p, label, div { font-family: 'Inter', sans-serif !important; color: #333; }
    
    /* Esconde menu padrão */
    [data-testid="stSidebarNav"] { display: none !important; }
    
    /* Sidebar customizada */
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
    
    /* Inputs */
    .stSelectbox > div > div {
        background-color: #FFFFFF; color: #333; border: 1px solid #E0E0E0; border-radius: 8px;
    }

    /* Tabs (Abas) Estilizadas Clean */
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

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-family: 'Inter', sans-serif; color: #002B49 !important; font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        color: #666 !important; font-size: 13px; text-transform: uppercase;
    }

    /* Cards Brancos para Gráficos */
    .chart-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }

    /* Botão Voltar */
    .secondary-btn button {
        background-color: transparent !important;
        color: #002B49 !important;
        border: 2px solid #002B49 !important;
        border-radius: 10px;
        font-weight: 600;
    }
    .secondary-btn button:hover { background-color: #E6EBF0 !important; }

</style>
""", unsafe_allow_html=True)

# --- Funções Auxiliares ---
def _fmt_date(d):
    return pd.to_datetime(d).strftime("%d/%m/%Y")

# --- Sidebar ---
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

    # --- Header ---
    c_back, c_title = st.columns([1, 5]) 
    with c_back:
        st.write("") 
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("⬅ Voltar"):
            st.switch_page("streamlit_app.py")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with c_title:
        st.markdown("<h1 style='margin-top: 0; font-size: 32px; color: #002B49;'>Macro Intelligence</h1>", unsafe_allow_html=True)
        st.caption("Análise técnica da Estrutura a Termo (ETTJ), Inflação Implícita e Boletim Focus.")

    # TABS
    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📉 Curva de Juros (ETTJ)", "🎣 Breakeven de Inflação", "🔮 Boletim Focus"])

    # Carregar histórico
    try:
        hist = load_history().copy()
        hist["data_base"] = pd.to_datetime(hist["data_base"])
        hist["data_vencimento"] = pd.to_datetime(hist["data_vencimento"])
        hist["prazo_dias"] = (hist["data_vencimento"] - hist["data_base"]).dt.days
        hist["prazo_anos"] = hist["prazo_dias"] / 365.25
        
        for c in ["taxa_compra", "taxa_venda"]:
            if c in hist.columns: hist[c] = pd.to_numeric(hist[c], errors="coerce")
        
        datas_disponiveis = sorted(hist["data_base"].unique())
        data_mais_recente = datas_disponiveis[-1]
    except Exception as e:
        st.error(f"Erro ao processar histórico: {e}")
        return

    # === ABA 1: CURVA DE JUROS (ETTJ) ===
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Filtros em Card
        with st.container():
            c1, c2 = st.columns(2)
            data_sel = c1.selectbox("Data Base", datas_disponiveis, index=len(datas_disponiveis)-1, format_func=_fmt_date)
            indexador = c2.selectbox("Família", ["IPCA", "PREFIXADO"], index=1) 

        # Processamento
        df_day = hist[hist["data_base"] == data_sel].copy()
        df_curve = df_day[df_day["indexador"] == indexador].copy()
        
        if indexador == "PREFIXADO":
            df_curve = df_curve[df_curve["cupom_txt"] == "SEM CUPOM"]
        else:
            pass 

        if len(df_curve) >= 3:
            ettj = build_ettj(df_curve, modo="Compra")
            vertices = ettj["vertices"]
            curva_interp = ettj["curve"]

            # Termômetro Slope
            ponto_curto = curva_interp.iloc[0]
            ponto_longo = curva_interp.iloc[-1]
            taxa_curta = ponto_curto["taxa_interp"]
            taxa_longa = ponto_longo["taxa_interp"]
            spread = taxa_longa - taxa_curta 
            spread_bps = spread * 100 
            
            if spread > 1.5: diagnostico = "Inclinação Alta (Prêmio de Risco)"
            elif spread > 0: diagnostico = "Normal"
            elif spread > -0.5: diagnostico = "Flat (Indecisão)"
            else: diagnostico = "Invertida (Risco Recessão)"

            st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("Taxa Curta (1y)", f"{taxa_curta:.2f}%")
            m2.metric("Taxa Longa (Terminal)", f"{taxa_longa:.2f}%")
            m3.metric("Spread (Inclinação)", f"{spread_bps:.0f} bps", diagnostico)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

            # --- PLOTLY CHART (DESIGN NOVO) ---
            st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
            fig = go.Figure()
            
            # Pontos Reais (Dourado/Mustard)
            fig.add_trace(go.Scatter(
                x=vertices["prazo_anos"], y=vertices["taxa"],
                mode='markers', name='Títulos Negociados', 
                marker=dict(size=10, color='#CFA257', line=dict(width=1, color='white'))
            ))
            
            # Curva Interpolada (Azul Navy)
            fig.add_trace(go.Scatter(
                x=curva_interp["prazo_anos"], y=curva_interp["taxa_interp"],
                mode='lines', name='Curva Interpolada', 
                line=dict(color='#002B49', width=3, shape='spline')
            ))

            fig.update_layout(
                title=f"<b>Curva de Juros {indexador}</b> | {_fmt_date(data_sel)}",
                xaxis_title="Prazo (Anos)", yaxis_title="Taxa (% a.a.)",
                height=500,
                template="plotly_white", # Fundo Branco Limpo
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter", color="#333"),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            # Gridlines suaves
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.info("💡 **Conceito:** O 'Spread' mede a diferença entre o juro longo e o curto. Curvas muito inclinadas indicam que o mercado exige prêmio alto para emprestar a longo prazo (Risco Fiscal).")
        else:
            st.warning(f"Dados insuficientes ({len(df_curve)} títulos) nesta data.")

    # === ABA 2: FISHER (Inflação Implícita) ===
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Inflação Implícita (Breakeven)")
        st.caption("Quanto o mercado precifica de inflação futura ao comparar títulos Prefixados vs IPCA+.")
        
        try:
            df_pre = df_day[(df_day["indexador"] == "PREFIXADO") & (df_day["cupom_txt"] == "SEM CUPOM")]
            df_ipca = df_day[(df_day["indexador"] == "IPCA") & (df_day["cupom_txt"] == "COM CUPOM")]
            if len(df_ipca) < 2: df_ipca = df_day[(df_day["indexador"] == "IPCA") & (df_day["cupom_txt"] == "SEM CUPOM")]

            if len(df_pre) >= 2 and len(df_ipca) >= 2:
                ettj_nom = build_ettj(df_pre)["curve"]
                ettj_real = build_ettj(df_ipca)["curve"]
                merged = pd.merge(ettj_nom, ettj_real, on="prazo_anos", suffixes=("_nom", "_real"))
                merged["inflacao_impl"] = ((1 + merged["taxa_interp_nom"]/100) / (1 + merged["taxa_interp_real"]/100) - 1) * 100
                merged = merged[(merged["prazo_anos"] >= 1) & (merged["prazo_anos"] <= 10)]

                if not merged.empty:
                    st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
                    fig2 = go.Figure()
                    
                    fig2.add_trace(go.Scatter(
                        x=merged["prazo_anos"], y=merged["inflacao_impl"],
                        mode='lines', name='IPCA Implícito', 
                        line=dict(color='#002B49', width=3), 
                        fill='tozeroy', fillcolor='rgba(0, 43, 73, 0.1)' # Azul Navy suave
                    ))
                    
                    fig2.update_layout(
                        title=f"<b>Inflação Implícita (Fisher)</b> - {_fmt_date(data_sel)}",
                        xaxis_title="Prazo (Anos)", yaxis_title="IPCA Esperado (% a.a.)",
                        height=500,
                        template="plotly_white",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Inter", color="#333"),
                        hovermode="x unified"
                    )
                    fig2.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
                    fig2.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')

                    st.plotly_chart(fig2, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    ipca_medio = merged["inflacao_impl"].mean()
                    st.success(f"📌 O mercado hoje precifica uma inflação média de **{ipca_medio:.2f}% a.a.** para a próxima década.")
                else: st.warning("Sem sobreposição de prazos suficiente.")
            else: st.warning("Não há pares suficientes de Prefixado/IPCA para calcular Fisher nesta data.")
        except Exception as e: st.error(f"Erro em Fisher: {e}")

    # === ABA 3: BOLETIM FOCUS ===
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Expectativas de Mercado (Banco Central)")
        
        try:
            df_focus = load_latest_expectativas_snapshot()
            if not df_focus.empty:
                data_focus = df_focus["data"].max()
                
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #E0E0E0; display: inline-block; margin-bottom: 20px;">
                    <span style="color: #666; font-size: 12px;">DATA DO RELATÓRIO</span><br>
                    <span style="color: #002B49; font-size: 18px; font-weight: bold;">{_fmt_date(data_focus)}</span>
                </div>
                """, unsafe_allow_html=True)
                
                focus_main = df_focus[df_focus["indicador"].isin(["IPCA", "Selic", "PIB Total", "Câmbio"])]
                
                if not focus_main.empty:
                    pivot = focus_main.pivot_table(index="indicador", columns="ano", values="mediana")
                    
                    # Estilizando a tabela com Pandas Styler para ficar clean
                    st.dataframe(
                        pivot.style.format("{:.2f}"), 
                        use_container_width=True
                    )
                    st.caption("Fonte: API Olinda/Bacen. Mediana das expectativas de mercado.")
            else: st.warning("Dados do Focus não encontrados.")
        except: st.error("Erro ao carregar Focus.")

if __name__ == "__main__":
    render()