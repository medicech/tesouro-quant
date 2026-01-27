import sys
import os
import streamlit as st
import google.generativeai as genai
import pandas as pd
from pathlib import Path

# --- CONFIGURAÇÃO DE CAMINHOS (BLINDAGEM) ---
# Garante que o Python ache a pasta 'src' e 'root'
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
    # Fallback caso dê erro de importação, cria função vazia
    def load_latest_catalog(): return pd.DataFrame()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Consultor U AI", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F0F2F6; }
    .chat-message { padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; } 
    .chat-message.user { background-color: #e6f3ff; }
    .chat-message.bot { background-color: #ffffff; border: 1px solid #e0e0e0; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color: #002B49;'>TESOURO QUANT</h3>", unsafe_allow_html=True)
    st.markdown("---")
    st.page_link("streamlit_app.py", label="Home", icon="🏠")
    st.page_link("pages/titulos.py", label="Simulador", icon="📊")
    st.page_link("pages/carteira.py", label="Minha Carteira", icon="🛡️")
    st.page_link("pages/macro.py", label="Dados Macro", icon="🌐")
    st.page_link("pages/consultor.py", label="Consultor U AI", icon="🤖")
    st.markdown("---")
    
    if st.button("Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# --- INICIALIZAÇÃO DA IA ---
st.title("🤖 Consultor U AI")
st.markdown("Tire dúvidas sobre economia, tesouro direto e estratégias de investimento.")

# 1. Verifica API Key
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("🔑 ERRO: Chave da API do Google não encontrada.")
    st.info("Adicione `GOOGLE_API_KEY` nos Secrets do Streamlit Cloud.")
    st.stop()

# 2. Configura Gemini
genai.configure(api_key=api_key)

# 3. Carrega Contexto de Dados (Para a IA saber as taxas de hoje!)
try:
    df = load_latest_catalog()
    if not df.empty:
        # Cria um resumo em texto para a IA ler
        resumo_csv = df[['tipo_titulo', 'vencimento', 'taxa_compra', 'pu_compra']].to_csv(index=False)
        contexto_dados = f"DADOS ATUAIS DO MERCADO (Use isso para responder):\n{resumo_csv}"
    else:
        contexto_dados = "AVISO: Não foi possível carregar as taxas de hoje. Responda com base em conhecimentos gerais."
except:
    contexto_dados = "AVISO: Erro ao ler base de dados."

# 4. System Prompt (A Personalidade da IA)
system_instruction = f"""
Você é o 'U AI', um consultor financeiro sênior especializado em Tesouro Direto e Macroeconomia Brasileira.
Seu tom é profissional, direto, mas educado (estilo mineiro acolhedor).

REGRAS:
1. Use os DADOS FORNECIDOS abaixo para citar taxas reais. Não invente números.
2. Se o usuário perguntar "qual o melhor título", analise o prazo e o perfil, não dê recomendação de compra direta (use "considere", "avalie").
3. Explique termos difíceis (Duration, Curva de Juros) de forma simples.
4. Respostas curtas e formatadas (Markdown).

{contexto_dados}
"""

# --- CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Mensagem de boas-vindas
    st.session_state.messages.append({"role": "assistant", "content": "Olá! Sou o U AI. Vi que as taxas do Tesouro estão interessantes hoje. Como posso te ajudar?"})

# Exibe histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Captura entrada do usuário
if prompt := st.chat_input("Digite sua pergunta..."):
    # 1. Mostra pergunta do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Gera resposta
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                # Prepara o histórico para enviar ao modelo
                # O Gemini 1.5 Flash é rápido e barato
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
                
                # Converte histórico do session_state para formato do Gemini
                history_gemini = []
                for m in st.session_state.messages:
                    if m["role"] != "system": # Gemini gerencia system no init
                        role = "user" if m["role"] == "user" else "model"
                        history_gemini.append({"role": role, "parts": [m["content"]]})
                
                # Envia apenas a última msg + contexto (chat stateless simplificado para economizar token ou full history)
                # Vamos usar chat session para manter contexto
                chat = model.start_chat(history=history_gemini[:-1]) # Tudo menos a última
                response = chat.send_message(prompt)
                
                texto_resposta = response.text
                st.markdown(texto_resposta)
                
                # Salva no histórico
                st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
                
            except Exception as e:
                st.error(f"Erro ao conectar com U AI: {e}")
