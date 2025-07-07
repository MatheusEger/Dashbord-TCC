import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go  # no topo do arquivo

st.set_page_config(page_title="Comparador de FIIs - Iniciante", page_icon="⚖️", layout="wide")
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
years_div = 1 #st.sidebar.slider("Período de Dividendos (anos)", 1, 10, 1)

# Slider de período para cotação na sidebar
years_cot = st.sidebar.slider("Período da Cotação (anos)", 1, 10, 5)


# Explicação dos Indicadores e Gráficos na sidebar
st.sidebar.header("ℹ️ O que são esses Indicadores e Gráficos?")
st.sidebar.markdown(r"""
- **Preço Atual**: É o valor mais recente pelo qual a cota do fundo foi negociada na Bolsa.  
  *Ou seja: é quanto você pagaria para comprar 1 cota do fundo hoje.*

- **Patrimônio Líquido (PL)**: Mostra o valor total que o fundo possui, somando todos os imóveis, títulos e o dinheiro em caixa, já descontando as dívidas.  
  *Serve para saber o "tamanho" do fundo, como se fosse o valor de todo o patrimônio de um condomínio.*

- **Quantidade de Cotas**: É o número total de "pedaços" (cotas) em que o fundo foi dividido.  
  *Se o fundo fosse uma pizza, cada fatia seria uma cota. Quanto mais cotas, mais investidores podem participar.*

- **Valor Patrimonial por Cota (VPA)**: Indica quanto vale cada cota em relação ao patrimônio do fundo.  
  *Exemplo: Se o fundo tem R\$ 100 milhões e 1 milhão de cotas, cada cota “vale” R\$ 100.*

- **Preço/VPA (P/VP)**: Mostra se a cota está barata ou cara comparada ao seu valor real.
  - *Se P/VP < 1 (Desconto):* você compra a cota por menos do que ela realmente vale. Exemplo: P/VP = 0,90 → você paga R\$ 0,90 por cada R\$ 1,00 de valor do fundo.
  - *Se P/VP > 1 (Ágio):* você paga mais do que a cota vale no fundo. Exemplo: P/VP = 1,10 → você paga R\$ 1,10 para cada R\$ 1,00 de valor patrimonial.

- **Dividend Yield 12M (DY 12M)**: Mostra a porcentagem de rendimento que o fundo pagou em dividendos (aluguéis e rendimentos) nos últimos 12 meses, comparando com o preço atual da cota.  
  *Exemplo: Se você tem uma cota que custa R\$ 100 e recebeu R\$ 8 de dividendos no ano, o DY é 8%.*

- **Cotação Semanal**: Um gráfico mostrando como o preço da cota mudou semana a semana. Ajuda a perceber se o valor está subindo ou caindo ao longo do tempo.

- **Dividendos nos Últimos 12 Meses**: Mostra, em gráfico, o total de dividendos pagos mês a mês durante o último ano.  
  *Assim, você pode ver em quais meses o fundo pagou mais ou menos rendimento.*

- **Cap Rate**: (quando disponível) Mostra quanto o fundo recebe de aluguel por ano em relação ao valor dos imóveis que ele possui.  
  *Exemplo: Se um fundo tem imóveis que valem R\$ 200 mil e recebe R\$ 10 mil de aluguel por ano, o Cap Rate é 5%. Ajuda a comparar qual fundo gera mais renda com seus imóveis.*
""", unsafe_allow_html=True)


st.markdown("<h1 style='text-align:center;'>📑 Comparador de Fundos Imobiliários</h1>", unsafe_allow_html=True)

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "fiis.db"
with sqlite3.connect(DB_PATH) as conn:
    # 1) carrega FIIs e demais tabelas
    fiis    = pd.read_sql("SELECT id, ticker, nome, gestao, admin, setor_id, tipo_id FROM fiis WHERE ativo = 1", conn)
    setores = pd.read_sql("SELECT id, nome FROM setor", conn)
    cot    = pd.read_sql("SELECT fii_id, data, preco_fechamento FROM cotacoes", conn, parse_dates=['data'])
    inds   = pd.read_sql(
        """
        SELECT fi.fii_id, i.nome AS indicador, fi.valor, fi.data_referencia
        FROM fiis_indicadores fi
        JOIN indicadores i ON fi.indicador_id = i.id
        """, conn, parse_dates=['data_referencia']
    )

    # ───> aqui, carregue também a tabela de tipos:
    tipos = pd.read_sql(
        "SELECT id AS tipo_id, nome AS tipo, descricao AS tipo_desc FROM tipo_fii",
        conn
    )

