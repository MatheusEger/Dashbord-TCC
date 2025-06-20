import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Análise por Fundo")

# Ocultar barra lateral para controle completo do layout
st.markdown("""
<style>
    .metric-block {
        text-align: center;
        padding: 1rem;
        border: 1px solid #ccc;
        border-radius: 12px;
        background-color: #f9f9f9;
    }
    .right-col {
        padding: 1rem;
        border-radius: 12px;
        background-color: #f4f4f4;
    }
</style>
""", unsafe_allow_html=True)

# Banco de dados
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "fiis.db"
conn = sqlite3.connect(DB_PATH)

# Carregando dados
fiis = pd.read_sql("SELECT * FROM fiis;", conn)
cotacoes = pd.read_sql("SELECT * FROM cotacoes;", conn)
indicadores = pd.read_sql("""
    SELECT fi.fii_id, f.ticker AS ticker_fii, i.nome AS indicador, fi.valor, fi.data_referencia
    FROM fiis_indicadores fi
    JOIN indicadores i ON i.id = fi.indicador_id
    JOIN fiis f ON f.id = fi.fii_id;
""", conn)
setores = pd.read_sql("SELECT * FROM setor;", conn)
conn.close()

# Menu lateral com seleção do ticker
st.sidebar.title("🔎 Filtro de FII")
fii_opcoes = sorted(fiis["ticker"].unique())
ticker_selecionado = st.sidebar.selectbox("Escolha o FII:", fii_opcoes)

# Dados do fundo selecionado
fii_info = fiis[fiis["ticker"] == ticker_selecionado].iloc[0]
fii_id = fii_info["id"]
setor_nome = setores[setores["id"] == fii_info["setor_id"]]["nome"].values[0]

# Preço atual
cotacao_fii = cotacoes[(cotacoes["fii_id"] == fii_id)]
if not cotacao_fii.empty:
    valor_raw = cotacao_fii.sort_values("data", ascending=False).head(1)["preco_fechamento"].values[0]
    cotacao_atual = float(str(valor_raw).replace(".", "").replace(",", "."))
else:
    cotacao_atual = 0.0  # ou use "-" se preferir exibir como string

# Últimos indicadores
dados_fii = indicadores[indicadores["ticker_fii"] == ticker_selecionado]
dados_fii["data_referencia"] = pd.to_datetime(dados_fii["data_referencia"])

def obter_ultimo_valor(nome_indicador):
    dados = dados_fii[dados_fii["indicador"] == nome_indicador]
    if not dados.empty:
        return dados.sort_values("data_referencia", ascending=False).iloc[0]["valor"]
    return "-"

# Layout principal
st.title("Análise por Fundo")

col_esq, col_dir = st.columns([2, 1])

with col_esq:
    st.markdown("### Indicadores Principais")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💰 Preço Atual", f"R$ {cotacao_atual:.2f}" if cotacao_atual else "-")
    col2.metric("P/VP", obter_ultimo_valor("P/VP"))
    col3.metric("DY Último", f"{obter_ultimo_valor('Dividend Yield Último')}%")
    col4.metric("DY 3M", f"{obter_ultimo_valor('Dividend Yield 3M')}%")
    col5.metric("DY 12M", f"{obter_ultimo_valor('Dividend Yield 12M')}%")

with col_dir:
    st.markdown("### 📄 Informações do Fundo")
    st.markdown(f"<div class='right-col'>"
                f"<b>Setor:</b> {setor_nome}<br>"
                f"<b>Último Dividendo:</b> R$ {obter_ultimo_valor('Dividendos')}<br>"
                f"<b>Patrimônio Líquido:</b> R$ {obter_ultimo_valor('Patrimônio Líquido')}</div>",
                unsafe_allow_html=True)

# Gráficos
st.markdown("### 📊 Indicadores Visuais")

# Gráfico de barras: DY Último, 3M e 12M
dy_data = {
    "Indicador": ["DY Último", "DY 3M", "DY 12M"],
    "Valor (%)": [
        float(obter_ultimo_valor("Dividend Yield Último") or 0),
        float(obter_ultimo_valor("Dividend Yield 3M") or 0),
        float(obter_ultimo_valor("Dividend Yield 12M") or 0)
    ]
}
dy_df = pd.DataFrame(dy_data)
fig_dy = px.bar(dy_df, x="Indicador", y="Valor (%)", text="Valor (%)", title="Dividend Yield (Último, 3M, 12M)")
st.plotly_chart(fig_dy, use_container_width=True)

# Gráfico Vacância
df_vac = dados_fii[dados_fii["indicador"].isin(["Vacância Percentual", "Vacância m²"])]
if not df_vac.empty:
    fig_vac = px.bar(df_vac, x="data_referencia", y="valor", color="indicador", barmode="group", title="Vacância (%) e m² ao longo do tempo")
    st.plotly_chart(fig_vac, use_container_width=True)

# Gráfico de dividendos ao longo do tempo
df_div = dados_fii[dados_fii["indicador"] == "Dividendos"]
if not df_div.empty:
    fig_div = px.line(df_div, x="data_referencia", y="valor", title="Histórico de Dividendos")
    st.plotly_chart(fig_div, use_container_width=True)

# Gráfico de cotação
if not cotacao_fii.empty:
    cotacao_fii["data"] = pd.to_datetime(cotacao_fii["data"])
    fig_cot = px.line(cotacao_fii, x="data", y="preco_fechamento", title="Evolução da Cotação")
    st.plotly_chart(fig_cot, use_container_width=True)
