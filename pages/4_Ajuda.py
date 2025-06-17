import streamlit as st

st.set_page_config(page_title="Ajuda e Glossário", layout="wide")

st.title("❓ Central de Ajuda e Glossário de Indicadores")

st.markdown("---")

st.markdown("""
### ℹ️ O que é um Fundo Imobiliário (FII)?
Um FII é um fundo que investe em empreendimentos imobiliários como shoppings, escritórios, galpões logísticos ou recebíveis imobiliários. Ao comprar cotas, o investidor passa a ter direito a uma fração dos rendimentos.

---

### 🔠 O que é um Ticker?
O ticker é o código de negociação do FII na bolsa, geralmente composto por 4 letras e o número '11'.  
Exemplo: `XPML11`, `HGLG11`, `KNRI11`.

---

### 📊 Indicadores explicados

#### 1. Dividend Yield (DY)
- **Fórmula**: Último rendimento ÷ preço da cota
- **Indica** quanto o investidor recebe mensalmente em relação ao preço pago pela cota.

#### 2. P/VP (Preço sobre Valor Patrimonial)
- **Fórmula**: Preço da cota ÷ Valor patrimonial por cota
- Valores < 1 indicam que o FII está abaixo do valor patrimonial.

#### 3. Número de Cotistas
- Total de investidores com cotas do fundo.

#### 4. Setor ou Segmento
- Área de atuação do FII, como logística, recebíveis, shopping, etc.

---

### 🛠️ Como usar o Dashboard
- Navegue pelo menu lateral e selecione “Análise Detalhada” para gráficos.
- Use os filtros por segmento para refinar os dados.
- A aba “Lista Completa” mostra todos os FIIs disponíveis com base nos dados coletados.

---
""")
