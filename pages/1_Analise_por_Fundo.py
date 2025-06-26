import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta

st.set_page_config(page_title="Análise por Fundo", layout="wide")

# Conexão com o banco
db_path = Path(__file__).resolve().parent.parent / "data" / "fiis.db"
conn = sqlite3.connect(db_path)
fiis = pd.read_sql("SELECT * FROM fiis;", conn)
cotacoes = pd.read_sql("SELECT * FROM cotacoes;", conn)
inds = pd.read_sql(
    """
    SELECT fi.fii_id, f.ticker AS ticker, i.nome AS indicador,
           fi.valor, fi.data_referencia
    FROM fiis_indicadores fi
    JOIN indicadores i ON i.id = fi.indicador_id
    JOIN fiis f ON f.id = fi.fii_id
    """, conn)
setores = pd.read_sql("SELECT * FROM setor;", conn)
conn.close()

# Sidebar: configurações e dados do fundo
ticker = st.sidebar.selectbox("FII", sorted(fiis["ticker"]), key="ticker")
# Adicione isto para o filtro de distribuições, padrão 1 ano:
dist_years = st.sidebar.slider("Distribuição de dividendos (Anos)", 1, 10, 1)
years = st.sidebar.slider("Histórico de cotações (Anos)", 1, 10, 5)
st.sidebar.markdown("---")

# Dados do fundo
f = fiis[fiis["ticker"] == ticker].iloc[0]
setor = setores.loc[setores["id"] == f["setor_id"], "nome"].iat[0]

# Função para indicador histórico
def get_hist(tick, name):
    df = inds[(inds['ticker']==tick) & (inds['indicador'].str.lower()==name.lower())]
    return df.sort_values('data_referencia')['valor'].iat[-1] if not df.empty else np.nan

def set_ticker(new_ticker):
    st.session_state['ticker'] = new_ticker    

# Dados do fundo direto da tabela fiis
f = fiis[fiis["ticker"] == ticker].iloc[0]
nome_completo = f.get('nome', '')
gestora = f.get('gestao', np.nan)
administrador = f.get('admin', np.nan)
setor = setores.loc[setores["id"] == f["setor_id"], "nome"].iat[0]

st.sidebar.markdown("**Dados do Fundo**")
st.sidebar.markdown(f"- **Nome:** {nome_completo}")
if not pd.isna(gestora):         st.sidebar.markdown(f"- **Gestora:** {gestora}")
if not pd.isna(administrador):    st.sidebar.markdown(f"- **Administrador:** {administrador}")
st.sidebar.markdown(f"- **Setor:** {setor}")

# Atalhos para fundos da mesma gestora
if not pd.isna(gestora):
    same = [t for t in sorted(fiis['ticker']) if t!=ticker and fiis.loc[fiis['ticker']==t, 'gestao'].iat[0]==gestora]
    if same:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Fundos da mesma gestora**")
        for t in same:
            st.sidebar.button(t, key=f"btn_{t}", on_click=set_ticker, args=(t,))

# Prepara dados principais
df_cot = cotacoes[cotacoes['fii_id']==f['id']].copy()
df_cot['data'] = pd.to_datetime(df_cot['data'])
df_cot.sort_values('data',ascending=False,inplace=True)
price = df_cot.iloc[0]['preco_fechamento'] if not df_cot.empty else np.nan
date = df_cot.iloc[0]['data'] if not df_cot.empty else pd.NaT

# Data segura para exibir
date_str = date.strftime('%d/%m/%Y') if not pd.isna(date) else '-'

# Histórico de indicadores
hf = inds[inds['ticker']==ticker].copy()
hf['data_referencia'] = pd.to_datetime(hf['data_referencia'])

# Patrimônio Líquido e Quantidade de Cotas
raw_pat = f.get('patrimonio_liquido', np.nan)
raw_qt  = f.get('qtd_cotas', f.get('quantidade_cotas', np.nan))

