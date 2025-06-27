import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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

meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
            'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

# Sidebar: configurações e dados do fundo
ticker = st.sidebar.selectbox("FII", sorted(fiis["ticker"]), key="ticker")

# Sidebar: filtros
years_div = st.sidebar.slider(
    "Distribuição de dividendos (Anos)",
    min_value=1,
    max_value=10,    
    value=1,
    key="years_div"
)

years_cot = st.sidebar.slider(
    "Histórico de cotação (Anos)",
    min_value=1,
    max_value=10,
    value=5,
    key="years_cot"
)

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
if not past30.empty:
    past_price = float(past30.iloc[0]['preco_fechamento'])
    delta30 = (price - past_price) / past_price * 100
else:
    delta30 = np.nan
    
# Máx/Min 3M
d3m = df_cot[df_cot['data']>= now-timedelta(days=90)]
high3 = d3m['preco_fechamento'].max() if not d3m.empty else np.nan
low3  = d3m['preco_fechamento'].min() if not d3m.empty else np.nan

# Dividendos
divs = hf[hf['indicador'].str.lower()=='dividendos'].sort_values('data_referencia')
last = get_hist(ticker,'Dividendos')

def DY(meses):
    cutoff = now - relativedelta(months=meses)
    soma = divs.loc[divs['data_referencia'] >= cutoff, 'valor'].sum()
    return soma / price * 100 if price else np.nan

divs_sorted = divs.sort_values('data_referencia', ascending=False)

def DY_last(n):
    """
    Soma os n últimos pagamentos de 'valor' e divide pelo preço atual.
    Mesmo se o mês corrente ainda não tiver pagamento, 
    a função pega o próximo lançamento anterior.
    """
    vals = divs_sorted['valor'].head(n)
    return (vals.sum() / price * 100) if price else np.nan

