import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

# --- Configuração da página ---
st.set_page_config("Dashboard de FIIs", layout="wide")

# --- Path do banco (arquivo ao lado deste script) ---
DB_PATH = Path(__file__).parents[1] / "data" / "fiis.db"

# --- 1) Conectar e listar tabelas (debug) ---
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tabelas disponíveis:", cursor.fetchall())

# --- 2) Carregar dados de FIIs com indicadores base ---
sql = """
SELECT
  f.id,
  f.ticker,
  f.nome,
  s.nome AS setor,
  (SELECT c2.preco_fechamento
     FROM cotacoes c2
    WHERE c2.fii_id = f.id
    ORDER BY c2.data DESC
    LIMIT 1
  ) AS preco_atual,
  MAX(CASE WHEN ind.nome = 'Patrimônio Líquido'  THEN fi.valor END) AS pl,
  MAX(CASE WHEN ind.nome = 'Quantidade de Cotas' THEN fi.valor END) AS qt,
  MAX(CASE WHEN ind.nome = 'Número de Imóveis'   THEN fi.valor END) AS num_imoveis,
  MAX(CASE WHEN ind.nome = 'Vacância Física'     THEN fi.valor END) AS vacancia_fisica
FROM fiis f
LEFT JOIN setor           s   ON f.setor_id       = s.id
LEFT JOIN fiis_indicadores fi  ON fi.fii_id        = f.id
LEFT JOIN indicadores     ind ON ind.id           = fi.indicador_id
GROUP BY f.id, f.ticker, f.nome, s.nome
"""
df = pd.read_sql_query(sql, conn)

# buscar dividendos para DY 12M
divs = pd.read_sql_query(
    """
    SELECT fi.fii_id, fi.valor, fi.data_referencia
      FROM fiis_indicadores fi
      JOIN indicadores i ON i.id = fi.indicador_id
     WHERE i.nome = 'Dividendos'
    """,
    conn,
    parse_dates=['data_referencia']
)
conn.close()

# --- 2) Limpeza e cálculos adicionais ---
# remover sem preço
df = df[df['preco_atual'].notna()].copy()

# converter para numérico
for col in ['pl', 'qt', 'preco_atual', 'vacancia_fisica']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# calcular VPA e P/VP
df['vpa_calc'] = df['pl'] / df['qt']
df['pvp_calc'] = df['preco_atual'] / df['vpa_calc']

# preparar dividendos por mês
divs['mes'] = divs['data_referencia'].dt.to_period('M').dt.to_timestamp()
mensal = (
    divs.groupby(['fii_id','mes'])['valor']
        .sum()
        .reset_index()
)
# somar últimos 12 meses
hoje = pd.Timestamp.today().to_period('M').to_timestamp()
ult_12m = (
    mensal[mensal['mes'] >= (hoje - pd.DateOffset(months=12))]
    .groupby('fii_id')['valor']
    .sum()
    .rename('div12m')
)
# unir e calcular DY%
df = df.merge(ult_12m, left_on='id', right_index=True, how='left')
df['dy_calc'] = (df['div12m'] / df['preco_atual']) * 100

# --- Listas para filtros ---
setores      = ['Todos'] + sorted(df['setor'].unique().tolist())
metricas_ord = ['DY 12M', 'P/VP', 'VPA']

# --- Cabeçalho ---
col_logo, col_title = st.columns([1,5])
with col_logo:
    st.image("./image/logo.png", width=80)
with col_title:
    st.title("Meu Primeiro Dashboard de FIIs")
    st.caption("Encontre seu FII de forma simples e guiada")

# --- 3) Busca e filtros ---
st.markdown("## 🔎 Encontre um FII")
search_col, filter_col = st.columns([3,1])
with search_col:
    query = st.text_input("", placeholder="Ex.: KNRI11, XPML11…")
with filter_col:
    sel_setor   = st.selectbox("Filtrar por Setor", setores)
    faixa_pvp   = st.slider("Faixa de P/VP", 0.0, 5.0, (0.0, 2.0))
    ordenar_por = st.selectbox("Ordenar por", metricas_ord)

# --- 4) Aplicar filtros ---
filtered = df.copy()
if query:
    mask = (
        filtered['nome'].str.contains(query, case=False, na=False) |
        filtered['ticker'].str.contains(query, case=False, na=False)
    )
    filtered = filtered[mask]
if sel_setor != 'Todos':
    filtered = filtered[filtered['setor'] == sel_setor]
filtered = filtered[
    filtered['pvp_calc'].between(*faixa_pvp) |
    filtered['pvp_calc'].isna()
]
st.write(f"🔍 {len(filtered)} fundos encontrados")

# --- 5) Top 3 por métrica escolhida ---
col_map = {'DY 12M': 'dy_calc', 'P/VP': 'pvp_calc', 'VPA': 'vpa_calc'}
asc     = False if ordenar_por == 'P/VP' else True
if ordenar_por == 'DY 12M': asc = False
else: asc = True if ordenar_por == 'VPA' else False
# ordenar adequadamente (DY e VPA maiores são melhores, P/VP menor é melhor)
if ordenar_por == 'P/VP':
    top3 = filtered.sort_values('pvp_calc', ascending=True).head(3)
elif ordenar_por == 'VPA':
    top3 = filtered.sort_values('vpa_calc', ascending=False).head(3)
else:
    top3 = filtered.sort_values('dy_calc', ascending=False).head(3)

# --- 6) Exibir cards de destaque ---
st.markdown("### ✨ Fundos em destaque")
cols = st.columns(3)
for col, (_, row) in zip(cols, top3.iterrows()):
    with col:
        st.header(row.ticker)
        st.subheader(row.setor)
        st.metric("Preço Atual",   f"R$ {row.preco_atual:,.2f}")
        st.metric("VPA",           f"R$ {row.vpa_calc:,.2f}")
        st.metric("P/VP",          f"{row.pvp_calc:.2f}")
        st.metric("DY 12M",        f"{row.dy_calc:.2f}%")
        st.metric("PL (Mi)",       f"{row.pl/1e6:.2f}")
        st.metric("Imóveis",       f"{int(row.num_imoveis)}")
        st.metric("Vacância (%)",  f"{row.vacancia_fisica:.2f}")
        st.button("Ver Detalhes", key=f"detail_{row.ticker}")

# --- 7) Visão geral em tabela ---
st.markdown("---")
st.markdown("### 📊 Visão Geral dos Fundos Filtrados")
st.dataframe(filtered[[
    'ticker','setor','preco_atual','vpa_calc','pvp_calc','dy_calc',
    'pl','num_imoveis','vacancia_fisica'
]])

# --- Dica para iniciantes ---
if st.button("💡 Dica para iniciantes"):
    st.info(
        "- **Ticker**: código do fundo (ex.: KNRI11)\n"
        "- **VPA**: valor patrimonial por cota\n"
        "- **P/VP**: preço sobre valor patrimonial (<1 pode indicar desconto)\n"
        "- **DY 12M**: dividend yield dos últimos 12 meses\n"
        "- **PL**: patrimônio líquido total\n"
        "- **Número de Imóveis** e **Vacância** ajudam a ver a exposição e risco\n\n"
        "Use filtros e ordene pelos indicadores para encontrar o fundo certo para você!"
    )

# --- Rodapé ---
st.markdown("---")
st.markdown("[📖 Glossário Completo](#) • [❓ Ajuda](#)")
