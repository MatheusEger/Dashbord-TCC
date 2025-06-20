import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Dashboard FIIs", layout="wide")

# Banco de dados
DB_PATH = Path(__file__).resolve().parent / "data" / "fiis.db"

@st.cache_data
def carregar_dados():
    conn = sqlite3.connect(DB_PATH)
    fiis = pd.read_sql("""
        SELECT f.id, f.ticker, f.nome, s.nome as setor, f.created_at
        FROM fiis f
        JOIN setor s ON f.setor_id = s.id
    """, conn)

    indicadores = pd.read_sql("""
        SELECT fi.fii_id, f.ticker AS ticker_fii, i.nome AS indicador, fi.valor, fi.data_referencia
        FROM fiis_indicadores fi
        JOIN indicadores i ON i.id = fi.indicador_id
        JOIN fiis f ON f.id = fi.fii_id
    """, conn)
    conn.close()
    return fiis, indicadores

fiis, indicadores = carregar_dados()

# Filtros
st.sidebar.title("Filtros")
setores = sorted(fiis['setor'].unique())
setores_selecionados = st.sidebar.multiselect("Setores", setores, default=setores)
fiis_filtrados = fiis[fiis['setor'].isin(setores_selecionados)]

indicadores = indicadores[indicadores['fii_id'].isin(fiis_filtrados['id'])]
indicadores["data_referencia"] = pd.to_datetime(indicadores["data_referencia"]).dt.date
data_max = indicadores["data_referencia"].max()
indicadores_atuais = indicadores[indicadores["data_referencia"] == data_max]

# Métricas principais
st.title("Dashboard FIIs - Indicadores Atuais")
col1, col2, col3 = st.columns(3)

vac = indicadores_atuais[indicadores_atuais['indicador'] == "Vacância Percentual"]['valor'].mean()
ocu = indicadores_atuais[indicadores_atuais['indicador'] == "Ocupação Percentual"]['valor'].mean()
dy = indicadores_atuais[indicadores_atuais['indicador'] == "Dividend Yield"]['valor'].mean()
pvp = indicadores_atuais[indicadores_atuais['indicador'] == "P/VP"]['valor'].mean()

col1.metric("Vacância Média", f"{vac:.2f}%")
col2.metric("Ocupacão Média", f"{ocu:.2f}%")
col3.metric("Dividend Yield", f"{dy:.2f}%")

# Gráfico de Vacância
st.subheader("Vacância Percentual por FII")
df_vac = indicadores_atuais[indicadores_atuais['indicador'] == "Vacância Percentual"]
fig_vac = px.bar(
    df_vac,
    x="valor",
    y="ticker_fii",
    orientation="h",
    text="valor",
    title="Vacância por FII",
    labels={"valor": "%", "ticker_fii": "FII"}
)
fig_vac.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig_vac, use_container_width=True)

# Evolução temporal de indicador
st.subheader("Evolução de Indicador")
indicador_sel = st.selectbox("Escolha um indicador", indicadores['indicador'].unique())
df_ind = indicadores[(indicadores['indicador'] == indicador_sel)]
fig_ind = px.line(
    df_ind,
    x="data_referencia",
    y="valor",
    color="ticker_fii",
    title=f"Evolução de {indicador_sel}"
)
st.plotly_chart(fig_ind, use_container_width=True)