# Substitua seu DYS por:
DYS = {
    'Atual': DY_last(1),   # último pagamento / preço
    '3M':    DY_last(3),   # soma 3 últimos pagamentos
    '6M':    DY_last(6),
    '12M':   DY_last(12),
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

# Bloco de imóveis
fii_id = int(f["id"])
conn2 = sqlite3.connect(db_path)
imoveis = pd.read_sql("SELECT * FROM fiis_imoveis WHERE fii_id = :fii_id", conn2, params={"fii_id": fii_id})
conn2.close()

if imoveis.empty:
    st.info("Nenhum imóvel cadastrado para este fundo.")
else:
    # Área e vacância
    total_area = imoveis["area_m2"].sum()
    occupied_area = (imoveis["area_m2"] * imoveis["tx_ocupacao"] / 100).sum()
    vacancia_fisica = (1 - occupied_area/total_area)*100 if total_area else np.nan

    # Exibição
    st.markdown(f"**Número de Imóveis:** {len(imoveis)}")
    st.markdown(f"**Vacância Física:** {vacancia_fisica:.2f}%")
    # total de unidades
    total_unidades = imoveis["num_unidades"].sum()
    st.markdown(f"**Total de Unidades:** {total_unidades}")

    # Tabela de imóveis
    st.subheader("Imóveis do Fundo")
    df_imov = (
        imoveis.rename(columns={
            "nome_imovel":"Imóvel","endereco":"Endereço","area_m2":"Área (m²)",
            "num_unidades":"Unidades","tx_ocupacao":"Tx. Ocupação (%)",
            "tx_inadimplencia":"Tx. Inadimplência (%)","pct_receitas":"% Receitas"
        })[["Imóvel","Endereço","Área (m²)","Unidades","Tx. Ocupação (%)","Tx. Inadimplência (%)","% Receitas"]]
    )
    st.dataframe(df_imov)

    # Imóveis que somam 50% das receitas
    sel, cum = [], 0.0
    for _, row in imoveis.sort_values("pct_receitas", ascending=False).iterrows():
        sel.append(row)
        cum += row["pct_receitas"]
        if cum >= 50:
            break
    df50 = pd.DataFrame(sel).rename(columns={"nome_imovel":"Imóvel","pct_receitas":"% Receitas"})[["Imóvel","% Receitas"]]
    if len(df50) > 2:
        st.subheader("Imóveis que representam 50% das Receitas")
        st.dataframe(df50)

col1,col2,col3 = st.columns(3)
col1.markdown("**Preço Atual** <span class='tooltip'>ℹ️<span class='tooltiptext'>Última cotação</span></span>",unsafe_allow_html=True)
col1.metric("",fmt(price), delta=fmt(delta30, 'percentual'))
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
st.subheader(f"Distribuições nos últimos {years_div} anos")

# Destaque dos Dividend Yields
c1, c2, c3, c4 = st.columns(4)
c1.markdown("**YIELD 1 MÊS**");    c1.markdown(f"**{DYS['Atual']:.2f}%**")
c2.markdown("**YIELD 3 MESES**");  c2.markdown(f"**{DYS['3M']:.2f}%**")
c3.markdown("**YIELD 6 MESES**");  c3.markdown(f"**{DYS['6M']:.2f}%**")
c4.markdown("**YIELD 12 MESES**"); c4.markdown(f"**{DYS['12M']:.2f}%**")

for label, n in [('1M',1),('3M',3),('6M',6),('12M',12)]:
    subset = divs_sorted.head(n)
    st.write(f"**Últimos {n} pagamentos ({label}):**")
    st.dataframe(subset[['data_referencia','valor']].rename(
        columns={'data_referencia':'Data','valor':'Valor (R$)'}
    ))

# 1) Filtra só dividendos e converte para timestamp mensal
# Filtra só “Dividendos” e prepara as colunas
df_div = hf[hf['indicador'].str.lower() == 'dividendos'].copy()
df_div['data_referencia'] = pd.to_datetime(df_div['data_referencia'])
df_div['mes'] = df_div['data_referencia'].dt.to_period('M').dt.to_timestamp()
df_div['valor'] = pd.to_numeric(df_div['valor'], errors='coerce')

# Agrupa por mês, soma e ordena
mensal = (
    df_div
    .groupby('mes', as_index=False)['valor']
    .sum()
    .sort_values('mes')
)

# Filtra pelos últimos `years_div` anos
n_meses = years_div * 12
mensal = mensal.sort_values('mes')
hd = mensal.tail(n_meses)

st.subheader(f"Distribuições nos últimos {years_div} anos")
if not hd.empty:
    # gera listagens de tickvals e ticktext
    tickvals = hd['mes']
    ticktext = [f"{meses_pt[d.month-1]}\n{d.year}" for d in hd['mes']]
    # e um customdata para o hover
    hover_labels = [f"{meses_pt[d.month-1]}/{d.year}" for d in hd['mes']]

    fig_div = px.bar(
        hd,
        x='mes',
        y='valor',
        labels={'valor': 'Dividendos (R$)'},
        title=f'Distribuições nos últimos {years_div} anos'
    )
    # substitui o eixo x
    fig_div.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=tickvals,
            ticktext=ticktext
        )
    )
    # customiza o hover para usar o nosso rótulo em PT
    fig_div.update_traces(
        customdata=hover_labels,
        hovertemplate='<b>%{customdata}</b><br>R$ %{y:,.2f}<extra></extra>'
    )
    st.plotly_chart(fig_div, use_container_width=True)

if not df_cot.empty:
    # 1) filtra pelas datas
    hc = df_cot[
        df_cot['data'] >= now - relativedelta(years=years_cot)
    ].copy()

    # 2) monta o gráfico com marcadores
    fig_price = px.line(
        hc,
        x='data',
        y='preco_fechamento',
        labels={'data': 'Data', 'preco_fechamento': 'Cotação (R$)'},
        title=f'Evolução da Cotação ({years_cot} anos)',
        markers=True  # desenha um ponto em cada cotação
    )

    # 3) ajusta o hover para usar dia/mês/ano e valor formatado
    hover_labels = hc['data'].dt.strftime('%d/%m/%Y')
    fig_price.update_traces(
        name='Cotação',    # rótulo na legenda
        customdata=hover_labels,
        hovertemplate='<b>%{customdata}</b><br>R$ %{y:,.2f}<extra></extra>'
    )

    # 4) formata o eixo X para mostrar mês/ano em cada tick
    fig_price.update_xaxes(
        tickformat='%b/%Y',  # ex: Jan/2025
        dtick='M1',          # um tick a cada 1 mês
        tickangle=-45        # inclina o texto pra caber melhor
    )

    # 5) garante que a legenda apareça
    fig_price.update_layout(showlegend=True)

    st.plotly_chart(fig_price, use_container_width=True)
    