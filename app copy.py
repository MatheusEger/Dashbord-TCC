import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from dateutil.relativedelta import relativedelta

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard de FIIs", layout="wide")

# --- DB Path ---
DB_PATH = Path(__file__).resolve().parent / "data" / "fiis.db"

# --- Carregamento de dados ---
conn = sqlite3.connect(DB_PATH)
sql_meta = """
SELECT f.id, f.ticker, f.nome, s.nome AS setor, t.nome AS tipo
FROM fiis f
LEFT JOIN setor s ON f.setor_id = s.id
LEFT JOIN tipo_fii t ON f.tipo_id = t.id
WHERE f.ativo = 1
"""
df_meta = pd.read_sql_query(sql_meta, conn)
cotacoes = pd.read_sql_query(
    "SELECT fii_id, data, preco_fechamento FROM cotacoes",
    conn,
    parse_dates=['data']
)
inds = pd.read_sql_query(
    """
    SELECT fi.fii_id, i.nome AS indicador, fi.valor, fi.data_referencia
    FROM fiis_indicadores fi
    JOIN indicadores i ON i.id = fi.indicador_id
    """,
    conn,
    parse_dates=['data_referencia']
)
conn.close()


# --- Preparação do DataFrame ---
df = df_meta.copy()
# Preço Atual
ultimo = (
    cotacoes.sort_values(['fii_id', 'data'])
    .groupby('fii_id')['preco_fechamento']
    .last()
    .rename('preco_atual')
)
df = df.merge(ultimo, left_on='id', right_index=True, how='left')
df['preco_atual'] = pd.to_numeric(df['preco_atual'], errors='coerce')

# --- PL e Qt ---
# Cria tabela pivot com indicadores
pivot = inds.pivot_table(
    index='fii_id',
    columns='indicador',
    values='valor',
    aggfunc='max'
)
# Renomeia colunas para uso interno
pivot = pivot.rename(
    columns={'Patrimônio Líquido': 'pl', 'Quantidade de Cotas': 'qt'}
)
# Garante que são numéricos
pivot[['pl', 'qt']] = pivot[['pl', 'qt']].apply(pd.to_numeric, errors='coerce')
# Mescla no DataFrame principal
df = df.merge(pivot[['pl', 'qt']], left_on='id', right_index=True, how='left')
# Calcula VPA e P/VP
df['vpa_calc'] = df['pl'] / df['qt']
df['pvp_calc'] = df['preco_atual'] / df['vpa_calc']

# --- Cálculo de DY 12M ---
divs = inds[inds['indicador'] == 'Dividendos'].copy()
divs['periodo'] = divs['data_referencia'].dt.to_period('M')
ult = divs['periodo'].max()
ini = ult - 11
d12 = divs[divs['periodo'].between(ini, ult)]
soma = d12.groupby('fii_id')['valor'].sum().rename('div12m')
df = df.merge(soma, left_on='id', right_index=True, how='left')
df['dy_calc'] = (df['div12m'] / df['preco_atual']) * 100

# --- Filtros na sidebar ---
st.sidebar.header("🔎 Filtros")
modo_ini = st.sidebar.checkbox("🔰 Modo Iniciante", value=True)
query = st.sidebar.text_input("Buscar por ticker ou nome", placeholder="Ex.: FLRP11...")
setores = ['Todos'] + sorted(df['setor'].dropna().unique())
tipos = ['Todos'] + sorted(df['tipo'].dropna().unique())
sel_setor = st.sidebar.selectbox("Setor", setores)
sel_tipo = st.sidebar.selectbox("Tipo", tipos)
pmin, pmax = df['preco_atual'].min(), df['preco_atual'].max()
faixa_preco = st.sidebar.slider(
    "Faixa de Preço Atual",
    pmin,
    pmax,
    (pmin, pmax),
    format="R$ %.2f"
)
faixa_pvp = st.sidebar.slider("Faixa de P/VP", float(df['pvp_calc'].min()), float(df['pvp_calc'].max()), (0.0, float(df['pvp_calc'].max())))
max_dy = float(df['dy_calc'].fillna(0).max())
faixa_dy = st.sidebar.slider(
    "Faixa de DY 12M (%)",
    0.0,
    max_dy,
    (0.0, max_dy)
)

# --- Aplicar filtros ---
f = df.copy()
if query:
    f = f[
        f['ticker'].str.contains(query, case=False, na=False) |
        f['nome'].str.contains(query, case=False, na=False)
    ]
if sel_setor != 'Todos':
    f = f[f['setor'] == sel_setor]
if sel_tipo != 'Todos':
    f = f[f['tipo'] == sel_tipo]
f = f[f['preco_atual'].between(*faixa_preco)]
f = f[f['pvp_calc'].between(*faixa_pvp)]
f = f[f['dy_calc'].between(*faixa_dy)]

# --- Título e resultados ---
st.title("Dashboard de FIIs")
st.success(f"🔍 {len(f)} fundos encontrados")

# --- Fundos em destaque fixos ---
st.markdown("### ✨ Fundos em destaque")
with st.container():
    col1, col2, col3 = st.columns(3)
    for idx, r in enumerate([
        {'ticker': 'JPPC11', 'tipo': 'Tijolo', 'preco_atual': 124.46, 'vpa_calc': 116.31, 'pvp_calc': 1.07, 'dy_calc': 178.23, 'pl': 6.40e6},
        {'ticker': 'FAMB11', 'tipo': 'Tijolo', 'preco_atual': 786.99, 'vpa_calc': 1844.83, 'pvp_calc': 0.43, 'dy_calc': 158.46, 'pl': 226.06e6},
        {'ticker': 'CFHI11', 'tipo': 'Tijolo', 'preco_atual': 331.70, 'vpa_calc': 502.04, 'pvp_calc': 0.66, 'dy_calc': 92.13, 'pl': 47.49e6}
    ]):
        with [col1, col2, col3][idx]:
            st.subheader(f"{r['ticker']} ({r['tipo']})")
            st.metric("Preço Atual", f"R$ {r['preco_atual']:,.2f}")
            st.metric("VPA", f"R$ {r['vpa_calc']:,.2f}")
            st.metric("P/VP", f"{r['pvp_calc']:.2f}")
            st.metric("DY 12M", f"{r['dy_calc']:.2f}%")
            st.metric("PL (Mi)", f"{r['pl']/1e6:.2f}")

# --- Tabela Geral ---
st.markdown("---")
f2 = f.rename(
    columns={
        'ticker': 'Ticker', 'setor': 'Setor', 'tipo': 'Tipo',
        'preco_atual': 'Preço', 'vpa_calc': 'VPA',
        'pvp_calc': 'P/VP', 'dy_calc': 'DY 12M'
    }
)
st.dataframe(f2[['Ticker', 'Setor', 'Tipo', 'Preço', 'VPA', 'P/VP', 'DY 12M']])

# --- Navegação sidebar ---
st.sidebar.markdown("---")
if st.sidebar.button("📖 Glossário de Termos"):
    st.experimental_set_query_params(page="glossario")
if st.sidebar.button("🎬 Vídeos e Tutoriais"):
    st.experimental_set_query_params(page="ajuda")
