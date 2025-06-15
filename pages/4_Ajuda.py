import streamlit as st

st.title("❓ Ajuda")

st.markdown("""
Esta aplicação tem como objetivo apresentar indicadores financeiros relevantes de Fundos Imobiliários (FIIs) de forma acessível.

**Menu de Páginas:**
- **🔍 Análise Detalhada**: gráficos e visualizações com base nos indicadores.
- **📋 Lista Completa**: exibe todos os FIIs coletados e permite filtragem por segmento.
- **📈 Comparações**: traz heatmap e gráficos do tipo radar para comparação entre os fundos.
- **❓ Ajuda**: explicações gerais.

**Filtros:**
- Você pode selecionar os segmentos desejados para refinar os dados apresentados nas visualizações.

**Indicadores (exemplos):**
- *Dividend Yield (DY)*: Retorno mensal sobre o preço da cota.
- *P/VP*: Preço sobre Valor Patrimonial.
- *Vacância Física*: Porcentagem da área vaga.
- *Cap Rate*: Rendimento dos imóveis comparado ao valor investido.
- *Número de Cotistas*: Indica liquidez e interesse.

Essas métricas são essenciais para análise comparativa e avaliação de performance dos fundos.
""")