# 2) faça o merge de tipos com o DataFrame de FIIs
fiis = fiis.merge(tipos, on="tipo_id", how="left")
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
    # --- Cap Rate ---
    cap_rate = None
    if 'Cap Rate' in df_ind['indicador'].values:
        cap_rate = float(df_ind[df_ind['indicador']=='Cap Rate']['valor'].iloc[-1])
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

    # Agora retorna cap_rate também
    return row, setor, pl, cotas, price, vpa, pvp, dy, cap_rate, df_price, df_ind

# lista de tipos e setores para cada coluna
tipo_names = tipos['tipo'].tolist()

# cria duas colunas para filtros
fcol1, fcol2 = st.columns(2)

with fcol1:
    selected_tipo1 = st.selectbox(
        "Selecione o Tipo (Fundo 1)",
        tipo_names,
        key="tipo1"
    )
    # filtra setores válidos para o tipo 1
    setores1 = setores[setores['id'].isin(
        fiis[fiis['tipo']==selected_tipo1]['setor_id']
    )]
    setor_names1 = sorted(setores1['nome'].unique())
    selected_setor1 = st.selectbox(
        "Selecione o Setor (Fundo 1)",
        setor_names1,
        key="setor1"
    )
    # FIIs para o primeiro filtro
    fiis1 = fiis[
        (fiis['tipo']==selected_tipo1) &
        (fiis['setor_id']==setores1.loc[setores1['nome']==selected_setor1,'id'].iloc[0])
    ]

with fcol2:
    # inicializa com mesmo valor do filtro 1
    default_idx = tipo_names.index(selected_tipo1)
    selected_tipo2 = st.selectbox(
        "Selecione o Tipo (Fundo 2)",
        tipo_names,
        index=default_idx,
        key="tipo2"
    )
    setores2 = setores[setores['id'].isin(
        fiis[fiis['tipo']==selected_tipo2]['setor_id']
    )]
    setor_names2 = sorted(setores2['nome'].unique())
    # define índice padrão igual ao selecionado em setor1, se existir
    default_set_idx = (
        setor_names2.index(selected_setor1)
        if selected_setor1 in setor_names2 else 0
    )
    selected_setor2 = st.selectbox(
        "Selecione o Setor (Fundo 2)",
        setor_names2,
        index=default_set_idx,
        key="setor2"
    )
    fiis2 = fiis[
        (fiis['tipo']==selected_tipo2) &
        (fiis['setor_id']==setores2.loc[setores2['nome']==selected_setor2,'id'].iloc[0])
    ]

# agora cada coluna de fundos filtra a partir dos seus próprios fiis1 e fiis2
col1, col2 = st.columns(2)
# converte para listas ordenadas
tickers1 = fiis1['ticker'].sort_values().tolist()
tickers2 = fiis2['ticker'].sort_values().tolist()

# Fundo 1
f1 = col1.selectbox(
    "Selecione Fundo 1",
    tickers1,
    key='f1'
)

# calcula índice padrão para Fundo 2: próximo ao selecionado em f1
if f1 in tickers2 and len(tickers2) > 1:
    idx1 = tickers2.index(f1)
    default_idx2 = idx1 + 1 if idx1 + 1 < len(tickers2) else 0
else:
    default_idx2 = 0

# Fundo 2 já herda o próximo da lista por padrão
f2 = col2.selectbox(
    "Selecione Fundo 2",
    tickers2,
    index=default_idx2,
    key='f2'
)

