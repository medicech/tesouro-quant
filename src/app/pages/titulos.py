import sys
import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# --- CONFIGURAÇÃO DE CAMINHOS (FORTIFICADA) ---
current_dir = os.path.dirname(os.path.abspath(__file__)) # src/app/pages/
app_dir = os.path.dirname(current_dir)                   # src/app/
src_dir = os.path.dirname(app_dir)                       # src/
root_dir = os.path.dirname(src_dir)                      # root/

sys.path.append(src_dir)
sys.path.append(root_dir)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Simulador | Tesouro Quant", page_icon="📊", layout="wide")

# --- CSS PREMIUM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    .stApp { background-color: #F0F2F6; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebarNav"] { display: none !important; }
    
    .highlight-card { 
        background-color: #FFFFFF; 
        padding: 20px; 
        border-radius: 16px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
        border-left: 5px solid #002B49; 
        margin-bottom: 20px; 
    }
    
    .timeline-card { 
        background-color: #E3F2FD; 
        padding: 10px; 
        border-radius: 12px; 
        border: 1px solid #BBDEFB; 
        text-align: center; 
        color: #002B49; 
        height: 110px; 
        display: flex; 
        flex-direction: column; 
        justify-content: center; 
        align-items: center; 
    }
    
    .primary-btn button { 
        background-color: #002B49 !important; 
        color: white !important; 
        border-radius: 10px; 
        border: none; 
        font-weight: 600; 
    }
    .primary-btn button:hover { background-color: #00406c !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE CARGA BLINDADA (ROBUSTEZ TOTAL) ---
def carregar_dados_blindado():
    """Tenta carregar o catálogo de qualquer lugar possível."""
    try:
        # 1. Tenta definir onde buscar
        possible_paths = [
            Path(root_dir) / "data" / "processed",           # Caminho relativo calculado
            Path("data/processed"),                          # Caminho relativo simples
            Path("/mount/src/tesouro-quant/data/processed"), # Caminho absoluto Streamlit Cloud
            Path(os.getcwd()) / "data" / "processed"         # Caminho absoluto local
        ]
        
        found_file = None
        
        # 2. Varre as pastas
        for pasta in possible_paths:
            if pasta.exists():
                # Busca arquivos que começam com 'tesouro_catalogo'
                files = list(pasta.glob("tesouro_catalogo_*.parquet"))
                if files:
                    # Pega o último (mais recente)
                    found_file = sorted(files)[-1]
                    break
        
        # 3. Carrega se achou
        if found_file:
            df = pd.read_parquet(found_file)
            return df, str(found_file)
            
        return pd.DataFrame(), None

    except Exception as e:
        return pd.DataFrame(), None

# --- FUNÇÕES DE NEGÓCIO ---
def _pct(x): return f"{x:.2f}%" if pd.notna(x) else "-"
def _brl(x): return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) else "-"

def calcular_aliquota_ir(dias: int) -> float:
    if dias <= 180: return 22.5
    if dias <= 360: return 20.0
    if dias <= 720: return 17.5
    return 15.0

def fmt_taxa_humanizada(row, col_taxa):
    val = row.get(col_taxa)
    if pd.isna(val): return "-"
    idx = str(row.get("indexador", "")).upper()
    if "IPCA" in idx: return f"IPCA + {val:.2f}%"
    elif "SELIC" in idx: return f"SELIC + {val:.4f}%"
    else: return f"{val:.2f}%"

def analisar_oportunidade(row, ipca_proj):
    insights = []
    score_visual = ""
    idx = str(row.get("indexador", "")).upper()
    taxa = float(row.get("taxa_compra", 0))
    prazo_anos = float(row.get("prazo_anos", 0))
    
    if "IPCA" in idx:
        if taxa >= 6.0:
            score_visual = "🔥 OPORTUNIDADE HISTÓRICA"
            insights.append("Taxa Real acima de 6% é rara. Excelente ponto de entrada.")
        elif taxa >= 5.0: score_visual = "✅ ÓTIMA RENTABILIDADE"
        else: score_visual = "😐 TAXA NEUTRA"
    elif "PREFIXADO" in idx:
        if taxa >= 12.5: score_visual = "🚀 TAXA ALTA"
        elif taxa >= 10.0: score_visual = "✅ TAXA OK"
        else: score_visual = "⚠️ TAXA BAIXA"
            
    if prazo_anos > 10: insights.append("🎯 **Longo Prazo:** Aposentadoria/Sucessão. Volátil no curto prazo.")
    elif prazo_anos < 3: insights.append("🎯 **Curto Prazo:** Reserva/Metas próximas.")
    
    return score_visual, insights

