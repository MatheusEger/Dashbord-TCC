import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from dateutil.relativedelta import relativedelta

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard de FIIs", layout="wide")

# --- Caminho do banco de dados ---
DB_PATH = Path(__file__).resolve().parent / "data" / "fiis.db"

# --- Carregamento dos dados ---
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
    conn,
    parse_dates=['data']
)

inds = pd.read_sql_query(
    """
    SELECT fi.fii_id, i.nome AS indicador, fi.valor, fi.data_referencia
    FROM fiis_indicadores fi
    JOIN indicadores i ON i.id = fi.indicador_id
    """,
    conn,
    parse_dates=['data_referencia']
)
conn.close()

# --- Preparação do DataFrame principal ---
df = df_meta.copy()

def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- Aviso Legal no topo ---
st.warning(
    """
    ⚠️ **Aviso Legal:**  
    Este dashboard **não fornece recomendações de investimento**.  
    Exibe apenas métricas de mercado obtidas de fontes públicas para análise independente do investidor, em conformidade com as diretrizes do CNPI  
    (veja mais em https://www.apimecbrasil.com.br/certificacao/sobre-o-cnpi/).
    """
)

# --- Último preço de fechamento ---
ultimo = (
    cotacoes
    .sort_values(['fii_id', 'data'])
    .groupby('fii_id')['preco_fechamento']
    .last()
    .rename('preco_atual')
)
df = df.merge(ultimo, left_on='id', right_index=True, how='left')
df['preco_atual'] = pd.to_numeric(df['preco_atual'], errors='coerce')

# --- Pivot de indicadores (PL, Qt e Cap Rate) ---
pivot = (
    inds
    .pivot_table(
        index='fii_id',
        columns='indicador',
        values='valor',
        aggfunc='max'
    )
    .rename(columns={
        'Patrimônio Líquido':   'pl',
        'Quantidade de Cotas':   'qt',
        'Cap Rate':              'cap_rate'
    })
)
pivot[['pl', 'qt', 'cap_rate']] = pivot[['pl', 'qt', 'cap_rate']].apply(
    pd.to_numeric, errors='coerce'
)

# Mescla indicadores ao DataFrame principal
df = df.merge(
    pivot[['pl', 'qt', 'cap_rate']],
    left_on='id', right_index=True, how='left'
)

# --- Cálculo de VPA e P/VP ---
df['vpa_calc'] = df['pl'] / df['qt']
df['pvp_calc'] = df['preco_atual'] / df['vpa_calc']

# --- Cálculo de DY 12M ---
divs = inds[inds['indicador'] == 'Dividendos'].copy()
divs['periodo'] = divs['data_referencia'].dt.to_period('M')
ultimo_periodo = divs['periodo'].max()
inicio_periodo = ultimo_periodo - 11
d12 = divs[divs['periodo'].between(inicio_periodo, ultimo_periodo)]
soma_divs = d12.groupby('fii_id')['valor'].sum().rename('div12m')
df = df.merge(soma_divs, left_on='id', right_index=True, how='left')
df['dy_calc'] = (df['div12m'] / df['preco_atual']) * 100

# --- Definição dinâmica dos filtros “avançados” ---
setores = ['Todos'] + sorted(df['setor'].dropna().unique().tolist())
tipos   = ['Todos'] + sorted(df['tipo'].dropna().unique().tolist())

min_preco = float(df['preco_atual'].min().round(2))
max_preco = float(df['preco_atual'].max().round(2))
min_pvp   = float(df['pvp_calc'].min().round(2))
max_pvp   = float(df['pvp_calc'].max().round(2))
min_dy    = float(df['dy_calc'].min().round(2))
max_dy    = float(df['dy_calc'].max().round(2))

# --- Layout de busca e filtros (coluna direita) ---
st.markdown("## 🔎 Encontre um FII")
search_col, filters_col = st.columns([1, 2])

with search_col:
    query = st.text_input("", placeholder="Ex.: KNRI11, XPML11…", key="busca")