data1 = prepare(f1, years_div)
data2 = prepare(f2, years_div)

# --- após calcular price, pl, cotas, vpa, pvp e qtd_imoveis para C1 e C2 ---
# desempacota os retornos para o Fundo 1
row1, setor1, pl1, cotas1, price1, vpa1, pvp1, dy1, cap_rate1, df_price1, df_ind1 = data1
row2, setor2, pl2, cotas2, price2, vpa2, pvp2, dy2, cap_rate2, df_price2, df_ind2 = data2

with sqlite3.connect(DB_PATH) as conn_im:
    df_qt1 = pd.read_sql(
        "SELECT COUNT(*) AS qtd FROM fiis_imoveis WHERE fii_id = ?",
        conn_im,
        params=(int(row1["id"]),)
    )
    qtd_imoveis1 = int(df_qt1["qtd"].iloc[0]) if not df_qt1.empty else 0

    df_qt2 = pd.read_sql(
        "SELECT COUNT(*) AS qtd FROM fiis_imoveis WHERE fii_id = ?",
        conn_im,
        params=(int(row2["id"]),)
    )
    qtd_imoveis2 = int(df_qt2["qtd"].iloc[0]) if not df_qt2.empty else 0

# funções de formatação genérica
def human_format(num):
    if num is None:
        return "N/A"
    for unit in ['', ' mil', ' Mi', ' Bi']:
        if abs(num) < 1000.0:
            return f"{num:,.2f}{unit}"
        num /= 1000.0
    return f"{num:,.2f} Bi"

def fmt_val(label, v):
    if v is None:
        return "N/A"
    
    # R$ com duas casas e vírgula decimal
    if label in ["Preço Atual", "VPA"]:
        s = f"{v:,.2f}"              # ex: "1,234.56"
        s = s.replace(",", "#")      # "1#234.56"
        s = s.replace(".", ",")      # "1#234,56"
        s = s.replace("#", ".")      # "1.234,56"
        return f"R$ {s}"
    
    # formata grandes números com sufixos e vírgula
    if label in ["Patrimônio Líquido (PL)", "Quantidade Cotas"]:
        s = human_format(v)          # ex: "1,23 Mi"
        return s.replace(".", ",")   # ex: "1,23 Mi" → "1,23 Mi"
    
    # P/VP com 2 decimais e vírgula decimal
    if label == "P/VP":
        s = f"{v:.2f}"               # ex: "0.86"
        return s.replace(".", ",")   # "0,86"
    
    # Número de Imóveis como inteiro (opcional), com vírgula se quiser
    if label == "Número de Imóveis":
        return f"{int(v)}"
    
    # fallback genérico
    return str(v)

# lista de tuplas: (label, função de comparação: True se v1 melhor que v2)
metrics = [
    ("Preço Atual",               lambda a, b: a > b),
    ("Patrimônio Líquido (PL)",   lambda a, b: a > b),
    ("Quantidade Cotas",          lambda a, b: a > b),
    ("VPA",                       lambda a, b: a > b),
    ("P/VP",                      lambda a, b: a < b),  # menor = melhor
    ("Número de Imóveis",         lambda a, b: a > b),
    ("Cap Rate",                  lambda a, b: (a or 0) > (b or 0)),  # maior = melhor, só se houver
]

# extraia os valores em dois dicionários
values1 = {
    "Preço Atual":            price1,
    "Patrimônio Líquido (PL)": pl1,
    "Quantidade Cotas":       cotas1,
    "VPA":                    vpa1,
    "P/VP":                   pvp1,
    "Número de Imóveis":      qtd_imoveis1,
    "Cap Rate":               cap_rate1,
}
values2 = {
    "Preço Atual":            price2,
    "Patrimônio Líquido (PL)": pl2,
    "Quantidade Cotas":       cotas2,
    "VPA":                    vpa2,
    "P/VP":                   pvp2,
    "Número de Imóveis":      qtd_imoveis2,
    "Cap Rate":               cap_rate2,
}


