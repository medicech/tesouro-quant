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
df_titulos, _ = carregar_arquivo("tesouro_catalogo_2026-01-28.parquet") # Tenta data específica
if df_titulos.empty:
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
    
    # Cria rótulo amigável
    df_titulos['label_filtro'] = df_titulos['tipo_titulo'] + " (" + df_titulos['vencimento'].dt.year.astype(str) + ")"

# --- HEADER ---
c1, c2 = st.columns([1, 5])
with c1:
    if st.button("⬅ Voltar"): st.switch_page("streamlit_app.py")
with c2:
    st.title("Macro Intelligence")
    st.caption("Análise Estrutural da Curva de Juros e Expectativas.")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📉 Curva de Juros (Nominal)", "🎈 Breakeven de Inflação", "🔮 Boletim Focus"])

# --- TAB 1: CURVA DE JUROS (CORRIGIDA COM INPUTS) ---
with tab1:
    if not df_titulos.empty:
        
        # --- ÁREA DE PARAMETROS ---
        with st.container(border=True):
            st.markdown("#### ⚙️ Parâmetros de Simulação")
            st.caption("Para comparar 'bananas com bananas', defina suas premissas para converter as taxas reais em nominais.")
            
            cp1, cp2, cp3 = st.columns(3)
            # Input do Usuário
            user_ipca = cp1.number_input("IPCA Projetado (% a.a.)", value=4.0, step=0.1, help="Usado para projetar o retorno nominal dos títulos IPCA+.")
            user_selic = cp2.number_input("Selic Média (% a.a.)", value=10.0, step=0.25, help="Usado para projetar o retorno dos títulos Selic.")
            
            # Filtros Visuais
            all_indexes = df_titulos['indexador'].unique()
            sel_indexes = cp3.multiselect("Filtrar Indexadores", all_indexes, default=['PREFIXADO', 'IPCA'])

        # --- LÓGICA DE CÁLCULO NOMINAL ---
        # Filtra indexadores primeiro
        df_chart = df_titulos[df_titulos['indexador'].isin(sel_indexes)].copy()
        
        # Filtra títulos padrão (tira Renda+ para limpar o gráfico, a menos que selecionado)
        df_chart = df_chart[~df_chart['tipo_titulo'].str.contains("Renda+|Educa+", regex=True)]

        def calcular_nominal(row):
            taxa_fixa = float(row['taxa_compra'])
            idx = row['indexador']
            
            if idx == 'PREFIXADO':
                return taxa_fixa, f"Prefixado: {taxa_fixa:.2f}%"
            
            elif idx == 'IPCA':
                # Fórmula de Fisher: (1 + Real) * (1 + Inflação) - 1
                nominal = ((1 + taxa_fixa/100) * (1 + user_ipca/100) - 1) * 100
                return nominal, f"Real: {taxa_fixa:.2f}% + IPCA: {user_ipca:.2f}%"
            
            elif idx == 'SELIC':
                # Selic + Spread
                nominal = user_selic + taxa_fixa
                return nominal, f"Selic: {user_selic:.2f}% + Spread: {taxa_fixa:.2f}%"
            
            return taxa_fixa, str(taxa_fixa)

        # Aplica o cálculo linha a linha
        if not df_chart.empty:
            df_chart[['taxa_projetada', 'detalhe_taxa']] = df_chart.apply(
                lambda x: pd.Series(calcular_nominal(x)), axis=1
            )

            # GRÁFICO
            fig = px.line(
                df_chart.sort_values('prazo_anos'), 
                x="vencimento", 
                y="taxa_projetada", # Agora usa a taxa calculada!
                color="indexador",
                markers=True,
                title=f"Curva de Juros Nominal (Considerando IPCA {user_ipca}% e Selic {user_selic}%)",
                labels={"taxa_projetada": "Rentabilidade Nominal Projetada (% a.a.)", "vencimento": "Vencimento"},
                color_discrete_map={"PREFIXADO": "#D32F2F", "IPCA": "#1976D2", "SELIC": "#388E3C"},
                custom_data=['tipo_titulo', 'detalhe_taxa'] # Dados para o tooltip
            )
            
            # Tooltip Personalizado
            fig.update_traces(
                hovertemplate="<b>%{customdata[0]}</b><br>Vencimento: %{x|%d/%m/%Y}<br>Rentabilidade Projetada: %{y:.2f}%<br><i>(%{customdata[1]})</i>"
            )
            
            fig.update_layout(height=500, hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Nenhum dado disponível para os filtros selecionados.")
            
    else:
        st.error("Sem dados de títulos.")

# --- TAB 2: BREAKEVEN ---
with tab2:
    st.markdown("### Inflação Implícita")
    st.info("💡 Diferença de taxa entre Prefixados e IPCA+ de mesmo vencimento.")
    
    if not df_titulos.empty:
        try:
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
        except:
            st.warning("Dados insuficientes para cálculo de Breakeven.")

# --- TAB 3: FOCUS ---
with tab3:
    st.markdown("### Expectativas de Mercado (Banco Central)")
    
    if not df_focus.empty:
        data_rel = pd.to_datetime(df_focus['Data'].max()).strftime('%d/%m/%Y')
        
        st.markdown(f"""
        <div style="background-color: white; padding: 15px; border-radius: 8px; border-left: 5px solid #002B49; margin-bottom: 20px;">
            <span style="font-size: 12px; font-weight: bold; color: #666; text-transform: uppercase;">Relatório Vigente</span><br>
            <span style="font-size: 28px; font-weight: 800; color: #002B49;">{data_rel}</span>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            df_view = df_focus[df_focus['Indicador'].isin(['IPCA', 'Selic'])].copy()
            df_view = df_view[df_view['DataReferencia'].isin([2026, 2027, 2028, 2029])]
            
            pivoted = df_view.pivot_table(index='Indicador', columns='DataReferencia', values='Mediana', aggfunc='first')
            
            st.dataframe(pivoted.style.format("{:.2f}%"), use_container_width=True)
            st.caption("Fonte: API Olinda/Bacen.")
        except Exception as e:
            st.error(f"Erro na tabela: {e}")
    else:
        st.warning("Dados do Focus não encontrados.")
