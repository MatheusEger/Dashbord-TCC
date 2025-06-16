import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import plotly.graph_objects as go

st.title("📈 Analise da Vacância")
st.markdown("""
Compare diferentes fundos e visualize o desempenho de forma gráfica para facilitar sua decisão de investimento, especialmente se você está começando agora.
Use o heatmap para ver rapidamente onde cada fundo se destaca e o gráfico radar para entender o perfil de um fundo específico.

✅ **Por que "Ocupação em 100%" e "Vacância Física próxima de 0%" são importantes?**
Esses indicadores refletem o uso efetivo dos imóveis do fundo. Alta ocupação e baixa vacância significam que os imóveis estão sendo alugados e gerando renda, o que aumenta a estabilidade e previsibilidade dos rendimentos.
""")

# Conexão com banco
def carregar_dados():
    DB_PATH = Path(__file__).parents[1] / "data" / "fiis.db"
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

# Filtro por segmento
disponiveis = sorted(fiis['setor'].unique())
segmento_filtro = st.multiselect("Filtrar por Segmento:", options=disponiveis, default=disponiveis)
fiis_filtrados = fiis[fiis['setor'].isin(segmento_filtro)]

def parse_data_ref(val):
    try:
        return pd.to_datetime(val, format="%Y-%m-%d")
    except:
        try:
            return pd.to_datetime("01/" + val, format="%d/%m/%Y")
        except:
            return pd.NaT

# Pivot + heatmap básico
st.subheader("Heatmap de Indicadores (última referência)")
st.markdown("Cores mais fortes indicam melhores desempenhos em cada indicador. Os valores numéricos também são exibidos com até duas casas decimais para facilitar a comparação.")
# Filtra apenas Vacância e Ocupação Percentual
df = indicadores[
    (indicadores['fii_id'].isin(fiis_filtrados['id'])) &
    (indicadores['indicador'].isin(['Vacância Percentual', 'Ocupação Percentual']))]
df['data_referencia'] = df['data_referencia'].apply(parse_data_ref).dt.date
df = df[df['data_referencia'] == df['data_referencia'].max()]
df_pivot = df.pivot_table(index="ticker_fii", columns="indicador", values="valor", aggfunc="last")

styled_heatmap = df_pivot.style.format("{:.2f}").background_gradient(cmap="Blues")
st.dataframe(styled_heatmap, use_container_width=True)

# Radar chart
st.subheader("Radar por FII")
st.markdown("Veja o perfil completo de um fundo selecionado. Ideal para entender seus pontos fortes e fracos.")

# Exibe apenas FIIs que possuem pelo menos 4 indicadores diferentes
df_radar_opcoes = df_pivot.dropna(thresh=4)

if not df_radar_opcoes.empty:
    fii_escolhido = st.selectbox("Escolha um FII:", df_radar_opcoes.index.tolist())
    df_radar = df_radar_opcoes.loc[[fii_escolhido]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=df_radar.values[0],
        theta=df_radar.columns,
        fill='toself',
        name=fii_escolhido
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=False,
        title=f"Perfil de Indicadores - {fii_escolhido}"
    )
    st.plotly_chart(fig_radar, use_container_width=True)
    st.markdown("""
    🔍 **Como interpretar:**
    - Pontas maiores indicam bons resultados naquele indicador.
    - Fundos com formas equilibradas tendem a ser mais consistentes.
    - Use esta visualização para comparar com outros fundos e identificar oportunidades.
    """)
else:
    st.warning("Nenhum FII disponível com indicadores suficientes para exibir o radar.")