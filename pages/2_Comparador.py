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

# +++ Slider de período para dividendos +++
years_div = st.sidebar.slider("Período de Dividendos (anos)", 1, 10, 1)

# Slider de período para cotação na sidebar
years_cot = st.sidebar.slider("Período da Cotação (anos)", 1, 10, 5)


# Explicação dos Indicadores e Gráficos na sidebar
st.sidebar.header("ℹ️ O que são esses Indicadores?")
st.sidebar.markdown(
    """
    **Preço Atual**: último preço de fechamento.  
    **PL (Patrimônio Líquido)**: valor dos ativos do fundo menos seus passivos.  
    **Quantidade Cotas**: total de cotas emitidas pelo fundo.  
    **VPA**: valor patrimonial por cota = PL ÷ quantidade de cotas.  
    **P/VP**: relação preço de mercado ÷ VPA.  
    **DY 12M**: soma de dividendos pagos nos últimos 12 meses ÷ preço atual.  
    **Cotação Semanal**: evolução do preço, última cotação de cada semana.  
    **Dividendos 12 Meses**: soma de dividendos mensais nos últimos 12 meses.  
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>📑 Comparador de Fundos Imobiliários</h1>", unsafe_allow_html=True)

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "fiis.db"
with sqlite3.connect(DB_PATH) as conn:
    fiis = pd.read_sql("SELECT id, ticker, nome, gestao, admin, setor_id FROM fiis WHERE ativo = 1", conn)    
    setores = pd.read_sql("SELECT id, nome FROM setor", conn)
    cot = pd.read_sql("SELECT fii_id, data, preco_fechamento FROM cotacoes", conn, parse_dates=['data'])
    inds = pd.read_sql(
        """
        SELECT fi.fii_id, i.nome AS indicador, fi.valor, fi.data_referencia
        FROM fiis_indicadores fi
        JOIN indicadores i ON fi.indicador_id = i.id
        """, conn, parse_dates=['data_referencia']
    )

def prepare(ticker, years_div):
    dy = 0.0
    row = fiis[fiis['ticker']==ticker].iloc[0]
    setor = setores.set_index('id').loc[row['setor_id'], 'nome'] \
               if row['setor_id'] in setores['id'].values else 'N/A'
    df_ind = inds[inds['fii_id']==row['id']].copy()
    df_ind.set_index('data_referencia', inplace=True)
    df_ind = inds[inds['fii_id']==row['id']].copy()
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
    one_period_ago = datetime.now() - relativedelta(years=years_div)

    # filtra dividendos daquele ticker e período
    divs_all = df_ind[
        (df_ind['indicador'] == 'Dividendos') &
        (df_ind['data_referencia'] >= one_period_ago)
    ]

    if price and not divs_all.empty:
         dy = divs_all['valor'].sum() / price * 100

    # … cálculos de pl, cotas, price, vpa, pvp, df_price, df_ind …
    return row, setor, pl, cotas, price, vpa, pvp, dy, df_price, df_ind

setores_validos = setores[setores['id'].isin(fiis['setor_id'])]
setor_names    = sorted(setores_validos['nome'].unique())
selected_setor = st.selectbox("Selecione o Setor", setor_names)

# 2) Descobre o ID do setor e filtra os FIIs ativos daquele setor
setor_id = setores_validos.loc[setores_validos['nome'] == selected_setor, 'id'].iloc[0]
fiis_setor = fiis[fiis['setor_id'] == setor_id]

# ── Agora, na área principal, crie as duas colunas:
col1, col2 = st.columns(2)

f1 = col1.selectbox(
    "Selecione Fundo 1",
    fiis_setor['ticker'].sort_values(),
    key='f1'
)

tickers_f2 = fiis_setor.loc[fiis_setor['ticker'] != f1, 'ticker'].sort_values()
f2 = col2.selectbox(
    "Selecione Fundo 2",
    tickers_f2,
    key='f2'
)

data1 = prepare(f1, years_div)
data2 = prepare(f2, years_div)

for c, data in zip([col1, col2], [data1, data2]):
    row, setor, pl, cotas, price, vpa, pvp, dy, df_price, df_ind = data
    c.markdown(f"### {row['ticker']} — {row['nome']}")
    c.markdown(
        f"**Setor:** {setor}  &nbsp; "
        f"**Gestora:** {row['gestao']}  &nbsp; "
        f"**Admin:** {row['admin']}"
    )

    # função human_format como você já tinha
    def human_format(num):
        if num is None: return "N/A"
        magnitude = 0
        for unit in ['', ' mil', ' Mi', ' Bi']:
            if abs(num) < 1000.0:
                return f"{num:,.2f}{unit}"
            num /= 1000.0
        return f"{num:,.2f} Bi"

    # 1ª linha: Preço Atual / Patrimônio Líquido
    r1 = c.columns(2)
    r1[0].markdown(
        "<div class='tooltip'>Preço Atual ℹ️"
        "<span class='tooltiptext'>Último preço de fechamento</span></div>",
        unsafe_allow_html=True
    )
    r1[0].metric(label="", value=f"R$ {price:,.2f}" if price else "N/A")
    r1[1].markdown(
        "<div class='tooltip'>Patrimônio Líquido ℹ️"
        "<span class='tooltiptext'>Ativos menos passivos</span></div>",
        unsafe_allow_html=True
    )
    r1[1].metric(label="", value=f"R$ {human_format(pl)}" if pl else "N/A")

    # 2ª linha: Quantidade Cotas / VPA
    r2 = c.columns(2)
    r2[0].markdown(
        "<div class='tooltip'>Quantidade Cotas ℹ️"
        "<span class='tooltiptext'>Total de cotas emitidas</span></div>",
        unsafe_allow_html=True
    )
    r2[0].metric(label="", value=f"{human_format(cotas)}" if cotas else "N/A")
    r2[1].markdown(
        "<div class='tooltip'>VPA ℹ️"
        "<span class='tooltiptext'>Valor patrimonial por cota (PL ÷ Cotas)</span></div>",
        unsafe_allow_html=True
    )
    r2[1].metric(label="", value=f"R$ {vpa:,.2f}" if vpa else "N/A")

    # 3ª linha: P/VP / DY
    r3 = c.columns(2)
    r3[0].markdown(
        "<div class='tooltip'>P/VP ℹ️"
        "<span class='tooltiptext'>Preço de mercado ÷ VPA</span></div>",
        unsafe_allow_html=True
    )
    r3[0].metric(label="", value=f"{pvp:.2f}%" if pvp else "N/A")
    with sqlite3.connect(DB_PATH) as conn_im:
        df_qt = pd.read_sql(
        "SELECT COUNT(*) AS qtd FROM fiis_imoveis WHERE fii_id = ?",
        conn_im,
        params=(int(row["id"]),),
    )
    qtd_imoveis = int(df_qt["qtd"].iloc[0]) if not df_qt.empty else 0

    if qtd_imoveis > 0:
        # exibe Número de Imóveis
        r3[1].markdown(
            "<div class='tooltip'>Número de Imóveis ℹ️"
            "<span class='tooltiptext'>Total de imóveis no portfólio do fundo</span></div>",
            unsafe_allow_html=True
        )
    r3[1].metric(label="", value=f"{qtd_imoveis}")

    c.markdown("---")

    # Gráficos empilhados verticalmente
    # Cotação Semanal
    if not df_price.empty:
        cutoff = datetime.now() - relativedelta(years=years_cot)
        df_week = df_price[df_price['data']>=cutoff] \
            .set_index('data') \
            .resample('W-FRI')['preco_fechamento'] \
            .last() \
            .reset_index()
        fig1 = px.line(
            df_week,
            x='data',
            y='preco_fechamento',
            title='Cotação Semanal',
            labels={'data':'Ano','preco_fechamento':'R$'}
        )
        fig1.update_xaxes(tickformat='%Y', dtick='M12')
                # aumenta espessura da linha para maior nitidez
        fig1.update_traces(line=dict(width=3), selector=dict(type='scatter'))
        c.plotly_chart(fig1, use_container_width=True)

    # Dividendos 12 Meses
    if not df_ind[df_ind['indicador']=='Dividendos'].empty:
        df_div = df_ind[df_ind['indicador']=='Dividendos'].copy()
        # usa a coluna data_referencia para extrair mês
        df_div['mes'] = pd.to_datetime(df_div['data_referencia']).dt.to_period('M').dt.to_timestamp()
        mensal = df_div.groupby('mes')['valor'].sum().reset_index()
        fig2 = px.bar(
            mensal.sort_values('mes').tail(12),
            x='mes',
            y='valor',
            title='Dividendos 12 Meses',
            labels={'mes': 'Mês/Ano', 'valor': 'R$'}
        )
        fig2.update_xaxes(tickformat='%b/%Y', dtick='M1', tickangle=-45)
        c.plotly_chart(fig2, use_container_width=True)

    # 1) Seção Imóveis
    c.subheader("Imóveis")
    fii_id = int(row["id"])  # usa row, não 'f'

    # 2) Consulta ao banco
    with sqlite3.connect(DB_PATH) as conn_im:
        df_imoveis = pd.read_sql(
            """
            SELECT area_m2,
                   num_unidades,
                   tx_ocupacao
            FROM fiis_imoveis
            WHERE fii_id = ?
            """,
            conn_im,
            params=(fii_id,),
        )

    # 3) Exibe ou informação de ausência de dados
    if df_imoveis.empty:
        c.info("Nenhum dado de imóveis disponível para este fundo.")
    else:
        total_imoveis  = len(df_imoveis)
        total_unidades = df_imoveis["num_unidades"].sum()
        total_area     = df_imoveis["area_m2"].sum()
        weighted_ocup  = (df_imoveis["area_m2"] * df_imoveis["tx_ocupacao"]).sum() / total_area
        vac_phys       = 100 - weighted_ocup

        # 4) Formata a área em BR
        area_str = (
            f"{total_area:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        # 5) Duas métricas por linha
        # primeira linha: Total de imóveis + Total de unidades
        r1c1, r1c2 = c.columns(2)
        r1c1.markdown(
            "<div class='tooltip'>Total de imóveis ℹ️"
            "<span class='tooltiptext'>Número total de imóveis que compõem o portfólio do fundo</span></div>",
            unsafe_allow_html=True
        )
        r1c1.metric(label="", value=total_imoveis)

        r1c2.markdown(
            "<div class='tooltip'>Total de unidades ℹ️"
            "<span class='tooltiptext'>Soma de todas as unidades habitacionais/comerciais</span></div>",
            unsafe_allow_html=True
        )
        r1c2.metric(label="", value=total_unidades)

        # segunda linha: Área total + Vacância Física
        r2c1, r2c2 = c.columns(2)
        r2c1.markdown(
            "<div class='tooltip'>Área total (m²) ℹ️"
            "<span class='tooltiptext'>Total da área em metros quadrados de todos os imóveis</span></div>",
            unsafe_allow_html=True
        )
        r2c1.metric(label="", value=area_str)

        r2c2.markdown(
            "<div class='tooltip'>Vacância Física (%) ℹ️"
            "<span class='tooltiptext'>Percentual de área vaga calculado como 100% menos a ocupação ponderada</span></div>",
            unsafe_allow_html=True
        )
        r2c2.metric(label="", value=f"{vac_phys:.2f}%")

