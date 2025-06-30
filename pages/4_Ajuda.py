import streamlit as st

# Configuração da página
st.set_page_config(page_title="Ajuda e Glossário", layout="wide")

# Estilo customizado para botões e expanders
st.markdown(
    """
    <style>
    div.stButton > button {
        background-color: #1f77b4;
        color: white;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-size: 1rem;
    }
    section[data-testid="stExpander"] > div:first-child {
        font-weight: 600;
        cursor: pointer;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Título principal
st.title("❓ Central de Ajuda e Glossário de Indicadores")

# Seção: Por onde começar
st.header("🚀 Por onde começar")
st.info("Siga os passos abaixo clicando em cada item para ver mais detalhes:")

with st.expander("1. Defina seu valor inicial"):
    st.write("- Estabeleça um valor que caiba no seu orçamento; sugerimos a partir de **R$ 1.000,00**.")
    st.write("- Confira o valor mínimo de investimento exigido pela corretora.")

with st.expander("2. Abra sua conta em uma corretora"):
    st.write("- Escolha uma corretora confiável (XP, Clear, Rico, entre outras). 📑")
    st.write("- Realize o cadastro com seus dados pessoais e envie a documentação necessária.")
    st.write("- Habilite o módulo de investimento em FIIs.")

with st.expander("3. Crie e diversifique sua carteira"):
    st.write("- Selecione FIIs de diferentes setores (logística, shoppings, recebíveis, lajes corporativas). 📊")
    st.write("- Defina percentuais de alocação para cada ativo (ex.: 30% logística, 20% shoppings, 50% recebíveis).")
    st.write("- Utilize planilhas ou ferramentas para simular cenários de retorno.")

with st.expander("4. Balanceie periodicamente"):
    st.write("- Revise sua carteira a cada 6 ou 12 meses. 🔄")
    st.write("- Reinvista parte dos proventos em fundos com bom indicador P/VP ou DY.")
    st.write("- Ajuste percentuais para manter a alocação alvo.")

with st.expander("5. Monitore indicadores-chave"):
    st.write("- Acompanhe mensalmente Dividend Yield, P/VP e Vacância. 📈")

# Vídeos de apoio (exemplos)
st.video("https://www.youtube.com/watch?v=EXEMPLO1", format="youtube")  # Abrindo conta na corretora
st.video("https://www.youtube.com/watch?v=EXEMPLO2", format="youtube")  # Montagem de carteira diversificada
st.video("https://www.youtube.com/watch?v=EXEMPLO3", format="youtube")  # Monitoramento e rebalanceamento

st.markdown("---")

# Conteúdo de ajuda aprimorado
st.markdown(
    """

### ℹ️ O que é um Fundo Imobiliário (FII)?
Um **FII** (Fundo de Investimento Imobiliário) reúne recursos de diversos investidores para aplicar em:
- **Imóveis físicos:** shoppings, edifícios, galpões, hotéis.
- **Títulos imobiliários:** CRIs, LCI, recebíveis imobiliários.

Ao comprar cotas, você se torna cotista e tem direito a:
- **Rendimentos mensais** oriundos de aluguéis ou juros dos títulos.
- **Valorização do patrimônio** quando o preço da cota sobe.

**Por que investir em FIIs?**
- Acesso a grandes empreendimentos com pouco capital.
- Renda passiva mensal, isenta de IR para pessoa física.
- Diversificação e liquidez (negociação em bolsa).

---

### 🔠 O que é um Ticker?
O **ticker** é o código que identifica o FII na Bolsa de Valores. Características:
- Composto por 4 letras + `11` (ex.: `XPML11`).
- Usado para:
  - **Ordem de compra/venda** no home broker.
  - **Consulta de preços** em sites e apps.
  - **Análise de performance** histórica.

---

### 📊 Principais Indicadores

#### 1. Dividend Yield (DY)
- **Fórmula:** (Rendimento mensal ÷ Preço da cota) × 100
- **Significado:** % de retorno mensal. Ex.: DY de 0,8% → R$0,80 por R$100 investidos.
- **Dica:** compare com a taxa Selic e com outros FIIs.

#### 2. P/VP (Preço sobre Valor Patrimonial)
- **Fórmula:** Preço da cota ÷ Valor Patrimonial por cota
- **Significado:** indica se a cota está barata (<1) ou cara (>1).

#### 3. Vacância Física / Ocupação
- **Ocupação (%):** % de área alugada.
- **Vacância (%):** 100% – Ocupação.
- **Importância:** alta vacância pode reduzir rendimentos.

#### 4. Número de Cotistas
- **O que é:** total de investidores com cotas.
- **Importância:** maior quantidade → maior liquidez das cotas.

#### 5. Patrimônio Líquido
- **O que é:** valor total dos ativos do fundo.
- **Importância:** indica escala e capacidade de geração de renda.

---

### 🛠️ Como usar o Dashboard
1. **Menu lateral:** navegue entre ‘Análise Detalhada’, ‘Comparador’, ‘Ranking’.  
2. **Filtros:** selecione setor e indicadores para personalizar gráficos.  
3. **Análise Detalhada:** gráficos de cota, dividendos e vacância do fundo.  
4. **Comparador:** compare dois fundos lado a lado (imóveis e indicadores).  
5. **Ranking:** top 10 FIIs por indicador e comparativo ocupação vs vacância.  
6. **Exportação:** baixe dados em CSV para análises externas.  

""",
    unsafe_allow_html=True
)
