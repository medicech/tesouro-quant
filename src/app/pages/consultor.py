import sys
import os
import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from pathlib import Path

# --- CONFIGURAÇÃO DE CAMINHOS (BLINDAGEM TOTAL) ---
# Garante que o Python ache a pasta 'src' independente de onde esteja rodando
current_dir = os.path.dirname(os.path.abspath(__file__)) # src/app/pages/
app_dir = os.path.dirname(current_dir)                   # src/app/
src_dir = os.path.dirname(app_dir)                       # src/
root_dir = os.path.dirname(src_dir)                      # root/

sys.path.append(src_dir)
sys.path.append(root_dir)

# --- IMPORTS SEGUROS ---
try:
    from core.catalogo import load_latest_catalog
except ImportError:
    # Fallback se não achar o core (evita tela de erro fatal)
    def load_latest_catalog(): return pd.DataFrame()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Consultor IA | Tesouro Quant", 
    page_icon="✨", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PREMIUM FINTECH ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #F0F2F6; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, h5, p, label, div { font-family: 'Inter', sans-serif !important; color: #333; }
    
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }

    /* CHAT STYLES */
    .stChatMessage { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 12px; padding: 15px; }
    .stChatMessage[data-testid="user-message"] { background-color: #E3F2FD; border-color: #BBDEFB; }
    .stChatInput > div { border-color: #E0E0E0 !important; background-color: #FFFFFF !important; color: #333 !important; }
    
    .secondary-btn button { background-color: transparent !important; color: #002B49 !important; border: 2px solid #002B49 !important; border-radius: 10px; font-weight: 600; }
    .secondary-btn button:hover { background-color: #E6EBF0 !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO QUE CAÇA O MODELO CERTO (A SALVAÇÃO) ---
def descobrir_modelo_disponivel():
    try:
        # Tenta pegar dos secrets ou variáveis de ambiente
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key: return None
        
        genai.configure(api_key=api_key)
        
        modelos_disponiveis = []
        # Lista modelos que suportam geração de texto
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelos_disponiveis.append(m.name)
        
        # Prioridade: 1. Flash (Rápido) -> 2. Pro (Forte) -> 3. Qualquer um
        for m in modelos_disponiveis:
            if 'flash' in m: return m
        for m in modelos_disponiveis:
            if 'pro' in m and 'vision' not in m: return m
            
        if modelos_disponiveis: return modelos_disponiveis[0]
        return None
    except Exception as e:
        print(f"Erro ao listar modelos: {e}")
        return None

# --- 🧠 PREPARAÇÃO DE DADOS (CONTEXTO) ---
def preparar_contexto_dados():
    try:
        df = load_latest_catalog()
        if df.empty: return "Nenhum título disponível hoje."
        
        # Seleciona colunas essenciais
        cols = ['tipo_titulo', 'ano_vencimento', 'taxa_compra', 'indexador']
        cols_existentes = [c for c in cols if c in df.columns]
        df_ia = df[cols_existentes].copy()

        # --- CORREÇÃO DE DADOS SUJOS ---
        # Filtra aberrações (ex: IPCA+ pagando 50%)
        if 'tipo_titulo' in df_ia.columns and 'taxa_compra' in df_ia.columns:
            mask_erro_ipca = (df_ia['tipo_titulo'].str.contains('IPCA')) & (df_ia['taxa_compra'] > 15.0)
            df_ia = df_ia[~mask_erro_ipca]

        return df_ia.to_string(index=False)
    except:
        return "Erro ao carregar dados de mercado."

# --- PROMPT REFINADO (SEU PROMPT ORIGINAL) ---
def get_instrucoes(contexto_dados):
    hoje = datetime.now()
    ano_atual = hoje.year
    
    return f"""
    Você é a 'U AI', Consultora Sênior de Renda Fixa do Tesouro Quant.
    
    DATA DE HOJE: {hoje.strftime('%d/%m/%Y')} (Ano Atual: {ano_atual})
    
    TABELA DE TÍTULOS DISPONÍVEIS AGORA:
    {contexto_dados}
    
    ---------------------------------------------------
    🛑 REGRAS DE LÓGICA OBRIGATÓRIAS (LEIA COM ATENÇÃO):
    
    1. PROIBIDO RECOMENDAR TÍTULOS CURTOS PARA LONGO PRAZO:
       - Se o usuário falar "Aposentadoria", "Futuro" ou "Longo Prazo":
       - VOCÊ DEVE IGNORAR qualquer título que vença antes de {ano_atual + 5} (Ex: Títulos 2026, 2027, 2028).
       - O motivo: Risco de Reinvestimento.
       - RECOMENDE: IPCA+ 2035, 2045 ou Renda+.
       
    2. FILTRO DE TAXAS REAIS vs NOMINAIS:
       - "Tesouro Prefixado" paga taxa NOMINAL (ex: 12%).
       - "Tesouro IPCA+" paga taxa REAL (ex: 6% + Inflação).
       - Nunca diga que um IPCA+ paga 10% fixo. Ele paga X% + variação da inflação.
       
    3. SEJA EDUCADA MAS FIRME:
       - Se o usuário quiser se aposentar com um título que vence ano que vem, ALERTE-O que isso é uma estratégia ruim.
    ---------------------------------------------------
    """

# --- RENDERIZAÇÃO ---
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
        st.info("**U AI:** Conectada.", icon="🧠")

def render():
    render_sidebar()

    # --- Header ---
    c_back, c_title = st.columns([1, 5]) 
    with c_back:
        st.write("") 
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("⬅ Voltar"): st.switch_page("streamlit_app.py")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with c_title:
        st.markdown("<h1 style='margin-top: 0; font-size: 32px; color: #002B49;'>Consultor U <span style='color:#CFA257'>AI</span></h1>", unsafe_allow_html=True)
        st.caption("Inteligência Artificial conectada aos dados do Tesouro Direto em Tempo Real.")

    # 1. Tenta descobrir modelo
    modelo_nome = descobrir_modelo_disponivel()
    
    if not modelo_nome:
        st.error("🚫 ERRO DE CONEXÃO: Não consegui acessar a API do Google.")
        st.warning("Verifique se a chave `GOOGLE_API_KEY` está configurada nos Secrets do Streamlit.")
        return 

    # 2. Carrega dados
    dados_mercado = preparar_contexto_dados()
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": f"Olá! Sou a U AI. Estou analisando as taxas de hoje. Como posso ajudar no seu planejamento?"}
        ]

    # 3. Exibe chat
    for message in st.session_state.messages:
        avatar = "👤" if message["role"] == "user" else "✨"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # 4. Input do usuário
    if prompt := st.chat_input("Ex: Quero me aposentar..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="✨"):
            msg_placeholder = st.empty()
            msg_placeholder.markdown("Raciocinando...")
            
            try:
                # Cria o modelo usando o nome descoberto dinamicamente (evita erro 404)
                model = genai.GenerativeModel(modelo_nome)
                
                # Monta histórico para contexto
                historico = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-4:]])
                prompt_final = f"{get_instrucoes(dados_mercado)}\n\nHISTÓRICO:\n{historico}\n\nUSUÁRIO AGORA: {prompt}\n\nRESPOSTA:"
                
                response = model.generate_content(prompt_final)
                
                msg_placeholder.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            except Exception as e:
                msg_placeholder.error(f"Erro técnico: {e}")

if __name__ == "__main__":
    render()
