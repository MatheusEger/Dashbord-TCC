import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("🏅 Ranking: Top 10 FIIs por Indicador")
DB_PATH = Path(__file__).parents[1] / "data" / "fiis.db"

@st.cache_data
def carregar_dados():
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

# ───── Sidebar de filtros ──────────────────────────────────────────────────────
st.sidebar.subheader("🔍 Filtros")

# 1) Filtro de Setor
setores = sorted(fiis['setor'].unique())
filtro_setor = st.sidebar.multiselect("Setores:", setores, default=setores)

# Narrow down pelos setores
fiis_filtrados = fiis[fiis['setor'].isin(filtro_setor)]
ids_filtrados  = fiis_filtrados['id'].tolist()

# 2) Prepara DataFrame de indicadores válidos
df_validos = indicadores[indicadores['fii_id'].isin(ids_filtrados)].copy()

# Exclui vacância/ocupação
indicadores_ocultar = [
    "Vacância Percentual", "Vacância m²",
    "Ocupação Percentual", "Ocupação m²"
]
df_validos = df_validos[~df_validos['indicador'].isin(indicadores_ocultar)]

# Unifica todas as janelas de Dividend Yield em um só
df_validos['indicador'] = df_validos['indicador'].replace({
    "Dividend Yield 1M": "Dividend Yield",
    "Dividend Yield 3M": "Dividend Yield",
    "Dividend Yield 6M": "Dividend Yield",
    "Dividend Yield 12M": "Dividend Yield"
})

# 3) Filtro de indicadores
indicadores_disponiveis = sorted(df_validos['indicador'].unique())
indicadores_padrao     = ["P/VP", "Patrimônio Líquido", "Dividend Yield"]
filtro_inds = st.sidebar.multiselect(
    "Indicadores:", 
    indicadores_disponiveis,
    default=[i for i in indicadores_padrao if i in indicadores_disponiveis]
)

# Aplica filtro de indicadores
df_validos = df_validos[df_validos['indicador'].isin(filtro_inds)]

# ───── Função de plot Top10 ────────────────────────────────────────────────────
def plot_top10(indicador_nome, container):
    df_i = df_validos[df_validos['indicador'] == indicador_nome].copy()
    df_i = df_i.sort_values("valor", ascending=False)
    top10 = df_i.head(10)

    fig = go.Figure(go.Bar(
        x=top10['valor'],
        y=top10['ticker_fii'],
        orientation='h'
    ))
    fig.update_layout(
        title={'text': indicador_nome, 'x': 0.5, 'xanchor': 'center'},
        xaxis_title="Valor",
        yaxis_title="FII",
        paper_bgcolor='rgba(0,0,0,0)',         
        plot_bgcolor='rgba(0,0,0,0)',         
        font=dict(family='Arial', size=12),
        margin=dict(l=80, r=40, t=50, b=40),
        height=350,
        yaxis=dict(autorange='reversed')
    )
    container.plotly_chart(fig, use_container_width=True)

# ───── Desenha os gráficos selecionados ────────────────────────────────────────
if not filtro_inds:
    st.warning("Selecione ao menos 1 indicador na sidebar para exibir os gráficos.")
else:
    col1, col2 = st.columns(2)
    half = (len(filtro_inds) + 1) // 2
    col1_inds = filtro_inds[:half]
    col2_inds = filtro_inds[half:]

    with col1:
        for ind in col1_inds:
            plot_top10(ind, col1)
    with col2:
        for ind in col2_inds:
            plot_top10(ind, col2)

st.subheader("📊 Comparativo de Ocupação e Vacância Física")

with sqlite3.connect(DB_PATH) as conn:
    df_im = pd.read_sql(
        f"""
        SELECT f.id AS fii_id,
               f.ticker,
               im.area_m2,
               im.tx_ocupacao
        FROM fiis_imoveis im
        JOIN fiis f ON f.id = im.fii_id
        WHERE im.fii_id IN ({','.join('?' for _ in ids_filtrados)})
        """,
        conn,
        params=ids_filtrados
    )

if df_im.empty:
    st.info("Não há dados de imóveis para calcular ocupação/vacância.")
else:
    # 2) Calcula ocupação ponderada e vacância para cada FII
    grp = df_im.groupby(['fii_id', 'ticker']).apply(
        lambda g: pd.Series({
            'ocupacao': (g.area_m2 * g.tx_ocupacao).sum() / g.area_m2.sum(),
            'vacancia': 100 - (g.area_m2 * g.tx_ocupacao).sum() / g.area_m2.sum()
        })
    ).reset_index()

    # 3) Ordena pelo menor valor de vacância e pega Top 20
    top20 = grp.sort_values('vacancia', ascending=True).head(20)

    # 4) Plota
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top20['ticker'],
        y=top20['ocupacao'],
        name="Ocupação (%)"
    ))
    fig.add_trace(go.Bar(
        x=top20['ticker'],
        y=top20['vacancia'],
        name="Vacância (%)",
        marker_color='indianred'
    ))
    fig.update_layout(
        barmode='group',
        title={'text': "Top 20 FIIs por Melhor Ocupação e Menor Vacância", 'x':0.5},
        xaxis_title="FII",
        yaxis_title="Percentual",
        font=dict(family='Arial', size=12),
        margin=dict(l=80, r=40, t=60, b=50),
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
