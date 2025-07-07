import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Análise de FII - Iniciante", page_icon="🔍", layout="wide")
st.markdown("<h1 style='text-align:left;'>📊Análise por fundo</h1>", unsafe_allow_html=True)

# Caminho para o banco
db_path = Path(__file__).resolve().parent.parent / "data" / "fiis.db"
# Conexão e leitura de tabelas
conn = sqlite3.connect(db_path)
fiis = pd.read_sql("SELECT * FROM fiis WHERE ativo = 1;", conn)
cotacoes = pd.read_sql("SELECT * FROM cotacoes;", conn)
hf_query = '''
SELECT fi.fii_id, f.ticker, i.nome AS indicador, fi.valor, fi.data_referencia
FROM fiis_indicadores fi
JOIN indicadores i ON i.id = fi.indicador_id
JOIN fiis f ON f.id = fi.fii_id
'''
inds = pd.read_sql(hf_query, conn)
setores = pd.read_sql("SELECT id, nome FROM setor;", conn)
tipos = pd.read_sql("SELECT id, nome FROM tipo_fii;", conn)
conn.close()

# Mapeamentos auxiliares
meses_pt = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']

def human_format(num):
    if pd.isna(num): return "–"
    n = float(num)
    if abs(n) >= 1e9: return f"{n/1e9:.2f} Bi"
    if abs(n) >= 1e6: return f"{n/1e6:.2f} Mi"
    if abs(n) >= 1e3: return f"{n/1e3:.2f} Mil"
    return f"{n:,.2f}"

# Sidebar: seleção
st.sidebar.title("Seleção de FII")
tickers = sorted(fiis["ticker"])
if "ticker" not in st.session_state:
    st.session_state.ticker = tickers[0]

ticker = st.sidebar.selectbox(
    "FII", tickers, index=tickers.index(st.session_state.ticker), key="ticker_select"
)
st.session_state.ticker = ticker

# Slider para períodos
years_div = st.sidebar.slider("Dividendos (anos)",1,10,1)
years_cot = st.sidebar.slider("Cotação (anos)",1,10,5)

# Dados do fundo selecionado
df_f = fiis[fiis["ticker"] == ticker].iloc[0]
# Resgata setor e tipo
setor = setores.set_index('id').loc[df_f["setor_id"], 'nome']
tipo = tipos.set_index('id').loc[df_f.get("tipo_id", None), 'nome'] if df_f.get("tipo_id") else 'N/D'

# Botões de mesma gestora
gest = df_f.get('gestao')
if gest:
    st.sidebar.markdown("**Fundos da mesma gestora**")
    mesmos = fiis[(fiis["gestao"] == gest) & (fiis["ticker"] != ticker)]
    for t in sorted(mesmos["ticker"]):
        if st.sidebar.button(t, key=f"btn_{t}"):
            st.session_state.ticker = t
            st.rerun()
else:
    st.sidebar.write("Somente o fundo pertence a mesma gestora")

# Prepara séries
fiid = int(df_f["id"])

# Cotação
df_cot = cotacoes[cotacoes['fii_id']==fiid].copy()
df_cot['data'] = pd.to_datetime(df_cot['data'])
df_cot.sort_values('data',ascending=False,inplace=True)
price = df_cot.iloc[0]['preco_fechamento'] if not df_cot.empty else np.nan
latest_date = df_cot.iloc[0]['data'].strftime('%d/%m/%Y') if not df_cot.empty else '-'

# Histórico de indicadores
hf = inds[inds['ticker']==ticker].copy()
hf['data_referencia'] = pd.to_datetime(hf['data_referencia'])

# Cálculos financeiros básicos
pl = hf[hf['indicador'].str.lower()=='patrimônio líquido']['valor'].iloc[-1] if not hf.empty else np.nan
qt = hf[hf['indicador'].str.lower()=='quantidade de cotas']['valor'].iloc[-1] if not hf.empty else np.nan
VPA = pl/qt if qt else np.nan
PVP = price/VPA if VPA else np.nan
mkt = price*qt if price and qt else np.nan

# 30 dias e 52 semanas
now = datetime.now()
past30 = df_cot[df_cot['data'] <= now - timedelta(days=30)]
delta30 = ((price - past30.iloc[0]['preco_fechamento'])/past30.iloc[0]['preco_fechamento']*100) if not past30.empty else np.nan

d52 = df_cot[df_cot['data'] >= now - timedelta(weeks=52)]
high52 = d52['preco_fechamento'].max() if not d52.empty else np.nan
low52 = d52['preco_fechamento'].min() if not d52.empty else np.nan

delta52 = ((price - low52) / low52 * 100) if pd.notna(low52) and low52 else np.nan

# Dividend Yield
# Filtra apenas os registros de dividendos
# Filtra dividendos e converte datas
divs = hf[hf['indicador'].str.lower() == 'dividendos'].copy()
divs['data_referencia'] = pd.to_datetime(divs['data_referencia'])

# Reagrupa por mês, somando cada mês só uma vez
df_div_mensal = (
    divs.assign(
        mes = divs['data_referencia'].dt.to_period('M').dt.to_timestamp()
    )
    .groupby('mes', as_index=False)['valor']
    .sum()
)

price_val = price or 1.0

def preco_em(data):
    tmp = df_cot[df_cot['data'] <= data]
    if tmp.empty:
        return price
    return tmp.iloc[-1]['preco_fechamento']

