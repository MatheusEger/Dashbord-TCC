import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import plotly.express as px

st.title("🔍 Análise Detalhada")
st.markdown("""
Esta página foi pensada para ajudar investidores iniciantes a analisarem Fundos Imobiliários de forma simples e visual.
Selecione o setor e indicador desejado para ver gráficos e explicações de forma clara.
""")

# Conexão com banco
def carregar_dados():
    DB_PATH = Path(__file__).parents[1] / "data" / "fiis.db"
    conn = sqlite3.connect(DB_PATH)
    fiis = pd.read_sql("""
        SELECT f.id, f.ticker, f.nome, s.nome as setor
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

# Filtro por segmento
disponiveis = sorted(fiis['setor'].unique())
segmento_filtro = st.multiselect("Filtrar por Segmento:", options=disponiveis, default=disponiveis)
fiis_filtrados = fiis[fiis['setor'].isin(segmento_filtro)]

# Gráfico por setor
st.subheader("Distribuição por Setor")
st.markdown("Veja quantos fundos existem em cada setor. Isso ajuda a entender onde há mais variedade de investimentos.")
fig_setor = px.histogram(fiis_filtrados, x="setor", color="setor", title="Quantidade de FIIs por Setor")
st.plotly_chart(fig_setor, use_container_width=True)

# Indicadores
st.subheader("Indicador Específico")
st.markdown("Escolha um indicador abaixo para ver os FIIs que mais se destacam na última referência disponível.")

indicador_opcoes = indicadores['indicador'].dropna().unique().tolist()
if indicador_opcoes:
    indicador_selecionado = st.selectbox("Escolha um indicador:", indicador_opcoes)
    df_ind = indicadores[indicadores['indicador'] == indicador_selecionado]
    df_ind = df_ind[df_ind['fii_id'].isin(fiis_filtrados['id'])]
    df_ind['data_referencia'] = pd.to_datetime(df_ind['data_referencia']).dt.date
    df_ult = df_ind[df_ind['data_referencia'] == df_ind['data_referencia'].max()]

    if not df_ult.empty:
        st.markdown(f"**Resumo do indicador {indicador_selecionado}:**")
        col1, col2, col3, col4 = st.columns(4)
        media = df_ult['valor'].mean()
        mediana = df_ult['valor'].median()
        maximo = df_ult['valor'].max()
        minimo = df_ult['valor'].min()
        col1.metric("Média", f"{media:.2f}")
        col2.metric("Mediana", f"{mediana:.2f}")
        col3.metric("Máximo", f"{maximo:.2f}")
        col4.metric("Mínimo", f"{minimo:.2f}")

        # Explicação amigável
        explicacao = ""
        if indicador_selecionado == "Nº Cotistas":
            if media > 5000:
                explicacao = "\n\n🔎 Um fundo com muitos cotistas tende a ser mais líquido e confiável, pois demonstra interesse do mercado. Fundos com milhares de cotistas são geralmente mais fáceis de negociar."
            else:
                explicacao = "\n\n⚠️ Poucos cotistas podem indicar baixa liquidez, o que dificulta a compra e venda das cotas."
        elif indicador_selecionado == "Dividend Yield":
            explicacao = "\n\n💰 Um DY acima de 0,6% ao mês costuma ser atrativo, mas sempre observe se é sustentável."
        elif indicador_selecionado == "P/VP":
            explicacao = "\n\n📉 Um P/VP abaixo de 1 pode indicar que o fundo está barato em relação ao seu valor patrimonial, mas cuidado com fundos problemáticos."
        elif indicador_selecionado == "Vacância Física":
            explicacao = "\n\n🏢 Vacância baixa é sinal positivo: indica imóveis ocupados e geração de receita."

        if explicacao:
            st.markdown(explicacao)

        # Limita exibição aos 15 maiores valores para facilitar leitura
        df_top = df_ult.sort_values(by="valor", ascending=False).head(15)

        fig_bar = px.bar(df_top, x="valor", y="ticker_fii", orientation="h", text="valor",
                         title=f"Top 15 FIIs por {indicador_selecionado} (última referência)",
                         labels={"valor": indicador_selecionado, "ticker_fii": "FII"})
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para o indicador com os filtros atuais.")
