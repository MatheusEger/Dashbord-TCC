import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Comparador de FIIs - Iniciante", layout="wide")
# CSS tooltips
st.markdown(
    """
    <style>
    .tooltip{position:relative;display:inline-block;cursor:help}
    .tooltip .tooltiptext{visibility:hidden;width:150px;background:#333;color:#fff;text-align:center;border-radius:4px;padding:5px;position:absolute;z-index:1;bottom:100%;left:50%;transform:translateX(-50%);opacity:0;transition:opacity .3s}
    .tooltip:hover .tooltiptext{visibility:visible;opacity:1}
    </style>
    """, unsafe_allow_html=True)
# Explicação dos Indicadores e Gráficos na sidebar
st.sidebar.header("ℹ️ O que são esses Indicadores?")
st.sidebar.markdown(
    """
    **Preço Atual**: último preço de fechamento.\n  
    **PL (Patrimônio Líquido)**: valor dos ativos do fundo menos seus passivos.\n
    **Quantidade Cotas**: total de cotas emitidas pelo fundo.\n
    **VPA**: valor patrimonial por cota = PL ÷ quantidade de cotas.\n  
    **P/VP**: relação preço de mercado ÷ VPA.\n  
    **DY 12M**: soma de dividendos pagos nos últimos 12 meses ÷ preço atual.\n  
    **Cotação Semanal**: evolução do preço, última cotação de cada semana.\n  
    **Dividendos 12 Meses**: soma de dividendos mensais nos últimos 12 meses.  
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>📑 Comparador de Fundos Imobiliários</h1>", unsafe_allow_html=True)

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "fiis.db"
with sqlite3.connect(DB_PATH) as conn:
    fiis = pd.read_sql("SELECT id, ticker, nome, gestao, admin, setor_id FROM fiis", conn)
    setores = pd.read_sql("SELECT id, nome FROM setor", conn)
    cot = pd.read_sql("SELECT fii_id, data, preco_fechamento FROM cotacoes", conn, parse_dates=['data'])
    inds = pd.read_sql(
        """
        SELECT fi.fii_id, i.nome AS indicador, fi.valor, fi.data_referencia
        FROM fiis_indicadores fi
        JOIN indicadores i ON fi.indicador_id = i.id
        """, conn, parse_dates=['data_referencia']
    )

def prepare(ticker):
    row = fiis[fiis['ticker']==ticker].iloc[0]
    setor = setores.set_index('id').loc[row['setor_id'], 'nome'] if row['setor_id'] in setores['id'].values else 'N/A'
    df_ind = inds[inds['fii_id']==row['id']].copy()
    df_ind.set_index('data_referencia', inplace=True)
    pl = None
    if 'Patrimônio Líquido' in df_ind['indicador'].values:
        pl = float(df_ind[df_ind['indicador']=='Patrimônio Líquido']['valor'].iloc[-1])
    cotas = None
    if 'Quantidade de Cotas' in df_ind['indicador'].values:
        cotas = float(df_ind[df_ind['indicador']=='Quantidade de Cotas']['valor'].iloc[-1])
    df_price = cot[cot['fii_id']==row['id']]
    price = df_price.sort_values('data')['preco_fechamento'].iloc[-1] if not df_price.empty else None
    vpa = pl/cotas if pl and cotas else None
    pvp = price/vpa if price and vpa else None
    one_year_ago = datetime.now() - relativedelta(years=1)
    divs = df_ind[df_ind['indicador']=='Dividendos']
    dy12 = None
    if price and not divs.empty:
        dy12 = divs[divs.index>=one_year_ago]['valor'].sum()/price*100
    return row, setor, pl, cotas, price, vpa, pvp, dy12, df_price, df_ind

col1, col2 = st.columns(2)
f1 = col1.selectbox("Selecione Fundo 1", fiis['ticker'].sort_values(), key='f1')
f2 = col2.selectbox("Selecione Fundo 2", fiis['ticker'].sort_values(), index=1, key='f2')

data1 = prepare(f1)
data2 = prepare(f2)

for c, data in zip([col1, col2], [data1, data2]):
    row, setor, pl, cotas, price, vpa, pvp, dy12, df_price, df_ind = data
    c.markdown(f"### {row['ticker']} — {row['nome']}")
    c.markdown(f"**Setor:** {setor}  &nbsp; **Gestora:** {row['gestao']}  &nbsp; **Admin:** {row['admin']}")
    # Métricas principais organizadas em duas linhas de três colunas
    # Função para formatar valores grandes
    def human_format(num):
        if num is None:
            return "N/A"
        magnitude = 0
        for unit in ['',' mil',' Mi',' Bi']:
            if abs(num) < 1000.0:
                return f"{num:,.2f}{unit}"
            num /= 1000.0
        return f"{num:,.2f} Bi"

    row1 = c.columns(3)
    # Tooltips nos indicadores
    row1[0].markdown("<div class='tooltip'>Preço Atual ℹ️<span class='tooltiptext'>Último preço de fechamento</span></div>", unsafe_allow_html=True)
    row1[0].metric(label="", value=f"R$ {price:,.2f}" if price else "N/A")
    row1[1].markdown("<div class='tooltip'>Patrimônio Líquido ℹ️<span class='tooltiptext'>Valor dos ativos do fundo menos passivos</span></div>", unsafe_allow_html=True)
    row1[1].metric(label="", value=f"R$ {human_format(pl)}" if pl else "N/A")
    row1[2].markdown("<div class='tooltip'>Quantidade Cotas ℹ️<span class='tooltiptext'>Total de cotas emitidas</span></div>", unsafe_allow_html=True)
    row1[2].metric(label="", value=f"{human_format(cotas)}" if cotas else "N/A")
    row2 = c.columns(3)
    # Tooltips segunda linha
    row2[0].markdown("<div class='tooltip'>VPA ℹ️<span class='tooltiptext'>Valor patrimonial por cota (PL ÷ Cotas)</span></div>", unsafe_allow_html=True)
    row2[0].metric(label="", value=f"R$ {vpa:,.2f}" if vpa else "N/A")
    row2[1].markdown("<div class='tooltip'>P/VP ℹ️<span class='tooltiptext'>Preço de mercado ÷ VPA</span></div>", unsafe_allow_html=True)
    row2[1].metric(label="", value=f"{pvp:.2f}x" if pvp else "N/A")
    row2[2].markdown("<div class='tooltip'>DY 12M ℹ️<span class='tooltiptext'>Dividend Yield últimos 12 meses</span></div>", unsafe_allow_html=True)
    row2[2].metric(label="", value=f"{dy12:.2f}%" if dy12 else "N/A")
    c.markdown("---")
    # Gráficos empilhados verticalmente
    # Cotação Semanal
    if not df_price.empty:
        df_week = df_price.set_index('data').resample('W-FRI')['preco_fechamento'].last().reset_index()
        fig1 = px.line(df_week, x='data', y='preco_fechamento', title='Cotação Semanal', labels={'data':'Data','preco_fechamento':'R$'})
        c.plotly_chart(fig1, use_container_width=True)
    # Dividendos 12 Meses
    if not df_ind[df_ind['indicador']=='Dividendos'].empty:
        df_div = df_ind[df_ind['indicador']=='Dividendos'].copy()
        df_div['mes'] = df_div.index.to_period('M').to_timestamp()
        mensal = df_div.groupby('mes')['valor'].sum().reset_index()
        fig2 = px.bar(mensal.tail(12), x='mes', y='valor', title='Dividendos 12 Meses', labels={'mes':'Mês/Ano','valor':'R$'})
        c.plotly_chart(fig2, use_container_width=True)
    c.markdown("---")

st.markdown("<p style='text-align:center;color:#888;'>Dados extraídos de fiis.db</p>", unsafe_allow_html=True)