def DY_n_months(n):
    # Último dia do mês anterior
    last_day_prev_month = (now.replace(day=1) - timedelta(days=1))
    # Primeiro dia do período: exatamente n meses atrás, dia 1
    start_period = (now.replace(day=1) - relativedelta(months=n))
    mask = (
        (divs['data_referencia'] >= start_period) &
        (divs['data_referencia'] <= last_day_prev_month)
    )
    total_divs = divs.loc[mask, 'valor'].sum()
    return (total_divs / price) * 100

DYS = {
    '1M':  DY_n_months(1),
    '3M':  DY_n_months(3),
    '6M':  DY_n_months(6),
    '12M': DY_n_months(12),
}

# CSS para tooltips
st.markdown("""
<style>
.tooltip{position:relative;display:inline-block;cursor:help}
.tooltip .tooltiptext{visibility:hidden;width:200px;background:#333;color:#fff;text-align:center;border-radius:4px;padding:5px;position:absolute;z-index:1;bottom:100%;left:50%;transform:translateX(-50%);opacity:0;transition:opacity .3s}
.tooltip:hover .tooltiptext{visibility:visible;opacity:1}
.metric-label{font-size:1.1rem;font-weight:bold}
</style>
""",unsafe_allow_html=True)

with sqlite3.connect(db_path) as conn_im:
    df_im = pd.read_sql(
        "SELECT endereco FROM fiis_imoveis WHERE fii_id = ?", conn_im, params=(fiid,)
    )
qtd_imoveis = len(df_im)

# Dados do Fundo na tela
# cria 3 colunas pra distribuir os campos
col1, col2 = st.columns(2)
with col1:
    st.metric("Nome do fundo", df_f["nome"])
    st.metric("Gestora", df_f["gestao"] or "N/D")
    st.metric("Administradora", df_f["admin"] or "N/D")

with col2:
    st.metric("Setor", setor)
    st.metric("Tipo", tipo)
    if qtd_imoveis>0:
        st.metric("Quantidade de imóveis", qtd_imoveis)

st.markdown("---")

st.subheader(f"{ticker} — Ultimo fechamento em {latest_date}")
cols = st.columns(4)
labels = ["Preço Atual", "Máx 52 Semanas", "Mín 52 Semanas", "Variação 30d"]
values = [f"R$ {price:,.2f}", f"R$ {high52:,.2f}", f"R$ {low52:,.2f}", f"{delta30:.2f}%"]
tips   = ["Último fechamento\nVariação nos ultimso 12 meses", "Maior nas últimas 52 semanas", "Menor nas últimas 52 semanas", "Comparação: hoje vs 30 dias atrás"]
col = cols[0]
col.markdown(
    f"<div class='metric-label tooltip'>Preço Atual ℹ️"
    f"<span class='tooltiptext'>{tips[0]}</span></div>",
    unsafe_allow_html=True
)
col.metric(label="", value=values[0], delta=f"{delta52:.2f}%")
col.caption("Variação das últimas 52 semanas")

# As outras continuam como antes:
for idx in range(1, 4):
    col = cols[idx]
    col.markdown(
        f"<div class='metric-label tooltip'>{labels[idx]} ℹ️"
        f"<span class='tooltiptext'>{tips[idx]}</span></div>",
        unsafe_allow_html=True
    )
    col.metric(label="", value=values[idx])

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
    "<span class='tooltiptext'>"
    "Soma de dividendos dos últimos n meses ÷ preço de fechamento atual × 100"
    "</span></div>",
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

with sqlite3.connect(db_path) as conn_im:
    df_imoveis = pd.read_sql(
        """
        SELECT area_m2,
               num_unidades,
               tx_ocupacao
        FROM fiis_imoveis
        WHERE fii_id = ?
        """,
        conn_im,
        params=(fiid,)
    )

if not df_imoveis.empty:
    st.subheader("Imóveis")
    total_imoveis   = len(df_imoveis)
    total_unidades  = df_imoveis["num_unidades"].sum()
    total_area = df_imoveis["area_m2"].sum()
    weighted_ocup   = (df_imoveis["area_m2"] * df_imoveis["tx_ocupacao"]).sum() / total_area
    vac_phys        = 100 - weighted_ocup

    area_str = (
    f"{total_area:,.2f}"     
    .replace(",", "X")           
    .replace(".", ",")          
    .replace("X", "."))

    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(
        "<span class='tooltip'>Total de imóveis ℹ️"
        "<span class='tooltiptext'>Número total de imóveis que compõem o portfólio do fundo</span>",
        unsafe_allow_html=True
    )
    col1.metric(label="", value=total_imoveis)

    col2.markdown(
        "<span class='tooltip'>Total de unidades ℹ️"
        "<span class='tooltiptext'>Soma de todas as unidades habitacionais/comerciais</span>"
        "</span>",
        unsafe_allow_html=True
    )
    col2.metric(label="", value=total_unidades)

    # Área total (m²)
    col3.markdown(
        "<span class='tooltip'>Área total (m²) ℹ️"
        "<span class='tooltiptext'>Total da área em metros quadrados de todos os imóveis</span>"
        "</span>",
        unsafe_allow_html=True
    )
    col3.metric(label="", value=area_str)

    # Vacância Física (%)
    col4.markdown(
        "<span class='tooltip'>Vacância Física (%) ℹ️"
        "<span class='tooltiptext'>Percentual de área vaga calculado como 100% menos a ocupação ponderada</span>"
        "</span>",
        unsafe_allow_html=True
    )
    col4.metric(label="", value=f"{vac_phys:.2f}%")
