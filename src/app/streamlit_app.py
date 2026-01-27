import sys
import os
import streamlit as st
import pandas as pd
import subprocess
from datetime import datetime
from pathlib import Path

# --- CONFIGURAÇÃO DE CAMINHOS (ADAPTADO PARA NUVEM) ---
# Garante que o Python ache as pastas 'src' e 'scripts' independente de onde esteja
current_dir = os.path.dirname(os.path.abspath(__file__)) # src/app/
src_dir = os.path.dirname(current_dir)                   # src/
root_dir = os.path.dirname(src_dir)                      # Raiz do projeto/

sys.path.append(src_dir)
sys.path.append(root_dir)

# Imports com tratamento de erro (Fallback para Nuvem)
try:
    from core.datasources.bcb_sgs import load_selic_meta, latest_value
    from core.config import DATA_DIR
except ImportError:
    load_selic_meta = None
    latest_value = None
    DATA_DIR = Path(root_dir) / "data"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Tesouro Quant | Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PREMIUM (VISUAL DO SEU PC) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #F0F2F6; font-family: 'Inter', sans-serif; }
    
    /* Remove navegação padrão feia */
    [data-testid="stSidebarNav"] { display: none !important; }
    
    /* --- ESTILO DOS CARDS INTERATIVOS --- */
    a.card-link { text-decoration: none; color: inherit; display: block; height: 100%; }
    
    .card-home {
        background-color: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #E0E0E0;
        text-align: left;
        height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s;
    }
    
    .card-home:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 24px rgba(0, 43, 73, 0.15);
        border-color: #002B49;
        cursor: pointer;
    }
    
    .card-title {
        color: #002B49;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .card-desc {
        color: #666;
        font-size: 14px;
        line-height: 1.5;
    }
    
    /* Card Azul (U AI) */
    .card-blue {
        background-color: #002B49 !important;
        border: 1px solid #002B49 !important;
    }
    .card-blue:hover {
        background-color: #003860 !important;
        box-shadow: 0 12px 24px rgba(0, 43, 73, 0.4);
    }
    
    /* Métricas */
    .big-metric { font-size: 32px; font-weight: 800; color: #002B49; }
    .metric-label { font-size: 12px; text-transform: uppercase; color: #888; font-weight: 600; }
    
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO ATUALIZAR (COM A LÓGICA DE CACHE CORRIGIDA) ---
def atualizar_dados():
    with st.status("🔄 Sincronizando Base de Dados...", expanded=True) as status:
        erros = []
        
        # Caminho absoluto para a pasta scripts
        scripts_path = os.path.join(root_dir, "scripts")
        
        # Lista de Scripts
        scripts = [
            ("Títulos", "run_fetch.py"),
            ("Selic", "run_fetch_selic.py"),
            ("Inflação", "run_fetch_inflation.py")
        ]

        for nome, script_file in scripts:
            st.write(f"📡 Atualizando {nome}...")
            try:
                full_path = os.path.join(scripts_path, script_file)
                # Usa sys.executable para garantir que rode no mesmo ambiente Python da Nuvem
                result = subprocess.run([sys.executable, full_path], capture_output=True, text=True)
                
                if result.returncode != 0:
                    erros.append(f"{nome}: {result.stderr}")
                else:
                    st.write(f"✅ {nome} ok.")
            except Exception as e:
                erros.append(f"{nome}: {str(e)}")
        
        if not erros:
            # O SEGREDO DO SUCESSO: LIMPAR O CACHE
            st.cache_data.clear()
            
            status.update(label="✅ Tudo pronto! Recarregando...", state="complete", expanded=False)
            st.toast("Base de dados 100% atualizada!", icon="🚀")
            st.rerun()
        else:
            status.update(label="❌ Erro na atualização", state="error")
            for err in erros:
                st.error(err)

# --- RENDERIZAÇÃO DA SIDEBAR ---
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
        
        if st.button("Forçar Atualização"): 
            atualizar_dados()

# --- RENDERIZAÇÃO DA HOME ---
def render_home():
    render_sidebar()
    
    st.title("Tesouro Quant")
    st.markdown("Plataforma de inteligência e precificação de títulos públicos.")
    st.markdown("---")

    # --- LÓGICA DE DADOS REAIS (Selic + IPCA Focus) ---
    selic_display = "--"
    ipca_display = "--"

    # 1. Carrega Selic
    try:
        path_proc = os.path.join(DATA_DIR, "processed")
        if load_selic_meta and latest_value:
            df_selic = load_selic_meta(path_proc)
            _, val_selic = latest_value(df_selic)
            if val_selic: selic_display = f"{val_selic:.2f}%"
    except: 
        selic_display = "11.25%" # Fallback visual

    # 2. Carrega IPCA (Focus)
    try:
        path_focus = os.path.join(DATA_DIR, "processed", "focus_ipca.parquet")
        if os.path.exists(path_focus):
            df_focus = pd.read_parquet(path_focus)
            ano_alvo = datetime.now().year
            
            # Tenta pegar meta deste ano ou do próximo
            row = df_focus[df_focus['DataReferencia'] == ano_alvo]
            if row.empty:
                row = df_focus[df_focus['DataReferencia'] == ano_alvo + 1]
            
            if not row.empty:
                val_ipca = row['Mediana'].iloc[0]
                ipca_display = f"{val_ipca:.2f}%"
    except: 
        ipca_display = "4.02%" # Fallback visual

    # --- CARDS DE MÉTRICAS (Visual Bonito) ---
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #002B49; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div class="metric-label">TAXA SELIC (META)</div>
            <div class="big-metric">{selic_display}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #CFA257; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <div class="metric-label">IPCA (FOCUS {datetime.now().year})</div>
            <div class="big-metric">{ipca_display}</div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.subheader("Aplicações")

    # --- GRID DE CARDS INTERATIVOS (Seu Visual Favorito) ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <a href="titulos" target="_self" class="card-link">
            <div class="card-home">
                <div class="card-title">📊 Simulador</div>
                <div class="card-desc">Precifique títulos em tempo real e compare rentabilidades.</div>
            </div>
        </a>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <a href="carteira" target="_self" class="card-link">
            <div class="card-home">
                <div class="card-title">🛡️ Gestão de Risco</div>
                <div class="card-desc">Controle sua duration, estresse e sensibilidade.</div>
            </div>
        </a>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <a href="macro" target="_self" class="card-link">
            <div class="card-home">
                <div class="card-title">🌐 Macro Dados</div>
                <div class="card-desc">Curva de Juros, Inflação Implícita e Boletim Focus.</div>
            </div>
        </a>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <a href="consultor" target="_self" class="card-link">
            <div class="card-home card-blue">
                <div class="card-title" style="color: white;">✨ U AI</div>
                <div class="card-desc" style="color: #E0E0E0;">Consultoria financeira inteligente baseada em IA.</div>
            </div>
        </a>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    render_home()
