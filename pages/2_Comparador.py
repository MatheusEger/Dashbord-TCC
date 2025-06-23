import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

st.set_page_config(layout="wide")
st.title("📊 Comparador de Fundos Imobiliários")

st.markdown("### 📌 Comparação")

def carregar_dados():
    DB_PATH = Path(__file__).parents[1] / "data" / "fiis.db"
    conn = sqlite3.connect(DB_PATH)

    fiis = pd.read_sql("""
        SELECT f.id, f.ticker, f.nome, s.nome AS setor
        FROM fiis f
        JOIN setor s ON f.setor_id = s.id
    """, conn)

    indicadores = pd.read_sql("""
        SELECT fi.fii_id, i.nome AS indicador, fi.valor
        FROM fiis_indicadores fi
        JOIN indicadores i ON fi.indicador_id = i.id
    """, conn)

    conn.close()
    return fiis, indicadores

fiis, indicadores = carregar_dados()
fiis = fiis.sort_values("ticker")

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
    def buscar_indicador(nome):
        linha = indicadores_df[indicadores_df['indicador'] == nome]
        if not linha.empty:
            return f"{float(linha['valor'].values[0]):,.2f}"
        return "N/A"

    st.markdown(f"### {dados['ticker']} - {dados['nome']}")
    st.markdown(f"**Setor:** {dados['setor']}")
    st.markdown(f"**Patrimônio Líquido:** R$ {buscar_indicador('Patrimônio Líquido')}")
    st.markdown(f"**Quantidade de Cotas:** {buscar_indicador('Quantidade de Cotas')}")
    st.markdown(f"**Qtd de Ativos:** {buscar_indicador('Qtd de Ativos')}")

    st.markdown("---")
    st.markdown(f"**P/VP:** {buscar_indicador('P/VP')}")
    st.markdown(f"**Dividend Yield 12M:** {buscar_indicador('Dividend Yield 12M')}%")
    st.markdown(f"**Último Dividendo:** R$ {buscar_indicador('Último Dividendo')}")
    st.markdown(f"**Rentabilidade Acumulada:** {buscar_indicador('Rentabilidade Acumulada')}%")
    
col1, col2 = st.columns(2)

with col1:
    exibir_info(col1, dados1, ind1)

with col2:
    exibir_info(col2, dados2, ind2)