# Tenta importar metricas do core, se falhar usa dummy
try:
    from core.precificacao import compute_duration_metrics
except ImportError:
    def compute_duration_metrics(row, modo): return {}

# --- FUNÇÃO DE DADOS DE MERCADO (SELIC/FOCUS) ---
def get_market_data():
    ipca_ref = 4.0
    selic_ref = 11.25
    
    # Define onde procurar (mesma lógica blindada)
    possible_paths = [
        Path(root_dir) / "data" / "processed",
        Path("data/processed")
    ]
    
    target_path = None
    for p in possible_paths:
        if p.exists():
            target_path = p
            break
            
    if target_path:
        # Focus
        try:
            path_focus = target_path / "focus_ipca.parquet"
            if path_focus.exists():
                df_focus = pd.read_parquet(path_focus)
                ano_alvo = datetime.now().year
                row = df_focus[df_focus['DataReferencia'] == ano_alvo]
                if not row.empty:
                    ipca_ref = row['Mediana'].iloc[0]
        except: pass

        # Selic
        try:
            path_selic = target_path / "selic_meta_sgs.parquet"
            if path_selic.exists():
                df_selic = pd.read_parquet(path_selic)
                # Pega ultima linha
                selic_ref = df_selic.iloc[-1]['valor']
        except: pass

    return ipca_ref, selic_ref

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

