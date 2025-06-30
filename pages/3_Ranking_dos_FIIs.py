import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("🏅 Ranking: Top 10 FIIs por Indicador")

@st.cache_data
def carregar_dados():
    DB_PATH = Path(__file__).parents[1] / "data" / "fiis.db"
    conn = sqlite3.connect(DB_PATH)
    fiis = pd.read_sql("""
        SELECT f.id, f.ticker, f.nome, s.nome as setor
        FROM fiis f
        JOIN setor s ON f.setor_id = s.id
    """, conn)
    indicadores = pd.read_sql("""
        SELECT fi.fii_id, f.ticker AS ticker_fii, i.nome AS indicador, fi.valor, fi.data_referencia
        FROM fiis_indicadores fi
        JOIN indicadores i ON i.id = fi.indicador_id
        JOIN fiis f ON f.id = fi.fii_id
        WHERE fi.valor IS NOT NULL
    """, conn)
    conn.close()
    return fiis, indicadores

fiis, indicadores = carregar_dados()

st.sidebar.subheader("🔍 Filtro")
setores = sorted(fiis['setor'].unique())
filtro_setor = st.sidebar.multiselect("Setores:", setores, default=setores)
fiis_filtrados = fiis[fiis['setor'].isin(filtro_setor)]
ids_filtrados = fiis_filtrados['id'].tolist()

df_validos = indicadores[indicadores['fii_id'].isin(ids_filtrados)]

# Remover indicadores de vacância/ocupação
indicadores_ocultar = [
    "Vacância Percentual", "Vacância m²", "Ocupação Percentual", "Ocupação m²"
]
df_validos = df_validos[~df_validos['indicador'].isin(indicadores_ocultar)]

# Mesclar indicadores de Dividend Yield
df_validos['indicador'] = df_validos['indicador'].replace({
    "Dividend Yield 1M": "Dividend Yield",
    "Dividend Yield 3M": "Dividend Yield",
    "Dividend Yield 6M": "Dividend Yield",
    "Dividend Yield 12M": "Dividend Yield"
})

# Lista de indicadores disponíveis
indicadores_disponiveis = sorted(df_validos['indicador'].unique())

col1, col2 = st.columns(2)
metade = len(indicadores_disponiveis) // 2
col1_inds = indicadores_disponiveis[:metade]
col2_inds = indicadores_disponiveis[metade:]

def plot_top10(indicador_nome, col):
    top10 = (
        df_validos[df_validos['indicador'] == indicador_nome]
        .sort_values('valor', ascending=False)
        .head(10)
    )
    fig = go.Figure(go.Bar(
        x=top10['valor'],
        y=top10['ticker_fii'],
        orientation='h',
        marker_color='royalblue'
    ))
    fig.update_layout(title=indicador_nome, xaxis_title="Valor", yaxis_title="FII", height=400)
    col.plotly_chart(fig, use_container_width=True)

with col1:
    for indicador in col1_inds:
        plot_top10(indicador, col1)

with col2:
    for indicador in col2_inds:
        plot_top10(indicador, col2)

# Gráfico agrupado: Ocupação vs Vacância
st.subheader("📊 Comparativo de Ocupação e Vacância Percentual")
st.markdown("Quanto **mais próxima de 100% a ocupação** e **mais próxima de 0% a vacância**, melhor é o desempenho do fundo.")

# Filtra apenas fundos com os dois indicadores
df_comparativo = indicadores[
    (indicadores['fii_id'].isin(ids_filtrados)) &
    (indicadores['indicador'].isin(['Vacância Percentual', 'Ocupação Percentual']))
]

# Converte a data
df_comparativo['data_referencia'] = pd.to_datetime(df_comparativo['data_referencia'], errors='coerce')
ultima_data = df_comparativo['data_referencia'].max()
df_comparativo = df_comparativo[df_comparativo['data_referencia'] == ultima_data]

# Pivot para ficar um FII por linha com os dois valores
df_pivot = df_comparativo.pivot_table(index="ticker_fii", columns="indicador", values="valor", aggfunc="last")
df_pivot = df_pivot.dropna().sort_values("Vacância Percentual", ascending=True).head(20)  # Top 20 com menor vacância

fig = go.Figure()

fig.add_trace(go.Bar(
    x=df_pivot.index,
    y=df_pivot["Ocupação Percentual"],
    name="Ocupação (%)",
    marker_color='seagreen'
))

fig.add_trace(go.Bar(
    x=df_pivot.index,
    y=df_pivot["Vacância Percentual"],
    name="Vacância (%)",
    marker_color='indianred'
))

fig.update_layout(
    barmode='group',
    xaxis_title="FII",
    yaxis_title="Percentual",
    title="Top 20 FIIs com Melhor Ocupação e Menor Vacância",
    height=600
)

st.plotly_chart(fig, use_container_width=True)
