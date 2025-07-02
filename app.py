import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from dateutil.relativedelta import relativedelta

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard de FIIs", layout="wide")

# --- DB Path ---
DB_PATH = Path(__file__).resolve().parent / "data" / "fiis.db"

# --- Conexão e leitura ---
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
    conn, parse_dates=['data']
)
inds = pd.read_sql_query(
    """
    SELECT fi.fii_id, i.nome AS indicador, fi.valor, fi.data_referencia
    FROM fiis_indicadores fi
    JOIN indicadores i ON i.id = fi.indicador_id
    """,
    conn, parse_dates=['data_referencia']
)
conn.close()

# --- Construção DataFrame ---
df = df_meta.copy()

# Preço Atual
ultimo = (
    cotacoes.sort_values(['fii_id','data'])
    .groupby('fii_id')['preco_fechamento']
    .last()
    .rename('preco_atual')
)
df = df.merge(ultimo, left_on='id', right_index=True, how='left')
df['preco_atual'] = pd.to_numeric(df['preco_atual'], errors='coerce')

# PL e Qt
pivot = inds.pivot_table(index='fii_id', columns='indicador', values='valor', aggfunc='max')
pivot = pivot.rename(columns={'Patrimônio Líquido':'pl','Quantidade de Cotas':'qt'})
pivot[['pl','qt']] = pivot[['pl','qt']].apply(pd.to_numeric, errors='coerce')
df = df.merge(pivot[['pl','qt']], left_on='id', right_index=True, how='left')
df['vpa_calc'] = df['pl'] / df['qt']
df['pvp_calc'] = df['preco_atual'] / df['vpa_calc']

# DY 12M (soma últimos 12 meses dividido pelo preço atual * 100)
divs = inds[inds['indicador']=='Dividendos'].copy()
divs['periodo'] = divs['data_referencia'].dt.to_period('M')
ult = divs['periodo'].max()
ini = ult - 11
d12 = divs[divs['periodo'].between(ini, ult)]
soma = d12.groupby('fii_id')['valor'].sum().rename('div12m')
df = df.merge(soma, left_on='id', right_index=True, how='left')
df['dy_calc'] = (df['div12m'] / df['preco_atual']) * 100

# --- Filtros e opções ---
setores = ['Todos'] + sorted(df['setor'].dropna().unique())
tipos   = ['Todos'] + sorted(df['tipo'].dropna().unique())
metricas = ['DY 12M','P/VP','VPA']

# Cabeçalho
col_logo, col_title = st.columns([1,5])
with col_logo:
    st.image("./image/logo.png", width=80)
with col_title:
    st.title("Dashboard de FIIs")
    st.caption("Encontre seu FII de forma simples e guiada")

# Busca e filtros
st.markdown("## 🔎 Encontre um FII")
sc, fc = st.columns([3,1])
with sc:
    query = st.text_input("Buscar por ticker ou nome", placeholder="Ex.: FLRP11...")
with fc:
    sel_setor = st.selectbox("Setor", setores)
    sel_tipo  = st.selectbox("Tipo", tipos)
    pmin = float(df['preco_atual'].min())
    pmax = float(df['preco_atual'].max())
    max_dy = float(df['dy_calc'].fillna(0).max())
    faixa_preco = st.slider("Faixa de Preço Atual", pmin, pmax, (pmin, pmax), format="R$ %.2f")
    faixa_pvp   = st.slider("Faixa de P/VP", 0.0, 5.0, (0.0, 2.0))
    faixa_dy    = st.slider("Faixa de DY 12M (%)", 0.0, max_dy, (0.0, max_dy))
    orden       = st.selectbox("Ordenar por", metricas)

# Aplicar filtros
f = df.copy()

# 1) Filtro de busca por texto (ticker ou nome)
if query:
    f = f[
        f['ticker'].str.contains(query, case=False, na=False) |
        f['nome'].str.contains(query, case=False, na=False)
    ]

# 2) Filtro por setor
if sel_setor != 'Todos':
    f = f[f['setor'] == sel_setor]

# 3) Filtro por tipo
if sel_tipo != 'Todos':
    f = f[f['tipo'] == sel_tipo]

# 4) Filtro por faixa de preço atual
f = f[f['preco_atual'].between(*faixa_preco)]

# 5) Filtro por faixa de P/VP
f = f[f['pvp_calc'].between(*faixa_pvp)]

# 6) Filtro por faixa de DY 12M
f = f[f['dy_calc'].between(*faixa_dy)]

st.write(f"🔍 {len(f)} fundos encontrados")

# Destaques Top3
mapa = {'DY 12M':'dy_calc','P/VP':'pvp_calc','VPA':'vpa_calc'}
if orden == 'P/VP':
    top = f.nsmallest(3, mapa[orden])
elif orden == 'VPA':
    top = f.nlargest(3, mapa[orden])
else:
    top = f.nlargest(3, mapa[orden])

st.markdown("### ✨ Fundos em destaque")
cols = st.columns(3)
for c, (_, row) in zip(cols, top.iterrows()):
    with c:
        st.subheader(f"{row.ticker} ({row.tipo})")
        st.metric("Preço Atual", f"R$ {row.preco_atual:,.2f}")
        st.metric("VPA",         f"R$ {row.vpa_calc:,.2f}")
        st.metric("P/VP",        f"{row.pvp_calc:.2f}")
        st.metric("DY 12M",      f"{row.dy_calc:.2f}%")
        if pd.notna(row.pl):
            st.metric("PL (Mi)", f"{row.pl/1e6:.2f}")

# Tabela
st.markdown("---")
st.markdown("### 📊 Visão Geral")
f2 = f.rename(columns={
    'ticker':'Ticker','setor':'Setor','tipo':'Tipo',
    'preco_atual':'Preço','vpa_calc':'VPA',
    'pvp_calc':'P/VP','dy_calc':'DY 12M'
})
st.dataframe(f2[['Ticker','Setor','Tipo','Preço','VPA','P/VP','DY 12M']])
