import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Análise de FII - Iniciante", layout="wide")
st.markdown("<h1 style='text-align:left;'>📊Análise por fundo</h1>", unsafe_allow_html=True)

db_path = Path(__file__).resolve().parent.parent / "data" / "fiis.db"
conn = sqlite3.connect(db_path)
fiis = pd.read_sql("SELECT * FROM fiis WHERE ativo = 1;", conn)
cotacoes = pd.read_sql("SELECT * FROM cotacoes;", conn)
hf_query = """
SELECT fi.fii_id, f.ticker, i.nome AS indicador, fi.valor, fi.data_referencia
FROM fiis_indicadores fi
JOIN indicadores i ON i.id = fi.indicador_id
JOIN fiis f ON f.id = fi.fii_id
"""
inds = pd.read_sql(hf_query, conn)
setores = pd.read_sql("SELECT id, nome FROM setor;", conn)
conn.close()

meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

def human_format(num):
    """
    Formata números como:
      - até 999              → sem sufixo
      - milhares (>= 1e3)    → ‘x.xxx Mil’
      - milhões (>= 1e6)     → ‘x,xx Mi’
      - bilhões (>= 1e9)     → ‘x,xx Bi’
    """
    if pd.isna(num):
        return "–"
    n = float(num)
    if abs(n) >= 1e9:
        return f"{n/1e9:.2f} Bi"
    if abs(n) >= 1e6:
        return f"{n/1e6:.2f} Mi"
    if abs(n) >= 1e3:
        return f"{n/1e3:.2f} Mil"
    return f"{n:,.2f}"

st.sidebar.title("Seleção de FII")
tickers = sorted(fiis["ticker"])
if "ticker" not in st.session_state:
    st.session_state.ticker = tickers[0]

ticker = st.sidebar.selectbox(
    "FII",
    tickers,
    index=tickers.index(st.session_state.ticker),
    key="ticker")

f = fiis[fiis["ticker"] == st.session_state.ticker].iloc[0]

years_div = st.sidebar.slider("Dividendos (anos)", 1, 10, 1)
years_cot = st.sidebar.slider("Cotação (anos)", 1, 10, 5)

f = fiis[fiis["ticker"] == ticker].iloc[0]
setor = setores.set_index('id').loc[f["setor_id"], 'nome']
f = fiis[fiis["ticker"] == ticker].iloc[0]

# cabeçalho de dados da empresa
st.sidebar.markdown("## Dados do Fundo")
st.sidebar.markdown(f"**Nome:** {f['nome']}")
st.sidebar.markdown(f"**Gestora:** {f['gestao'] or 'N/D'}")
st.sidebar.markdown(f"**Administradora:** {f['admin'] or 'N/D'}")

# imóveis (se existir tabela fiis_imoveis)
with sqlite3.connect(db_path) as conn_im:
    df_im = pd.read_sql(
        "SELECT endereco FROM fiis_imoveis WHERE fii_id = ?",
        conn_im,
        params=(int(f["id"]),)
    )
if not df_im.empty:
    st.sidebar.markdown(f"**Quantidade de imóveis:** {len(df_im)}")

# listar fundos da mesma gestora
gest = f.get("gestao")
if gest:
    mesmos = fiis[(fiis["gestao"] == gest) & (fiis["ticker"] != f["ticker"])]
    if not mesmos.empty:
        st.sidebar.markdown("**Fundos da mesma gestora**")
        for t in sorted(mesmos["ticker"]):
            # cada botão, quando clicado, atualiza session_state e recarrega o app
            if st.sidebar.button(t, key=f"btn_{t}"):
                st.session_state.ticker = t
                st.experimental_rerun()

fiid = int(f["id"])
df_cot = cotacoes[cotacoes['fii_id']==fiid].copy()
df_cot['data'] = pd.to_datetime(df_cot['data'])
df_cot.sort_values('data', ascending=False, inplace=True)
price = df_cot.iloc[0]['preco_fechamento'] if not df_cot.empty else np.nan
latest_date = df_cot.iloc[0]['data'].strftime('%d/%m/%Y') if not df_cot.empty else '-'

hf = inds[inds['ticker']==ticker].copy()
hf['data_referencia'] = pd.to_datetime(hf['data_referencia'])

pl = hf[hf['indicador'].str.lower()=='patrimônio líquido']['valor'].iloc[-1] if not hf.empty else np.nan
qt = hf[hf['indicador'].str.lower()=='quantidade de cotas']['valor'].iloc[-1] if not hf.empty else np.nan
VPA = pl/qt if qt else np.nan
PVP = price/VPA if VPA else np.nan
mkt = price*qt if price and qt else np.nan

now = datetime.now()
past30 = df_cot[df_cot['data'] <= now - timedelta(days=30)]
delta30 = ((price - past30.iloc[0]['preco_fechamento'])/past30.iloc[0]['preco_fechamento']*100) if not past30.empty else np.nan

d52 = df_cot[df_cot['data'] >= now - timedelta(weeks=52)]
high52 = d52['preco_fechamento'].max() if not d52.empty else np.nan
low52 = d52['preco_fechamento'].min() if not d52.empty else np.nan