with filters_col:
    modo_ini = st.checkbox("🔰 Modo Iniciante", value=True, key="modo_ini")
    if modo_ini:
        st.markdown("### Como usar este dashboard")
        st.markdown(
            """
            - 📝 **Buscar**: digite o ticker (ex.: KNRI11).  
            - 🎯 **Filtrar**: ajuste setor, tipo, faixa de preço, P/VP e DY 12M.  
            - 🌟 **Ordenar**: escolha um indicador para destacar os melhores.  
            - 📊 **Visão Geral**: explore todos os resultados em tabela.  
            """
        )
        if st.button("💡 Dica Rápida", key="dica_ini"):
            st.info(
                """
                **Como interpretar os filtros:**  
                - **P/VP (Preço/Valor Patrimonial):** valores **< 1** indicam desconto; **> 1** indicam prêmio.  
                - **DY 12M (Dividend Yield):** retorno em dividendos nos últimos 12 meses.  
                - **VPA (Valor Patrimonial por Cota):** valor contábil de cada cota.  

                **Se está começando agora:**  
                - 📘 Em **Comece por Aqui**, entenda cada métrica.  
                - 🔍 Em **Análise por Fundo**, veja detalhes e histórico.  
                - 🔄 No **Comparador**, compare fundos lado a lado.  
                - 🏆 No **Ranking**, confira líderes por indicador.  
                - 📖 No **Glossário**, consulte termos financeiros.
                """
            )
        ordenar_por = "VPA"
        ordem       = "Crescente"
    else:
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            # Primeiro filtro: Tipo
            sel_tipo = st.selectbox("Filtrar por Tipo", tipos, key="tipo")

            # Filtro dependente: Setor (apenas os setores que existem no tipo selecionado)
            if sel_tipo != "Todos":
                setores_filtrados = (
                    ['Todos'] +
                    sorted(df[df['tipo'] == sel_tipo]['setor'].dropna().unique().tolist())
                )
            else:
                setores_filtrados = setores

            sel_setor = st.selectbox("Filtrar por Setor", setores_filtrados, key="setor")

            faixa_preco = st.slider(
                "Faixa de Preço (R$)",
                min_preco, max_preco,
                (min_preco, max_preco),
                key="preco"
            )

        with fcol2:
            faixa_pvp = st.slider(
                "Faixa de P/VP",
                min_pvp, max_pvp,
                (min_pvp, max_pvp),
                key="pvp"
            )
            faixa_dy = st.slider(
                "Faixa de DY 12M (%)",
                min_dy, max_dy,
                (min_dy, max_dy),
                key="dy"
            )
            ordenar_por = st.selectbox(
                "Ordenar por",
                ["Preço Atual", "VPA", "P/VP", "DY 12M"],
                key="ordenar"
            )
            ordem = st.radio(
                "Ordem",
                ["Decrescente", "Crescente"],
                horizontal=True,
                key="ordem"
            )

# --- Aplicação dos filtros ---
f = df.copy()

if query:
    f = f[
        f['ticker'].str.contains(query, case=False, na=False) |
        f['nome'].str.contains(query, case=False, na=False)
    ]

if not modo_ini:
    if sel_tipo != 'Todos':
        f = f[f['tipo'] == sel_tipo]
        # Limita os setores de acordo com o tipo já filtrado
    if sel_setor != 'Todos':
        f = f[f['setor'] == sel_setor]
    f = f[f['preco_atual'].between(*faixa_preco)]
    f = f[f['pvp_calc'].between(*faixa_pvp)]
    f = f[f['dy_calc'].between(*faixa_dy)]
    f = f.sort_values(
        by={
            "Preço Atual": "preco_atual",
            "VPA":         "vpa_calc",
            "P/VP":        "pvp_calc",
            "DY 12M":      "dy_calc"
        }[ordenar_por],
        ascending=(ordem == "Crescente")
    )


# --- Título e resumo de resultados ---
st.title("Dashboard de FIIs")
f = f.dropna(subset=['preco_atual', 'vpa_calc', 'pvp_calc', 'dy_calc'])

# --- Fundos em destaque ---
st.markdown("### ✨ Fundos em destaque")
top3 = (
    f.sort_values(
        by={
            "Preço Atual": "preco_atual",
            "VPA":         "vpa_calc",
            "P/VP":        "pvp_calc",
            "DY 12M":      "dy_calc"
        }[ordenar_por],
        ascending=(ordem == "Crescente")
    )
    .head(3)
    .reset_index(drop=True)
)

cols = st.columns(3)
for i, row in top3.iterrows():
    with cols[i]:
        st.subheader(f"{row['ticker']} ({row['tipo']})")
        st.metric("Preço Atual", format_brl(row['preco_atual']))
        st.metric("VPA", format_brl(row['vpa_calc']))
        st.metric("P/VP",         f"{row['pvp_calc']:.2f}")
        st.metric("DY 12M",       f"{row['dy_calc']:.2f}%")
        if not pd.isna(row.get('cap_rate')):
            st.metric("Cap Rate", f"{row['cap_rate']:.2f}%")

st.success(f"🔍 {len(f)} fundos encontrados")

# --- Tabela geral de resultados ---
st.markdown("---")
f2 = f.rename(columns={
    'ticker':      'Ticker',
    'setor':       'Setor',
    'tipo':        'Tipo',
    'preco_atual': 'Preço',
    'vpa_calc':    'VPA',
    'pvp_calc':    'P/VP',
    'dy_calc':     'DY 12M',
    'cap_rate':   'Cap Rate'
})
st.dataframe(f2[['Ticker','Setor','Tipo','Preço','VPA','P/VP','DY 12M','Cap Rate']])
