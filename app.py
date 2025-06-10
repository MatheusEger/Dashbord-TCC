import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import plotly.express as px

# Config inicial
st.set_page_config(page_title="Dashboard FIIs", layout="wide")

# Sidebar
st.sidebar.title("📊 Dashboard FIIs")
st.sidebar.markdown("---")
pagina = st.sidebar.radio("Menu", ["🔍 Análise Detalhada", "📋 Lista Completa", "❓ Ajuda"])
st.sidebar.markdown("---")

# Conexão com banco
DB_PATH = Path(__file__).resolve().parent / "data" / "fiis.db"
def carregar_dados():
    conn = sqlite3.connect(DB_PATH)
    fiis = pd.read_sql("""
        SELECT f.id, f.ticker, f.nome, s.nome as setor, f.created_at
        FROM fiis f
        JOIN setor s ON f.setor_id = s.id
    """, conn)

    indicadores = pd.read_sql("""
        SELECT fi.fii_id, f.ticker AS ticker_fii, i.nome AS indicador, fi.valor, fi.data_referencia
        FROM fiis_indicadores fi
        JOIN indicadores i ON i.id = fi.indicador_id
        JOIN fiis f ON f.id = fi.fii_id 
    """, conn)
    conn.close()
    return fiis, indicadores

fiis, indicadores = carregar_dados()

# Atualizar opções de filtro na sidebar
disponiveis = sorted(fiis['setor'].unique())

segmento_filtro = st.sidebar.multiselect(
    "Filtrar por Segmento:",
    options=disponiveis,
    default=disponiveis,
    key="filtro_segmento"
)

fiis_filtrados = fiis[fiis['setor'].isin(segmento_filtro)]

# === Layout com colunas principais
col1, col2, col3 = st.columns(3)
col1.metric("Total de FIIs", len(fiis_filtrados))
col2.metric("Setores", fiis_filtrados['setor'].nunique())
col3.metric("Indicadores distintos", indicadores.drop_duplicates(subset=["fii_id", "indicador", "data_referencia"]).shape[0])

if pagina == "🔍 Análise Detalhada":
    # === Gráfico de barras: FIIs por setor
    st.subheader("Distribuição por Setor")
    fig_setor = px.histogram(fiis_filtrados, x="setor", color="setor", title="Quantidade de FIIs por Setor")
    st.plotly_chart(fig_setor, use_container_width=True)

    # === Gráfico de linha: indicadores agregados
    st.subheader("Evolução dos Indicadores")
    indicador_opcoes = indicadores['indicador'].dropna().unique().tolist()
    if indicador_opcoes:
        indicador_selecionado = st.selectbox("Escolha um indicador para visualizar:", indicador_opcoes)
        df_ind = indicadores[indicadores['indicador'] == indicador_selecionado]
        df_ind = df_ind[df_ind['fii_id'].isin(fiis_filtrados['id'])]  # aplica o filtro de segmento
        df_ind["data_referencia"] = pd.to_datetime(df_ind["data_referencia"]).dt.date
        df_ind = df_ind[df_ind["data_referencia"] == df_ind["data_referencia"].max()]  # último mês

        if not df_ind.empty:
            fig_ind = px.bar(
                df_ind,
                x="valor",
                y="ticker_fii",
                orientation="h",
                labels={"valor": indicador_selecionado, "ticker_fii": "FII"},
                title=f"{indicador_selecionado} (última referência)",
                text="valor"
            )
            fig_ind.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_ind, use_container_width=True)

            st.dataframe(df_ind[["ticker_fii", "data_referencia", "valor"]], use_container_width=True)

        else:
            st.info("Nenhum dado disponível para o indicador selecionado com os filtros atuais.")
    else:
        st.warning("Nenhum indicador disponível.")

elif pagina == "📋 Lista Completa":
    st.subheader("Tabela Completa de FIIs")
    st.dataframe(fiis_filtrados, use_container_width=True)

elif pagina == "❓ Ajuda":
    st.subheader("Ajuda")
    st.markdown("""
    Esta aplicação tem como objetivo apresentar indicadores financeiros relevantes de Fundos Imobiliários (FIIs) de forma acessível.
    
    **Menu:**
    - *Análise Detalhada*: gráficos e visualizações com base nos indicadores.
    - *Lista Completa*: exibe todos os FIIs coletados.
    - *Ajuda*: esta seção.
    
    **Filtros:**
    - Selecione os segmentos de FIIs desejados para atualizar os gráficos e a lista.
    """)