divs = hf[hf['indicador'].str.lower()=='dividendos'].sort_values('data_referencia', ascending=False)
price_val = price if price else 1
def DY_last(n): return divs['valor'].head(n).sum()/price_val*100
DYS = {'1M': DY_last(1), '3M': DY_last(3), '6M': DY_last(6), '12M': DY_last(12)}

st.markdown(
    """
    <style>
    .tooltip{position:relative;display:inline-block;cursor:help}
    .tooltip .tooltiptext{visibility:hidden;width:200px;background:#333;color:#fff;text-align:center;border-radius:4px;padding:5px;position:absolute;z-index:1;bottom:100%;left:50%;transform:translateX(-50%);opacity:0;transition:opacity .3s}
    .tooltip:hover .tooltiptext{visibility:visible;opacity:1}
    .metric-label{font-size:1.1rem;font-weight:bold}
    </style>
    """, unsafe_allow_html=True
)

st.subheader(f"{ticker} — Ultimo fechamento em {latest_date}")
cols = st.columns(4)
labels = ["Preço Atual", "Máx 52 Semanas", "Mín 52 Semanas", "Variação 30d"]
values = [f"R$ {price:,.2f}", f"R$ {high52:,.2f}", f"R$ {low52:,.2f}", f"{delta30:.2f}%"]
tips = ["Último fechamento", "Maior nas últimas 52 semanas", "Menor nas últimas 52 semanas", "Comparação: hoje vs 30 dias atrás"]
for col, lab, val, tip in zip(cols, labels, values, tips):
    col.markdown(f"<div class='metric-label tooltip'>{lab} ℹ️<span class='tooltiptext'>{tip}</span></div>", unsafe_allow_html=True)
    col.metric(label="", value=val)

st.markdown("---")

st.subheader(f"Indicadores do fundo {ticker}")
cols2 = st.columns(4)
labels2 = ["VPA", "P/VP", "Patrimônio Líquido", "Valor de Mercado"]
values2 = [
    f"R$ {VPA:,.2f}",
    f"{PVP:.2f}%",
    f"R$ {human_format(pl)}",
    f"R$ {human_format(mkt)}"]
tips2 = [
    "Valor patrimonial por cota",
    "Preço ÷ valor patrimonial",
    "Ativos menos passivos (ativos – passivos)",
    "Capitalização total (preço × número de cotas)"
]

for col, lab, val, tip in zip(cols2, labels2, values2, tips2):
    col.markdown(
        f"<div class='metric-label tooltip'>{lab} ℹ️"
        f"<span class='tooltiptext'>{tip}</span></div>",
        unsafe_allow_html=True
    )
    col.metric(label="", value=val)
    
st.markdown(
    "<div class='metric-label tooltip'>Dividend Yield ℹ️"
    "<span class='tooltiptext'>Rendimento de dividendos pagos nos últimos períodos ÷ preço atual</span>"
    "</div>",
    unsafe_allow_html=True
)
cols3 = st.columns(4)
for col, period in zip(cols3, ['1M','3M','6M','12M']):
    col.metric(label=period, value=f"{DYS[period]:.2f}%")


st.columns(1)
st.markdown("**Distribuições Mensais**")
df_div = (divs.assign(
    mes=divs['data_referencia']
              .dt.to_period('M')
              .dt.to_timestamp()
)
).groupby('mes')['valor'].sum().reset_index().tail(years_div*12)

if df_div.empty:
    st.info(f"Sem distribuição mensal nos últimos {years_div*12} meses.")
else:
    fig_div = px.bar(
        df_div, x='mes', y='valor',
        labels={'mes':'Mês/Ano','valor':'Dividendos (R$)'}
    )
    fig_div.update_xaxes(
        tickformat='%b/%Y', dtick='M1', tickangle=-45
    )
    st.plotly_chart(fig_div, use_container_width=True)

st.markdown("**Evolução da Cotação**")

hc = df_cot[df_cot['data'] >= now - relativedelta(years=years_cot)]
df_sem = (hc.set_index('data')['preco_fechamento'].resample('W-FRI').last().ffill().reset_index())
fig_price = px.line(df_sem,x='data',y='preco_fechamento',labels={'data': 'Ano', 'preco_fechamento': 'R$'})
fig_price.update_traces(hovertemplate='%{x|%d/%m/%Y}<br>R$ %{y:,.2f}<extra></extra>')
x = df_sem['data'].map(pd.Timestamp.toordinal).values
y = df_sem['preco_fechamento'].values
m, b = np.polyfit(x, y, 1)
trend_y = m * x + b
fig_price.add_scatter(x=df_sem['data'],y=trend_y,mode='lines',name='Tendência',line=dict(color='red', dash='dash'))
min_date, max_date = df_sem['data'].min(), df_sem['data'].max()
fig_price.update_xaxes(range=[min_date, max_date], tickformat='%Y', dtick='M12')

st.plotly_chart(fig_price, use_container_width=True)

st.subheader("Vacância Física")
# Vacância Física
with sqlite3.connect(db_path) as conn_im:
    has_table = pd.read_sql("SELECT count(*) as cnt FROM sqlite_master WHERE type='table' AND name='imoveis';", conn_im)['cnt'].iat[0] > 0
if has_table:
# Verifica se existe a tabela de imóveis
    with sqlite3.connect(db_path) as conn_im:
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='imoveis';", conn_im)
        st.info("Nenhum dado de imóveis disponível para este fundo.")

