import streamlit as st

# Configuração da página
st.set_page_config(page_title="Glossário de FIIs", layout="wide")

# Título da página
st.title("📖 Glossário Completo de FIIs e Indicadores")

# ==============================================
# Seção: O que é um Fundo?
# ==============================================
st.header("O que é um Fundo?")
st.write(
    "Um **fundo** é como um condomínio de pessoas que se juntam para investir em algo maior do que conseguiriam sozinhas."
)
# Destaque para iniciantes, texto claro sem símbolos confusos
st.write(
    "Para iniciantes: Imagine um grupo de amigos comprando juntos um imóvel. Cada um contribui com parte do valor e recebe uma porcentagem proporcional dos ganhos quando alugam ou vendem esse imóvel."
)

# ==============================================
# Seção: O que é um Fundo de Investimento?
# ==============================================
st.header("O que é um Fundo de Investimento?")
st.write(
    "Um **Fundo de Investimento** é um veículo regulamentado pela CVM para reunir recursos de diversos investidores."
)
st.expander("Como funciona na prática?").write(
    "1. Você aplica seu dinheiro no fundo.\n"
    "2. Um gestor profissional escolhe onde investir: ações, títulos, imóveis, etc.\n"
    "3. Você recebe resultados conforme a performance desses ativos."
)

# ==============================================
# Seção: O que é um FII? (Fundo de Investimento Imobiliário)
# ==============================================
st.header("O que é um FII? (Fundo de Investimento Imobiliário)")
st.write(
    "Um **FII** reúne dinheiro de várias pessoas para investir em imóveis e renda imobiliária."
)
st.write(
    "- Imóveis físicos: shoppings, edifícios, galpões.\n"
    "- Títulos imobiliários: CRIs, LCIs, recebíveis imobiliários."
)
# Benefício para iniciantes sem símbolos confusos
st.success(
    "Por que isso é bom para iniciantes? Você não precisa comprar um imóvel inteiro: basta adquirir uma cota, que geralmente custa um valor acessível e permite participar dos lucros."
)

# ==============================================
# Seção: O que é uma Cota?
# ==============================================
st.header("O que é uma Cota?")
st.write(
    "A **cota** é a menor parte que você pode comprar de um fundo."
)
st.write(
    "Exemplo para iniciantes: Se um FII tem patrimônio total de R\$ 100 milhões e 1 milhão de cotas, cada cota vale R\$ 100."
)

# ==============================================
# Seção: O que é um Dividendo? (Provento)
# ==============================================
st.header("O que é um Dividendo? (Provento)")
st.write(
    "Um **dividendo** é a parte do lucro ou renda que o fundo distribui periodicamente aos cotistas."
)
st.write(
    "Em FIIs, os dividendos normalmente vêm dos aluguéis pagos pelos imóveis que o fundo possui."
)
st.write(
    "Exemplo: Se você possui 10 cotas e cada cota paga R\$ 1 no mês, você recebe R\$ 10 no total."
)

# ==============================================
# ==============================================
# Seção: O que é um Ticker?
# ==============================================
st.header("🔠 O que é um Ticker?")
st.write(
    "O **ticker** é o código que identifica um FII na Bolsa de Valores."
)
# Características do ticker
st.write(
    "**Características:**"
)
st.write(
    "- Composto por 4 letras + 11 (ex.: XPML11)."
)
st.write(
    "- Indica tipo de fundo (ex.: LOG para logística, HGLG para galpões logísticos)."
)
# Exemplos de uso
st.subheader("Usos do ticker")
st.write(
    "- **Ordem de compra/venda:** informe o ticker no seu home broker."
)
st.write(
    "- **Consulta de preços:** pesquise o ticker em sites e apps financeiros."
)
st.write(
    "- **Análise histórica:** use o ticker para baixar séries de preço e volume."
)
# ====================================================================
# Indicadores principais com explicações detalhadas
# ==================================================================== com explicações detalhadas
# ==============================================
st.header("📊 Indicadores e Fórmulas (Linha a linha)")

