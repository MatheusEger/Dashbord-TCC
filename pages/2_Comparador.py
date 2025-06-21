import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

st.set_page_config(layout="wide")
st.title("📊 Comparador de Fundos Imobiliários")

# Função para carregar dados do banco
def carregar_dados():
    DB_PATH = Path(__file__).parents[1] / "data" / "fiis.db"
    conn = sqlite3.connect(DB_PATH)

    # Junta informações de fundo + setor
    fiis = pd.read_sql("""
       SELECT f.id, f.ticker, f.nome, s.nome AS setor, f.qtde_ativos
        FROM fiis f
J       OIN setor s ON f.setor_id = s.id      
    """, conn)
    

    # Indicadores
    indicadores = pd.read_sql("""
        SELECT i.fii_id, i.indicador, i.valor
        FROM fiis_indicadores i
    """, conn)

    conn.close()
    return fiis, indicadores

fiis, indicadores = carregar_dados()
fiis = fiis.sort_values("ticker")

# Interface lado a lado
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔹 Fundo 1")
    fundo1 = st.selectbox("Selecione o primeiro fundo:", fiis['ticker'])
    dados1 = fiis[fiis['ticker'] == fundo1].iloc[0]
    ind1 = indicadores[indicadores['fii_id'] == dados1['id']]

with col2:
    st.subheader("🔸 Fundo 2")
    fundo2 = st.selectbox("Selecione o segundo fundo:", fiis['ticker'], index=1)
    dados2 = fiis[fiis['ticker'] == fundo2].iloc[0]
    ind2 = indicadores[indicadores['fii_id'] == dados2['id']]

# Função para exibir bloco de informações do fundo
def exibir_info(col, dados, indicadores_df):
    st.markdown(f"### {dados['ticker']} - {dados['nome']}")
    st.markdown(f"**Setor:** {dados['setor']}")
    st.markdown(f"**Patrimônio Líquido:** R$ {dados['patrimonio_liquido']:,.2f}")
    st.markdown(f"**Quantidade de Cotas:** {dados['qtd_cotas']}")
    st.markdown(f"**Qtd de Ativos:** {dados['qtde_ativos']}")

    def buscar_indicador(nome):
        linha = indicadores_df[indicadores_df['indicador'] == nome]
        if not linha.empty:
            return f"{float(linha['valor'].values[0]):,.2f}"
        return "N/A"

    st.markdown("---")
    st.markdown(f"**P/VP:** {buscar_indicador('P/VP')}")
    st.markdown(f"**Dividend Yield 12M:** {buscar_indicador('Dividend Yield 12M')}%")
    st.markdown(f"**Último Dividendo:** R$ {buscar_indicador('Último Dividendo')}")
    st.markdown(f"**Rentabilidade Acumulada:** {buscar_indicador('Rentabilidade Acumulada')}%")

# Exibir lado a lado
st.markdown("### 📌 Comparação")
col1, col2 = st.columns(2)

with col1:
    exibir_info(col1, dados1, ind1)

with col2:
    exibir_info(col2, dados2, ind2)