# pré-calcule os troféus para não ter que rodar lambda dentro do loop de renderização
trofeus1 = {lbl: " 🏆" if cmp(values1[lbl], values2[lbl]) else "" for lbl, cmp in metrics}
trofeus2 = {lbl: " 🏆" if cmp(values2[lbl], values1[lbl]) else "" for lbl, cmp in metrics}

rows      = [row1,        row2]
values    = [values1,     values2]
trofeus   = [trofeus1,    trofeus2]
dfs_price = [df_price1,   df_price2]
dfs_ind   = [df_ind1,     df_ind2]

col_f1, col_f2 = st.columns(2)
for idx, c in enumerate([col_f1, col_f2]):
    row      = rows[idx]
    vals     = values[idx]
    trofs    = trofeus[idx]
    df_price = dfs_price[idx]
    df_ind   = dfs_ind[idx]

    # agora, quando for buscar imóveis:
    with sqlite3.connect(DB_PATH) as conn_im:
        df_qt = pd.read_sql(
            "SELECT COUNT(*) AS qtd FROM fiis_imoveis WHERE fii_id = ?",
            conn_im,
            params=(int(row["id"]),),  # <-- row está definido!
        )
        qtd_imoveis = int(df_qt["qtd"].iloc[0]) if not df_qt.empty else 0

    # 1ª linha: Preço Atual / Patrimônio Líquido
    r1 = c.columns(2)
    r1[0].markdown(
        "<div class='tooltip'>Preço Atual ℹ️"
        "<span class='tooltiptext'>Último preço de fechamento</span></div>",
        unsafe_allow_html=True
    )
    r1[0].metric(label="",
                 value=fmt_val("Preço Atual", vals["Preço Atual"]) + trofs["Preço Atual"])
    r1[1].markdown(
        "<div class='tooltip'>Patrimônio Líquido (PL) ℹ️"
        "<span class='tooltiptext'>Ativos menos passivos</span></div>",
        unsafe_allow_html=True
    )
    r1[1].metric(label="",
                 value=fmt_val("Patrimônio Líquido (PL)", vals["Patrimônio Líquido (PL)"]) 
                       + trofs["Patrimônio Líquido (PL)"])

    # 2ª linha: Quantidade Cotas / VPA
    r2 = c.columns(2)
    r2[0].markdown(
        "<div class='tooltip'>Quantidade Cotas ℹ️"
        "<span class='tooltiptext'>Total de cotas emitidas</span></div>",
        unsafe_allow_html=True
    )
    r2[0].metric(label="",
                 value=fmt_val("Quantidade Cotas", vals["Quantidade Cotas"]) 
                       + trofs["Quantidade Cotas"])
    r2[1].markdown(
        "<div class='tooltip'>VPA ℹ️"
        "<span class='tooltiptext'>Valor patrimonial por cota (PL ÷ Cotas)</span></div>",
        unsafe_allow_html=True
    )
    r2[1].metric(label="",
                 value=fmt_val("VPA", vals["VPA"]) + trofs["VPA"])

    # 3ª linha: P/VP / Número de Imóveis
    r3 = c.columns(2)
    r3[0].markdown(
        "<div class='tooltip'>P/VP ℹ️"
        "<span class='tooltiptext'>Preço de mercado ÷ VPA</span></div>",
        unsafe_allow_html=True
    )
    r3[0].metric(label="",
                 value=fmt_val("P/VP", vals["P/VP"]) + trofs["P/VP"])
    # se quiser repetir a lógica condicional pra imóveis, mantenha como antes
    if vals["Número de Imóveis"] > 0:
        r3[1].markdown(
            "<div class='tooltip'>Número de Imóveis ℹ️"
            "<span class='tooltiptext'>Total de imóveis no portfólio do fundo</span></div>",
            unsafe_allow_html=True
        )
        r3[1].metric(
            label="",
            value=fmt_val("Número de Imóveis", vals["Número de Imóveis"]) 
                + trofs["Número de Imóveis"]
        )
    # Exibe Cap Rate somente se houver pelo menos um valor diferente de None
    if vals["Cap Rate"] is not None:
        c.markdown(
            "<div class='tooltip'>Cap Rate ℹ️"
            "<span class='tooltiptext'>Taxa de capitalização anual do fundo (Receita Anual de Aluguéis ÷ Valor de Mercado dos Imóveis)</span></div>",
            unsafe_allow_html=True
        )
        cap_rate_fmt = f"{vals['Cap Rate']:.2f}%" if vals['Cap Rate'] is not None else "N/A"
        c.metric(
            label="",
            value=cap_rate_fmt + trofs.get("Cap Rate", "")
        )

    c.markdown("---")

    # Gráficos empilhados verticalmente
    # Cotação Semanal
    if not df_price.empty:
        # data mínima disponível para este fundo
        data_min = df_price['data'].min()

        # determina cutoff: anos atrás, mas não antes do primeiro dado
        cutoff_user = datetime.now() - relativedelta(years=years_cot)
        cutoff = max(cutoff_user, data_min)

        # filtra pelo período ajustado
        df_filtered = df_price[df_price['data'] >= cutoff]

        if df_filtered.empty:
            c.info("Sem dados de cotação para o período selecionado.")
        else:
            # resample semanal genérico e descarta NaN
            df_week = (
                df_filtered
                .set_index('data')
                .resample('W')['preco_fechamento']
                .last()
                .dropna()
                .reset_index()
            )

            if df_week.empty:
                c.info("Não há cotações semanais suficientes para plotar o gráfico.")
            else:
                x = df_week['data'].map(pd.Timestamp.toordinal).values
                y = df_week['preco_fechamento'].values
                m, b = np.polyfit(x, y, 1)
                trend_y = m * x + b

                fig1 = px.line(
                    df_week,
                    x='data',
                    y='preco_fechamento',
                    title='Cotação Semanal',
                    labels={'data':'Data','preco_fechamento':'R$'}
                )
                fig1.update_xaxes(
                    tickformat='%Y',    # mostra apenas o ano
                    dtick='M12',        # passo de um tick a cada 12 meses
                    ticklabelmode='period'  # garante que o rótulo seja o início de cada período
                )                
                fig1.update_traces(line=dict(width=3), selector=dict(type='scatter'))

                fig1.add_trace(
                    go.Scatter(
                        x=df_week['data'],
                        y=trend_y,
                        mode='lines',
                        name='Tendência',
                        line=dict(color='red', dash='dash', width=2)  # aqui o color='red'
                    )
                )
                fig1.data[0].name = "Cotação Semanal"
                fig1.data[1].name = "Tendência"

                # nova configuração de legenda
                fig1.update_layout(
                    legend=dict(
                        title_text="",            # sem título
                        orientation="h",          # legenda horizontal
                        x=1,                    # centralizada
                        y=1.10,                   # acima do gráfico
                        xanchor="center",
                        yanchor="bottom",
                        bgcolor="rgba(255,255,255,0.6)",  # fundo semitransparente
                        bordercolor="black",
                        borderwidth=1,
                        font=dict(size=11)
                    ),
                    margin=dict(t=80, b=40, l=40, r=40)  # espaço extra no topo
                )

                c.plotly_chart(
                    fig1,
                    use_container_width=True,
                    key=f"cotacao_semanal_{idx}"
                )
                                
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
        c.plotly_chart(
            fig2,
            use_container_width=True,
            key=f"dividendos_12m_{idx}"
        )

            # 1) Seção Imóveis
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

    # Só exibe a seção se houver dados
    if not df_imoveis.empty:
        c.subheader("Imóveis")

        total_imoveis  = len(df_imoveis)
        total_unidades = df_imoveis["num_unidades"].sum()
        total_area     = df_imoveis["area_m2"].sum()
        weighted_ocup  = (df_imoveis["area_m2"] * df_imoveis["tx_ocupacao"]).sum() / total_area
        vac_phys       = 100 - weighted_ocup

    # formata área
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