# Dividend Yield
st.subheader("1. Dividend Yield (DY)")
st.write("Fórmula: (Total de dividendos pagos ÷ preço da cota) × 100")
st.write(
    "O que significa: representa o percentual de retorno em proventos em relação ao preço pago pela cota.\n"
    "Exemplo fácil: se o fundo paga R\$ 1 de dividendos e cada cota custa R\$ 100, o DY será 1% (1 ÷ 100 × 100)."
)
st.write(
    "Dica para iniciantes: compare o DY com a taxa Selic para avaliar se é melhor investir em FIIs ou na renda fixa do Tesouro Direto."
)

# P/VP
st.subheader("2. P/VP (Preço sobre Valor Patrimonial)")
st.write("Fórmula: preço da cota ÷ valor patrimonial por cota")
st.write(
    "O que mostra: indica se a cota está sendo negociada com desconto (<1) ou ágio (>1) em relação ao valor contábil.\n"
    "Exemplo: P/VP de 0,8 significa que o mercado paga 20% a menos que o valor patrimonial."
)
st.success(
    "Para iniciantes: cotas com P/VP abaixo de 1 podem indicar oportunidade de compra, mas pesquise o motivo do desconto."
)

# Vacância Física
st.subheader("3. Vacância Física / Ocupação")
st.write("Fórmula: vacância (%) = 100 – ocupação (%)")
st.write(
    "O que é: percentual de área dos imóveis do fundo que está desocupada.\n"
    "Exemplo: se a ocupação é 90%, a vacância é 10%."
)
st.warning(
    "Atenção: vacância alta reduz a geração de renda e pode impactar seus dividendos."
)

# Número de Cotistas
st.subheader("4. Número de Cotistas")
st.write("O que é: quantidade de pessoas que possuem cotas do fundo.")
st.write(
    "Por que importa: mais cotistas normalmente significam maior liquidez, ou seja, mais facilidade para comprar ou vender cotas."
)

# Patrimônio Líquido
st.subheader("5. Patrimônio Líquido (PL)")
st.write("O que é: soma do valor de todos os ativos do fundo (imóveis e títulos).\n"
         "Exemplo: um FII com patrimônio líquido de R\$ 200 milhões possui esse montante investido em bens imobiliários.")
st.success(
    "Dica para iniciantes: fundos maiores podem ter projetos e contratos mais estáveis, mas avalie também o setor de atuação."
)

# Cap Rate
st.subheader("6. Cap Rate")
st.write("Fórmula: (receita anual de aluguéis ÷ valor de mercado dos imóveis) × 100")
st.write(
    "O que mede: retorno anual esperado apenas com a renda de aluguéis.\n"
    "Exemplo: R\$ 10 milhões de aluguel ÷ R\$ 200 milhões de imóveis = cap rate de 5%."
)
st.write(
    "Dica iniciante: cap rate alto pode parecer atrativo, mas verifique vacância, localização e risco de inadimplência."
)

# Volatilidade
st.subheader("7. Volatilidade")
st.write("Fórmula: desvio padrão dos retornos mensais da cota")
st.write(
    "O que é: mede a variação do preço da cota ao longo do tempo.\n"
    "Exemplo: volatilidade de 2% ao mês indica flutuações médias de 2%."
)
st.warning(
    "Para iniciantes: maior volatilidade significa mais risco de oscilações bruscas. Considere fundos mais estáveis se preferir segurança."
)

# ==============================================
# Como usar o Dashboard
# ==============================================
st.header("🛠️ Como usar o Dashboard")
st.write(
    "1. Selecione o período (6 meses, 1 ano, 5 anos).\n"
    "2. Filtre por setor (logística, shoppings, recebíveis).\n"
    "3. Compare fundos no ‘Comparador’ para ver diferenças lado a lado.\n"
    "4. Consulte o ‘Ranking’ para identificar os melhores FIIs segundo cada indicador.\n"
    "5. Exporte em CSV para estudar offline ou incluir em relatórios."
)
st.write(
    "Dica final: use múltiplos indicadores juntos para uma análise mais robusta antes de tomar decisões de investimento."
)
