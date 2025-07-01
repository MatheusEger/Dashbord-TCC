import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("🏅 Ranking: Top 10 FIIs por Métrica e por Tipo/Setor")
DB_PATH = Path(__file__).parents[1] / "data" / "fiis.db"

@st.cache_data
def carregar_dados():
    conn = sqlite3.connect(DB_PATH)
    fiis = pd.read_sql(
        """
        SELECT f.id, f.ticker, f.nome, s.nome AS setor, t.nome AS tipo
        FROM fiis f
        JOIN setor s ON f.setor_id = s.id
        JOIN tipo_fii t ON f.tipo_id = t.id
        WHERE f.ativo = 1
        """, conn)
    indicadores = pd.read_sql(
        """
        SELECT fi.fii_id, f.ticker AS ticker_fii, i.nome AS indicador, fi.valor, fi.data_referencia
        FROM fiis_indicadores fi
        JOIN indicadores i ON i.id = fi.indicador_id
        JOIN fiis f ON f.id = fi.fii_id
        WHERE fi.valor IS NOT NULL
        """, conn)
    conn.close()
    return fiis, indicadores

fiis, indicadores = carregar_dados()

# ── Sidebar de filtros ───────────────────────────────────────────────────────
st.sidebar.subheader("🔍 Filtros")

tipos = sorted(fiis['tipo'].unique())
filtro_tipo = st.sidebar.multiselect(
    "Tipos:", tipos, default=[], key="filtro_tipo"
)

# Setores dinâmicos conforme Tipo selecionado
if filtro_tipo:
    setores_opcoes = sorted(fiis[fiis['tipo'].isin(filtro_tipo)]['setor'].unique())
else:
    setores_opcoes = sorted(fiis['setor'].unique())

filtro_setor = st.sidebar.multiselect(
    "Setores:", setores_opcoes, default=[], key="filtro_setor"
)

# Filtro de Métricas (sem indicadores de dividendos)
metricas_disponiveis = sorted(indicadores['indicador'].unique())
metricas_disponiveis = [m for m in metricas_disponiveis if 'Dividend' not in m]
metricas_padrao = [m for m in ["P/VP", "Valor Patrimonial por Cota", "Preço Atual"] if m in metricas_disponiveis]
filtro_metrica = st.sidebar.multiselect(
    "Métricas:", metricas_disponiveis, default=metricas_padrao, key="filtro_metrica"
)

# ── Filtra dados conforme seleção ────────────────────────────────────────────
fiis_filtrados = fiis.copy()
if filtro_tipo:
    fiis_filtrados = fiis_filtrados[fiis_filtrados['tipo'].isin(filtro_tipo)]
if filtro_setor:
    fiis_filtrados = fiis_filtrados[fiis_filtrados['setor'].isin(filtro_setor)]
ids_filtrados = fiis_filtrados['id'].tolist()

df_validos = indicadores[indicadores['fii_id'].isin(ids_filtrados)].copy()
irrelevantes = ["Vacância Percentual", "Vacância m²", "Ocupação Percentual", "Ocupação m²"]
df_validos = df_validos[~df_validos['indicador'].isin(irrelevantes)]
df_validos = df_validos[~df_validos['indicador'].str.contains('Dividend', case=False, na=False)]

df_validos['indicador'] = df_validos['indicador'].replace({
    "Valor Patrimonial por Cota": "VPA",
    "Preço Atual": "Preço Atual",
    "P/VP": "P/VP"
})
selected_mets = filtro_metrica or metricas_disponiveis

# ── Função de plotagem ───────────────────────────────────────────────────────
def plot_top10(metrica, df_source, container, key):
    df_i = df_source[df_source['indicador'] == metrica].nlargest(10, 'valor')
    if df_i.empty:
        container.info(f"Sem dados para {metrica}.")
        return
    fig = go.Figure(go.Bar(
        x=df_i['valor'],
        y=df_i['ticker_fii'],
        orientation='h',
        hovertemplate="<b>%{y}</b><br>Valor (R$): %{x:,.2f}<extra></extra>"
    ))
    fig.update_layout(
        title={'text': metrica, 'x': 0.5},
        xaxis_title="Valor (R$)",
        yaxis_title="Código do FII",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        yaxis=dict(autorange='reversed')
    )
    container.plotly_chart(fig, use_container_width=True, key=key)

# ── Ranking por Métrica ───────────────────────────────────────────────────────
st.subheader("📈 Top 10 por Métrica")
cols_mets = st.columns(2)
for idx, metrica in enumerate(selected_mets):
    plot_top10(metrica, df_validos, cols_mets[idx % 2], key=f"met-{metrica}-{idx}")

# ── Ranking por Tipo e Setor ─────────────────────────────────────────────────
st.subheader("🏆 Top 10 FIIs por Tipo e Setor")
for tipo in (filtro_tipo or tipos):
    st.markdown(f"### Tipo: {tipo}")
    setores_disp = sorted(fiis_filtrados[fiis_filtrados['tipo'] == tipo]['setor'].unique())
    for setor in (filtro_setor or setores_disp):
        st.markdown(f"#### Setor: {setor}")
        ids_grp = fiis_filtrados[(fiis_filtrados['tipo'] == tipo) & (fiis_filtrados['setor'] == setor)]['id']
        df_grp = df_validos[df_validos['fii_id'].isin(ids_grp)]
        if df_grp.empty:
            st.write("Sem dados para este grupo.")
            continue
        cols_group = st.columns(2)
        for idx, metrica in enumerate(selected_mets):
            plot_top10(metrica, df_grp, cols_group[idx % 2], key=f"grp-{tipo}-{setor}-{metrica}")
            