# --- RENDERIZAÇÃO DA PÁGINA ---
def render():
    render_sidebar()
    st.markdown("<h1 style='margin-top: 0; font-size: 32px; color: #002B49;'>Simulador de Mercado</h1>", unsafe_allow_html=True)

    if "portfolio" not in st.session_state: st.session_state.portfolio = []

    # CARREGAMENTO DE DADOS BLINDADO
    df, path_used = carregar_dados_blindado()

    if df.empty:
        st.warning("⚠️ Nenhum dado encontrado.")
        st.info("💡 Vá até a **Home** e clique em **'Forçar Atualização'** para baixar os dados mais recentes.")
        # Debug discreto
        with st.expander("Detalhes Técnicos"):
            st.write(f"Raiz do projeto identificada: {root_dir}")
            st.write("Pastas verificadas sem sucesso.")
        return

    # --- CORREÇÃO DE LOGICA DO INDEXADOR ---
    def classificar_indexador(nome):
        nome_upper = str(nome).upper()
        if "IPCA" in nome_upper or "RENDA+" in nome_upper or "EDUCA+" in nome_upper:
            return "IPCA"
        elif "SELIC" in nome_upper:
            return "SELIC"
        else:
            return "PREFIXADO"

    if 'indexador' not in df.columns:
        df['indexador'] = df['tipo_titulo'].apply(classificar_indexador)
    else:
        df['indexador'] = df.apply(lambda row: classificar_indexador(row['tipo_titulo']) if 'RENDA' in str(row['tipo_titulo']).upper() else row['indexador'], axis=1)

    # Tratamento de Datas e Numéricos
    if 'vencimento' in df.columns and 'data_vencimento' not in df.columns:
        df['data_vencimento'] = pd.to_datetime(df['vencimento'])
    elif 'data_vencimento' in df.columns:
        df['data_vencimento'] = pd.to_datetime(df['data_vencimento'])
    
    if "data_base" in df.columns: ref_date = pd.to_datetime(df["data_base"].max())
    else: ref_date = pd.Timestamp.today()

    df["prazo_anos"] = (df["data_vencimento"] - ref_date).dt.days / 365.25
    df["ano_vencimento"] = df["data_vencimento"].dt.year
    
    for c in ["taxa_compra", "pu_compra", "taxa_venda", "pu_venda"]:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    
    df["minimo_compra"] = df["pu_compra"].apply(lambda x: max(30.0, x * 0.01) if pd.notna(x) else 0)

    # Top Cards
    top_ipca = df[df["indexador"] == "IPCA"].nlargest(1, "taxa_compra")
    top_pre = df[df["indexador"] == "PREFIXADO"].nlargest(1, "taxa_compra")
    
    with st.expander("⚙️ Configurar Filtros de Taxa", expanded=False):
        modo = st.radio("Visualizar taxas para:", ["Investir (Compra)", "Resgatar (Venda)"], horizontal=True)
        col_taxa = "taxa_compra" if "Investir" in modo else "taxa_venda"
        col_pu = "pu_compra" if "Investir" in modo else "pu_venda"

    df["rentabilidade_texto"] = df.apply(lambda row: fmt_taxa_humanizada(row, col_taxa), axis=1)
    df["label_completo"] = df["tipo_titulo"] + " | " + df["rentabilidade_texto"]

    # Cards Visuais
    c1, c2, c3 = st.columns(3)
    with c1:
        if not top_ipca.empty:
            r = top_ipca.iloc[0]
            st.markdown(f"""<div class="highlight-card"><div style="font-size: 12px; font-weight: 600; color: #888;">🔥 Maior IPCA+ ({r['ano_vencimento']})</div><div style="font-size: 24px; font-weight: 700; color: #002B49;">{fmt_taxa_humanizada(r, "taxa_compra")}</div></div>""", unsafe_allow_html=True)
    with c2:
        if not top_pre.empty:
            r = top_pre.iloc[0]
            st.markdown(f"""<div class="highlight-card" style="border-left-color: #CFA257;"><div style="font-size: 12px; font-weight: 600; color: #888;">🚀 Maior Prefixado ({r['ano_vencimento']})</div><div style="font-size: 24px; font-weight: 700; color: #002B49;">{fmt_taxa_humanizada(r, "taxa_compra")}</div></div>""", unsafe_allow_html=True)     
    with c3:
        st.markdown(f"""<div class="highlight-card" style="border-left-color: #999;"><div style="font-size: 12px; font-weight: 600; color: #888;">📅 Data Base</div><div style="font-size: 24px; font-weight: 700; color: #333;">{ref_date.strftime("%d/%m/%Y")}</div></div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Tabela
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        st.markdown("### 🔍 Filtros")
        opts = sorted(df["indexador"].astype(str).unique().tolist())
        defs = [x for x in ["IPCA", "PREFIXADO"] if x in opts]
        idx_sel = st.multiselect("Indexador", opts, default=defs)
        
        if "cupom_txt" not in df.columns:
            df["cupom_txt"] = df["tipo_titulo"].apply(lambda x: "COM JUROS" if "Juros" in str(x) else "SEM CUPOM")
        cupom_sel = st.checkbox("Esconder com Juros Semestrais?", value=True)
    
    with col_f2:
        st.markdown("### 📊 Tabela de Taxas")
        view = df.copy()
        if idx_sel: view = view[view["indexador"].isin(idx_sel)]
        if cupom_sel: view = view[view["cupom_txt"] == "SEM CUPOM"]
        view = view.sort_values("data_vencimento")
        
        view["Nome Tabela"] = view["tipo_titulo"]
        dsp = pd.DataFrame()
        dsp["Título"] = view["Nome Tabela"]
        dsp["Vencimento"] = view["data_vencimento"].apply(lambda x: x.strftime("%d/%m/%Y"))
        dsp["Rendimento Anual"] = view["rentabilidade_texto"]
        if col_pu in view.columns: dsp["Preço Unitário"] = view[col_pu].apply(_brl)
        if "Investir" in modo: dsp["Investimento Mínimo"] = view["minimo_compra"].apply(_brl)

        st.dataframe(dsp, hide_index=True, use_container_width=True, height=400)

    # Simulador
    st.markdown("---")
    st.markdown("<h2 style='color: #002B49;'>🧮 Simulador de Rentabilidade</h2>", unsafe_allow_html=True)
    
    auto_ipca, auto_selic = get_market_data()

    c_sim1, c_sim2, c_sim3, c_sim4 = st.columns(4)
    dinheiro = c_sim1.number_input("Quanto quer investir?", value=1000.0, step=100.0, format="%.2f")
    titulo_label = c_sim2.selectbox("Escolha o Título", view["label_completo"].unique())
    ipca_proj = c_sim3.number_input("IPCA Estimado (%)", value=auto_ipca, step=0.1)
    selic_proj = c_sim4.number_input("Selic Média (%)", value=auto_selic, step=0.25)
    
    with st.expander("🔧 Ajustes Finos (Impostos e Taxas)", expanded=False):
        sc1, sc2, sc3 = st.columns(3)
        calc_ir = sc2.checkbox("Descontar IR?", value=True)
        calc_b3 = sc3.checkbox("Descontar Taxa B3?", value=True)

    if titulo_label:
        row = view[view["label_completo"] == titulo_label].iloc[0]
        if col_taxa in row:
            taxa_titulo = float(row.get(col_taxa, 0))
            dias_sim = (row["data_vencimento"] - pd.Timestamp.today()).days
            anos_sim = dias_sim / 365.25
            
            if anos_sim > 0:
                st.markdown("#### 🗓️ Cronograma do Investimento")
                t1, t2, t3 = st.columns(3)
                hoje_str = pd.Timestamp.today().strftime("%d/%m/%Y")
                venc_str = row["data_vencimento"].strftime("%d/%m/%Y")
                
                with t1: st.markdown(f"<div class='timeline-card'><div>INÍCIO (HOJE)</div><div style='font-size:18px;font-weight:bold;'>{hoje_str}</div></div>", unsafe_allow_html=True)
                with t2: st.markdown(f"<div class='timeline-card' style='background:#FFF3E0;color:#E65100;border-color:#FFE0B2;'><div>TEMPO</div><div style='font-size:18px;font-weight:bold;'>{dias_sim} Dias</div><div>({anos_sim:.1f} anos)</div></div>", unsafe_allow_html=True)
                with t3: st.markdown(f"<div class='timeline-card' style='background:#E8F5E9;color:#1B5E20;border-color:#C8E6C9;'><div>VENCIMENTO</div><div style='font-size:18px;font-weight:bold;'>{venc_str}</div></div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)

                # CÁLCULOS
                idx = str(row["indexador"]).upper()
                if "IPCA" in idx: 
                    taxa_bruta = ((1 + taxa_titulo/100) * (1 + ipca_proj/100)) - 1
                elif "PREFIXADO" in idx: 
                    taxa_bruta = taxa_titulo/100
                elif "SELIC" in idx: 
                    taxa_bruta = (selic_proj + taxa_titulo)/100
                else: 
                    taxa_bruta = taxa_titulo/100

                bruto = dinheiro * ((1 + taxa_bruta) ** anos_sim)
                custo_b3 = bruto * (0.0020 * anos_sim) if calc_b3 else 0.0
                aliq_ir = calcular_aliquota_ir(dias_sim)
                lucro_bruto = bruto - dinheiro
                base_ir = max(0, lucro_bruto - custo_b3)
                ir_val = base_ir * (aliq_ir / 100.0) if calc_ir else 0.0
                liquido = bruto - custo_b3 - ir_val
                
                poupanca_est = dinheiro * ((1 + 0.07) ** anos_sim)
                cdi_bruto = dinheiro * ((1 + selic_proj/100) ** anos_sim)
                cdi_liq = cdi_bruto - (cdi_bruto - dinheiro)*(aliq_ir/100) if calc_ir else cdi_bruto

                st.markdown("#### 💰 Projeção Financeira")
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("Valor Líquido Final", _brl(liquido), delta=f"Lucro: {_brl(liquido-dinheiro)}")
                r2.metric("vs Poupança", _brl(poupanca_est), delta=f"{_brl(liquido - poupanca_est)}", delta_color="normal")
                r3.metric("vs CDI (100%)", _brl(cdi_liq), delta=f"{_brl(liquido - cdi_liq)}", delta_color="normal")
                
                rent_aa = ((1 + (liquido - dinheiro)/dinheiro)**(1/anos_sim) - 1) * 100
                r4.metric("Rentabilidade Líquida a.a.", f"{rent_aa:.2f}%")

                st.markdown("---")
                score, insights = analisar_oportunidade(row, ipca_proj)
                cb1, cb2 = st.columns([1, 2])
                with cb1: st.markdown(f"### 🤖 Raio-X UAI\n<div style='font-size: 20px; font-weight: bold; color: #002B49;'>{score}</div>", unsafe_allow_html=True)
                with cb2: 
                    for ins in insights: st.info(ins, icon="💡")

                st.markdown("<br><div class='primary-btn'>", unsafe_allow_html=True)
                if st.button("💾 Adicionar Título à Carteira", use_container_width=True):
                    qtd_calc = dinheiro / float(row["pu_compra"])
                    item = {
                        "id": row["Nome Tabela"], "indexador": row["indexador"],
                        "vencimento": row["data_vencimento"], "taxa_compra": float(row["taxa_compra"]),
                        "pu_compra": float(row["pu_compra"]), "qtd": qtd_calc,
                        "metrics": compute_duration_metrics(row, modo="Compra")
                    }
                    st.session_state.portfolio.append(item)
                    st.success(f"✅ **{row['Nome Tabela']}** adicionado!")
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
