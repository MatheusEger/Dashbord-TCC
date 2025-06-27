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
fiis = pd.read_sql("SELECT * FROM fiis;", conn)
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

st.sidebar.title("Seleção de FII")
ticker = st.sidebar.selectbox("FII", sorted(fiis["ticker"]))
years_div = st.sidebar.slider("Dividendos (anos)", 1, 10, 1)
years_cot = st.sidebar.slider("Cotação (anos)", 1, 10, 5)

f = fiis[fiis["ticker"] == ticker].iloc[0]
setor = setores.set_index('id').loc[f["setor_id"], 'nome']
st.sidebar.markdown(f"**Ticker:** {ticker} **Setor:** {setor}")
if f.get('gestao'): st.sidebar.markdown(f"**Gestora:** {f['gestao']}")
if f.get('admin'): st.sidebar.markdown(f"**Administrador:** {f['admin']}")

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
values2 = [f"R$ {VPA:,.2f}", f"{PVP:.2f}%", f"R$ {pl:,.2f}", f"R$ {mkt:,.2f}"]
tips2 = ["Valor patrimonial por cota", "Preço ÷ valor patrimonial", "Ativos menos passivos", "Capitalização total"]
for col, lab, val, tip in zip(cols2, labels2, values2, tips2):
    col.markdown(f"<div class='metric-label tooltip'>{lab} ℹ️<span class='tooltiptext'>{tip}</span></div>", unsafe_allow_html=True)
    col.metric(label="", value=val)

st.subheader("Dividend Yield")
cols3 = st.columns(4)
for col, period in zip(cols3, ['1M','3M','6M','12M']):
    col.metric(label=f"{period}", value=f"{DYS[period]:.2f}%")

left, right = st.columns(2)
left.markdown("**Distribuições Mensais**")
df_div = divs.copy(); df_div['mes']=df_div['data_referencia'].dt.to_period('M').dt.to_timestamp()
mensal=df_div.groupby('mes')['valor'].sum().reset_index().tail(years_div*12)
fig_div=px.bar(mensal,x='mes',y='valor',labels={'mes':'Mês/Ano','valor':'Dividendos (R$)'},color_discrete_sequence=['green'])
fig_div.update_xaxes(tickformat='%b/%Y',dtick='M1',tickangle=-45)
left.plotly_chart(fig_div,use_container_width=True)

right.markdown("**Evolução da Cotação**")
hc=df_cot[df_cot['data']>=now-relativedelta(years=years_cot)]
df_sem=hc.set_index('data').resample('W-FRI')['preco_fechamento'].last().reset_index()
fig_price=px.line(df_sem,x='data',y='preco_fechamento',labels={'data':'Ano','preco_fechamento':'R$'},color_discrete_sequence=['blue'])
fig_price.update_traces(hovertemplate='%{x|%d/%m/%Y}<br>R$ %{y:,.2f}<extra></extra>')
min_date,max_date=df_sem['data'].min(),df_sem['data'].max()
fig_price.update_xaxes(range=[min_date,max_date],tickformat='%Y',dtick='M12')
right.plotly_chart(fig_price,use_container_width=True)

st.subheader("Vacância Física")
# Vacância Física
with sqlite3.connect(db_path) as conn_im:
    has_table = pd.read_sql("SELECT count(*) as cnt FROM sqlite_master WHERE type='table' AND name='imoveis';", conn_im)['cnt'].iat[0] > 0
if has_table:
# Verifica se existe a tabela de imóveis
    with sqlite3.connect(db_path) as conn_im:
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='imoveis';", conn_im)
        st.info("Nenhum dado de imóveis disponível para este fundo.")

