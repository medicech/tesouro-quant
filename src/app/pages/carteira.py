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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Carteira | Tesouro Quant", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PREMIUM FINTECH ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #F0F2F6; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, h5, p, label { font-family: 'Inter', sans-serif !important; color: #333; }
    
    /* Esconde menu padrão */
    [data-testid="stSidebarNav"] { display: none !important; }
    
    /* Sidebar customizada */
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
    
    /* Inputs */
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div {
        background-color: #FFFFFF; color: #333; border: 1px solid #E0E0E0; border-radius: 8px;
    }

    /* KPI Cards */
    .kpi-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-left: 5px solid #002B49;
        margin-bottom: 20px;
    }
    .kpi-label { font-size: 12px; text-transform: uppercase; font-weight: 600; color: #888; margin-bottom: 5px; }
    .kpi-value { font-size: 24px; font-weight: 700; color: #002B49; }

    /* Estilos de Texto da Tabela */
    .cell-label { font-size: 11px; color: #999; text-transform: uppercase; margin-bottom: 2px; }
    .cell-value { font-size: 15px; font-weight: 600; color: #333; }
    .cell-title { font-size: 16px; font-weight: 700; color: #002B49; }

    /* Botão Voltar */
    .secondary-btn button {
        background-color: transparent !important;
        color: #002B49 !important;
        border: 2px solid #002B49 !important;
        border-radius: 10px;
        font-weight: 600;
    }
    .secondary-btn button:hover { background-color: #E6EBF0 !important; }
    
    /* Botão Excluir - Ajuste Fino */
    div[data-testid="column"] button {
        border-radius: 8px;
        border: 1px solid #FFCDD2;
        background-color: white;
        color: #D32F2F;
        transition: all 0.2s;
    }
    div[data-testid="column"] button:hover {
        background-color: #FFEBEE;
        border-color: #D32F2F;
        color: #B71C1C;
    }

</style>
""", unsafe_allow_html=True)

# --- Formatação ---
def _brl(x: float) -> str:
    return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
        st.markdown("<h1 style='margin-top: 0; font-size: 32px; color: #002B49;'>Minha Carteira</h1>", unsafe_allow_html=True)
        st.caption("Monitoramento de risco, duration e testes de estresse.")

    if "portfolio" not in st.session_state or not st.session_state.portfolio:
        st.info("👈 Sua carteira está vazia.")
        st.markdown("""
        <div style="background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #DDD;">
            <h4 style="margin: 0; color: #002B49;">Como começar?</h4>
            <p style="color: #666;">Vá até o <b>Simulador</b>, escolha um título e clique em <b>Adicionar à Carteira</b>.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Cálculos
    total_investido = 0.0
    soma_duration_ponderada = 0.0
    
    for item in st.session_state.portfolio:
        val_total = item["pu_compra"] * item["qtd"]
        total_investido += val_total
        dur = item["metrics"].get("duration_modified_anos", 0)
        soma_duration_ponderada += (dur * val_total)
    
    duration_media = soma_duration_ponderada / total_investido if total_investido > 0 else 0

    if duration_media < 2: nivel = "🟢 Baixa (Conservador)"
    elif duration_media < 6: nivel = "🟡 Média (Moderado)"
    else: nivel = "🔴 Alta (Arrojado)"

    # --- KPI Cards ---
    st.markdown("<br>", unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    
    with k1:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Patrimônio Total</div><div class="kpi-value">{_brl(total_investido)}</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card" style="border-left-color: #CFA257;"><div class="kpi-label">Duration Média</div><div class="kpi-value">{duration_media:.2f} Anos</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="kpi-card" style="border-left-color: #999;"><div class="kpi-label">Nível de Risco</div><div class="kpi-value" style="font-size: 18px; padding-top: 4px;">{nivel}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # --- Stress Test ---
    st.subheader("🌪️ Teste de Estresse")
    
    with st.container():
        st.markdown('<div style="background-color: white; padding: 25px; border-radius: 16px; border: 1px solid #E0E0E0;">', unsafe_allow_html=True)
        
        cenarios = {
            "Personalizado": 0,
            "📉 Otimismo: Queda de Juros (-1%)": -100,
            "📈 Risco Fiscal: Juros Sobem (+1%)": 100,
            "🚨 Pânico de Mercado: Juros Explodem (+2%)": 200,
            "🕊️ Corte Agressivo da Selic (-2%)": -200
        }
        
        cs1, cs2 = st.columns(2)
        with cs1:
            cenario_sel = st.selectbox("Selecione o Cenário:", list(cenarios.keys()))
            valor_cenario = cenarios[cenario_sel]
        
        with cs2:
            if cenario_sel == "Personalizado":
                choque = st.number_input("Choque Manual (bps):", value=0, step=10)
            else:
                choque = valor_cenario
                st.markdown(f"<div style='margin-top: 32px; color: #666;'>Simulando choque de <b>{choque} bps</b></div>", unsafe_allow_html=True)

        if choque != 0:
            delta_y = choque / 10000.0
            impacto = -soma_duration_ponderada * delta_y
            novo_patrimonio = total_investido + impacto
            var_pct = (impacto / total_investido) * 100
            
            st.markdown("<hr style='margin: 20px 0; border-top: 1px solid #EEE;'>", unsafe_allow_html=True)
            res1, res2 = st.columns(2)
            res1.metric("Saldo Projetado", _brl(novo_patrimonio))
            res2.metric("Impacto (Mark-to-Market)", f"{_brl(impacto)}", f"{var_pct:.2f}%", delta_color="inverse")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Lista de Ativos (Layout Novo e Limpo) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📋 Ativos Custodiados")

    # Headers alinhados
    # Usamos container border=False para alinhar, mas o fundo é cinza da página
    h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 2, 1])
    h1.markdown("**TÍTULO**")
    h2.markdown("**TAXA**")
    h3.markdown("**VENCIMENTO**")
    h4.markdown("**VALOR**")
    h5.markdown("")

    for i, item in enumerate(st.session_state.portfolio):
        val_total_item = item["pu_compra"] * item["qtd"]
        
        # Cria um container branco (Card) para cada linha
        # Isso substitui a DIV HTML manual e corrige o layout
        with st.container():
            st.markdown(
                """<div style="background-color: white; border-radius: 12px; padding: 10px; border: 1px solid #E0E0E0; margin-bottom: 8px;">""", 
                unsafe_allow_html=True
            )
            
            # ATENÇÃO: vertical_alignment='center' é a chave aqui! (Requer Streamlit > 1.31)
            # Se der erro, remova o argumento, mas a maioria já tem atualizado.
            try:
                c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1], vertical_alignment="center")
            except TypeError:
                # Fallback para versões antigas
                c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])

            with c1:
                st.markdown(f"<div class='cell-title'>{item['id']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='cell-label'>{item['indexador']}</div>", unsafe_allow_html=True)
            
            with c2:
                st.markdown(f"<div class='cell-value'>{item['taxa_compra']:.2f}%</div>", unsafe_allow_html=True)
            
            with c3:
                st.markdown(f"<div class='cell-value'>{item['vencimento'].strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
            
            with c4:
                st.markdown(f"<div class='cell-value'>{_brl(val_total_item)}</div>", unsafe_allow_html=True)
            
            with c5:
                # Botão de Lixeira limpo e nativo
                if st.button("🗑️", key=f"del_{i}", help="Remover"):
                    st.session_state.portfolio.pop(i)
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True) # Fecha o container visual

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Limpar Carteira Completa", type="secondary"):
        st.session_state.portfolio = []
        st.rerun()

if __name__ == "__main__":
    render()