pl = get_hist(ticker,'Patrimônio Líquido')
pl = raw_pat if np.isnan(pl) else pl
qt = get_hist(ticker,'Quantidade de Cotas')
qt = raw_qt if np.isnan(qt) else qt

# Cálculos
def safe_div(a,b): return (a/b) if b else np.nan
VPA = safe_div(pl,qt)
PVP = safe_div(price,VPA)
mkt = price*qt if price and qt else np.nan
now = datetime.now()

# Delta 30d
past30 = df_cot[df_cot['data']<= now-timedelta(days=30)]
delta30 = (price/past30.iloc[0]['preco_fechamento']-1)*100 if not past30.empty else np.nan

# Máx/Min 3M
d3m = df_cot[df_cot['data']>= now-timedelta(days=90)]
high3 = d3m['preco_fechamento'].max() if not d3m.empty else np.nan
low3  = d3m['preco_fechamento'].min() if not d3m.empty else np.nan

# Dividendos
divs = hf[hf['indicador'].str.lower()=='dividendos'].sort_values('data_referencia')
last = get_hist(ticker,'Dividendos')

def DY(m):
    cutoff = now - timedelta(days=30*m)
    soma = divs[divs['data_referencia'] >= cutoff]['valor'].sum()
    return (soma / price) * 100 if price and not divs.empty else np.nan

DYS = {
    'Atual': (last / price) * 100 if price else np.nan,
    '3M': DY(3),
    '6M': DY(6),
    '12M': DY(12)
}

# Formatação
def fmt(v,mode='moeda'):
    if pd.isna(v): return '-'
    if mode=='moeda': return f"R$ {v:,.2f}".replace(',','X').replace('.',',').replace('X','.')
    return f"{v:.2f}%"

def abr(v):
    if pd.isna(v): return '-'
    if abs(v)>=1e9: return f"R$ {v/1e9:.2f} Bi"
    if abs(v)>=1e6: return f"R$ {v/1e6:.2f} Mi"
    if abs(v)>=1e3: return f"R$ {v/1e3:.2f} mil"
    return fmt(v)

# CSS tooltips
st.markdown("""
<style>.tooltip{position:relative;display:inline-block;cursor:help;} .tooltip .tooltiptext{visibility:hidden;width:140px;background:#333;color:#fff;text-align:center;border-radius:4px;padding:4px;position:absolute;z-index:1;bottom:125%;left:50%;margin-left:-70px;opacity:0;transition:opacity 0.2s;} .tooltip:hover .tooltiptext{visibility:visible;opacity:1;}</style>
""",unsafe_allow_html=True)

# Dashboard
title = st.title("Análise por Fundo")
st.markdown(f"Fechamento: {date_str}")
col1,col2,col3 = st.columns(3)
col1.markdown("**Preço Atual** <span class='tooltip'>ℹ️<span class='tooltiptext'>Última cotação</span></span>",unsafe_allow_html=True)
col1.metric("",fmt(price),delta=fmt(delta30,'percentual'))
col1.caption("Variação dos últimos 30 dias")
col2.markdown("**Máximo 3M** <span class='tooltip'>ℹ️<span class='tooltiptext'>Maior nos últimos 3 meses</span></span>",unsafe_allow_html=True)
col2.metric("",fmt(high3))
col3.markdown("**Mínimo 3M** <span class='tooltip'>ℹ️<span class='tooltiptext'>Menor nos últimos 3 meses</span></span>",unsafe_allow_html=True)
col3.metric("",fmt(low3))

# Segunda linha
r1,r2,r3,r4=st.columns(4)
r1.markdown("**VPA** <span class='tooltip'>ℹ️<span class='tooltiptext'>Patrimonial por cota</span></span>",unsafe_allow_html=True)
r1.metric("",fmt(VPA))
r2.markdown("**P/VP** <span class='tooltip'>ℹ️<span class='tooltiptext'>Preço sobre Valor Patrimonial</span></span>", unsafe_allow_html=True)
pvp_text = fmt(PVP, 'percentual')
# só mostra comentário se PVP for diferente de zero
if PVP and PVP != 0:
    pvp_comment = "Desconto" if PVP < 1 else "Prêmio"
