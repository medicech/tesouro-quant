import streamlit as st
import pandas as pd
import sys
import os
import subprocess
from pathlib import Path

# --- CONFIGURAÇÃO DE PATH ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(current_dir), 'core'))
sys.path.append(os.path.dirname(current_dir))

# Tenta importar módulos internos
try:
    from core.config import DATA_DIR
    from core.datasources.bcb_sgs import load_selic_meta, latest_value
    from core.datasources.bcb_expectativas import load_latest_snapshot
except ImportError:
    DATA_DIR = Path("data") # Fallback
    def load_selic_meta(p): return pd.DataFrame()
    def latest_value(df): return pd.Timestamp.today(), 0.0
    def load_latest_snapshot(): return pd.DataFrame()

# --- PAGE CONFIG ---
st.set_page_config(page_title="Tesouro Quant", page_icon="🏛️", layout="wide")

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 5px solid #002B49;
    }
    .big-number { font-size: 36px; font-weight: bold; color: #002B49; }
    .label { font-size: 14px; color: #666; text-transform: uppercase; letter-spacing: 1px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### TESOURO QUANT\nTerminal Inteligente v1.0")
    st.markdown("---")
    st.page_link("streamlit_app.py", label="Home", icon="🏠")
    st.page_link("pages/titulos.py", label="Simulador", icon="📊")
    st.page_link("pages/carteira.py", label="Minha Carteira", icon="🛡️")
    st.page_link("pages/macro.py", label="Dados Macro", icon="🌐")
    st.page_link("pages/consultor.py", label="Consultor U AI", icon="🤖")
    
    st.markdown("---")
    
    # --- BOTÃO DE ATUALIZAÇÃO COM LIMPEZA DE CACHE ---
    if st.button("Forçar Atualização"):
        with st.status("🔄 Sincronizando dados...", expanded=True) as status:
            
            # 1. Define caminhos dos scripts
            root_scripts = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'scripts')
            script_titles = os.path.join(root_scripts, "run_fetch.py")
            script_selic = os.path.join(root_scripts, "run_fetch_selic.py")
            script_focus = os.path.join(root_scripts, "run_fetch_inflation.py")
            
            # 2. Executa os robôs
            errors = []
            
            st.write("📡 Baixando Títulos do Tesouro...")
            res1 = subprocess.run([sys.executable, script_titles], capture_output=True, text=True)
            if res1.returncode != 0: errors.append(f"Títulos: {res1.stderr}")
            
            st.write("🏦 Consultando Banco Central (Selic)...")
            res2 = subprocess.run([sys.executable, script_selic], capture_output=True, text=True)
            if res2.returncode != 0: errors.append(f"Selic: {res2.stderr}")

            st.write("🔮 Lendo Boletim Focus...")
            res3 = subprocess.run([sys.executable, script_focus], capture_output=True, text=True)
            if res3.returncode != 0: errors.append(f"Focus: {res3.stderr}")

            # 3. Finalização e LIMPEZA DE CACHE
            if not errors:
                st.cache_data.clear() # <--- O SEGREDO ESTÁ AQUI!
                status.update(label="✅ Tudo pronto!", state="complete", expanded=False)
                st.success("Base de dados 100% atualizada!")
                st.rerun() # Recarrega a página na força
            else:
                status.update(label="❌ Erro na atualização", state="error")
                for err in errors: st.error(err)

# --- MAIN PAGE ---
st.title("Tesouro Quant")
st.markdown("Plataforma de inteligência e precificação de títulos públicos.")
st.markdown("---")

# Carrega Dados para Cards
try:
    path_proc = Path(DATA_DIR) / "processed"
    
    # Selic
    df_selic = load_selic_meta(path_proc)
    _, selic_atual = latest_value(df_selic)
    
    # IPCA (Focus)
    try:
        df_focus = pd.read_parquet(path_proc / "focus_ipca.parquet")
        # Pega a mediana do ano seguinte ao atual (ex: 2026 se estivermos em 2025/26 simulado)
        meta_ipca = df_focus['Mediana'].iloc[0]
    except:
        meta_ipca = 4.00

except Exception:
    selic_atual = 0.0
    meta_ipca = 0.0

# Cards
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""<div class="metric-card"><div class="label">Taxa Selic (Meta)</div><div class="big-number">{selic_atual:.2f}%</div></div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="metric-card" style="border-left-color: #CFA257;"><div class="label">IPCA (Focus 2026)</div><div class="big-number">{meta_ipca:.2f}%</div></div>""", unsafe_allow_html=True)

st.markdown("### Aplicações")

a1, a2, a3, a4 = st.columns(4)

with a1:
    with st.container(border=True):
        st.subheader("📊 Simulador")
        st.write("Precifique títulos em tempo real e compare rentabilidades.")

with a2:
    with st.container(border=True):
        st.subheader("🛡️ Gestão de Risco")
        st.write("Controle sua duration, estresse e sensibilidade.")

with a3:
    with st.container(border=True):
        st.subheader("🌐 Macro Dados")
        st.write("Curva de Juros, Inflação Implícita e Boletim Focus.")

with a4:
    with st.container(border=True): # Style U AI
        st.markdown('<div style="background-color: #002B49; padding: 10px; border-radius: 5px; color: white;">✨ <b>U AI</b><br><span style="font-size: 12px">Consultoria financeira inteligente baseada em IA.</span></div>', unsafe_allow_html=True)

# --- ÁREA DE DEBUG (PARA VOCÊ VER O QUE ESTÁ ACONTECENDO) ---
with st.expander("🕵️‍♂️ Diagnóstico do Servidor (Debug)", expanded=False):
    st.write(f"📂 Diretório Atual: `{os.getcwd()}`")
    processed_path = Path(DATA_DIR) / "processed"
    st.write(f"📂 Pasta Processed: `{processed_path}`")
    
    if processed_path.exists():
        files = list(processed_path.glob("*"))
        st.write(f"📄 Arquivos encontrados ({len(files)}):")
        for f in files:
            st.code(f"{f.name} - {f.stat().st_size} bytes")
    else:
        st.error("❌ A pasta 'processed' NÃO EXISTE neste servidor.")