else:
    pvp_comment = ""
r2.metric("", pvp_text, pvp_comment)
r2.caption("P/VP maior que 1 indica prêmio")
r2.caption("P/VP menor que 1 indica desconto")
r3.markdown("**Patrimônio Líquido** <span class='tooltip'>ℹ️<span class='tooltiptext'>Ativos menos passivos</span></span>",unsafe_allow_html=True)
r3.metric("",abr(pl))
r4.markdown("**Valor de Mercado** <span class='tooltip'>ℹ️<span class='tooltiptext'>Capitalização de mercado</span></span>",unsafe_allow_html=True)
r4.metric("",abr(mkt))

# Gráficos

# Distribuições nos últimos X anos (sidebar)
st.subheader(f"Distribuições nos últimos {dist_years} anos")

# Destaque dos Dividend Yields
c1, c2, c3, c4 = st.columns(4)
c1.markdown("**YIELD 1 MÊS**");    c1.markdown(f"**{DYS['Atual']:.2f}%**")
c2.markdown("**YIELD 3 MESES**");  c2.markdown(f"**{DYS['3M']:.2f}%**")
c3.markdown("**YIELD 6 MESES**");  c3.markdown(f"**{DYS['6M']:.2f}%**")
c4.markdown("**YIELD 12 MESES**"); c4.markdown(f"**{DYS['12M']:.2f}%**")


# 1) Filtra só dividendos e converte para timestamp mensal
df_div = hf[
    (hf['indicador'].str.lower() == 'dividendos')
].copy()
df_div['mes'] = df_div['data_referencia'].dt.to_period('M').dt.to_timestamp()

# 2) Agrega por mês
mensal = df_div.groupby('mes', as_index=False)['valor'].sum()

# 3) Restringe ao período desejado (ex.: últimos `years` anos)
anos = years  # pode ser o mesmo `years` que você já usa no gráfico de cotação
limite = now - timedelta(days=365 * anos)
hd = mensal[mensal['mes'] >= limite]

if not hd.empty:
    # 4) Linha de dividendos
    fig_div = px.line(
        hd,
        x='mes',
        y='valor',
        labels={'mes': 'Mês', 'valor': 'Dividendos (R$)'},
        title='Evolução dos Dividendos'
    )
    # 5) Formata o eixo X igual ao outro gráfico
    fig_div.update_xaxes(tickformat='%b\n%Y')
    
    # 6) Calcula e adiciona reta de tendência
    x_ord = hd['mes'].map(datetime.toordinal)
    trend = np.polyval(np.polyfit(x_ord, hd['valor'], 1), x_ord)
    fig_div.add_scatter(
        x=hd['mes'],
        y=trend,
        mode='lines',
        line=dict(color='red', dash='dash'),
        name='Tendência'
    )
    
    # 7) Desenha usando container width
    st.plotly_chart(fig_div, use_container_width=True)
else:
    st.write("Não há dividendos no período selecionado.")

if not df_cot.empty:
    hc=df_cot[df_cot['data']>=now-timedelta(days=365*years)];
    fc=px.line(hc,x='data',y='preco_fechamento',labels={'data':'Ano','preco_fechamento':'Cotação (R$)'},title='Evolução da Cotação'); 
    fc.update_xaxes(tickformat='%Y'); 
    x1=hc['data'].map(datetime.toordinal); 
    t1=np.polyval(np.polyfit(x1,hc['preco_fechamento'],1),x1); 
    fc.add_scatter(x=hc['data'],y=t1,mode='lines',line=dict(color='red',dash='dash'),name='Tendência'); 
    st.plotly_chart(fc,use_container_width=True)
