import streamlit as st
import re

# Função para corrigir o símbolo do real no texto
def fix_real(texto):
    return re.sub(r'R\$', r'R\$', texto)

# Configuração da página
st.set_page_config(
    page_title="Glossário de FIIs",
    page_icon="📚",
    layout="wide"
)

# === Índice na sidebar (apenas visual, não clica) ===
with st.sidebar:
    st.markdown("## Índice (visual)")
    st.markdown("""
    - 📦 O que é um Fundo?
    - 💼 Fundo de Investimento
    - 🏢 O que é um FII?
    - 🎟️ O que é uma Cota?
    - 💰 Dividendo (Provento)
    - 🔠 Ticker
    - 📂 Tipos de FIIs
    - 🏷️ Setores
    - 📊 Indicadores e Fórmulas
    - 🛠️ Como usar o Dashboard
    """)
    st.markdown("---")
    st.info("Navegue pelos tópicos rolando a página.\nO índice é apenas para referência visual.")

# Título principal
st.title("📖 Glossário Completo de FIIs e Indicadores")

# Estrutura de cada seção (aplicando fix_real em todos os textos relevantes)
st.header("📦 O que é um Fundo?")
st.write(fix_real(
    "Um **fundo** é como um condomínio de pessoas que se juntam para investir em algo maior do que conseguiriam sozinhas.\n"
    "Para iniciantes: Imagine um grupo de amigos comprando juntos um imóvel. Cada um contribui com parte do valor e recebe uma porcentagem proporcional dos ganhos quando alugam ou vendem esse imóvel."
))

st.header("💼 Fundo de Investimento")
st.write(fix_real(
    "Um **Fundo de Investimento** é um veículo regulamentado pela CVM para reunir recursos de diversos investidores."
))
st.expander("Como funciona na prática?").write(
    "1. Você aplica seu dinheiro no fundo.\n"
    "2. Um gestor profissional escolhe onde investir: ações, títulos, imóveis, etc.\n"
    "3. Você recebe resultados conforme a performance desses ativos."
)

st.header("🏢 O que é um FII?")
st.write(fix_real(
    "Um **FII** reúne dinheiro de várias pessoas para investir em imóveis e renda imobiliária.\n"
    "- Imóveis físicos: shoppings, edifícios, galpões.\n"
    "- Títulos imobiliários: CRIs, LCIs, recebíveis imobiliários."
))
st.success(fix_real(
    "Por que isso é bom para iniciantes? Você não precisa comprar um imóvel inteiro: basta adquirir uma cota, que geralmente custa um valor acessível e permite participar dos lucros."
))

st.header("🎟️ O que é uma Cota?")
st.write(fix_real(
    "A **cota** é a menor parte que você pode comprar de um fundo.\n"
    "Exemplo para iniciantes: Se um FII tem patrimônio total de R$ 100 milhões e 1 milhão de cotas, cada cota vale R$ 100."
))

st.header("💰 O que é um Dividendo? (Provento)")
st.write(fix_real(
    "Um **dividendo** é a parte do lucro ou renda que o fundo distribui periodicamente aos cotistas.\n"
    "Em FIIs, os dividendos normalmente vêm dos aluguéis pagos pelos imóveis que o fundo possui.\n"
    "Exemplo: Se você possui 10 cotas e cada cota paga R$ 1 no mês, você recebe R$ 10 no total."
))

st.header("🔠 O que é um Ticker?")
st.write(
    "O **ticker** é o código que identifica um FII na Bolsa de Valores."
)
st.write("**Características:**")
st.write(
    "- Composto por 4 letras + 11 (ex.: XPML11).\n"
    "- Indica tipo de fundo (ex.: LOG para logística, HGLG para galpões logísticos)."
)
st.subheader("Usos do ticker")
st.write(
    "- **Ordem de compra/venda:** informe o ticker no seu home broker.\n"
    "- **Consulta de preços:** pesquise o ticker em sites e apps financeiros.\n"
    "- **Análise histórica:** use o ticker para baixar séries de preço e volume."
)

st.header("📂 Tipos de FIIs")
st.write(fix_real(
    "Os **tipos** de FIIs ajudam a entender a estratégia de investimento de cada fundo.\n"
    "- **Tijolo:** investem em imóveis físicos, como shoppings, galpões logísticos e lajes corporativas.\n"
    "- **Papel:** aplicam em títulos de crédito imobiliário (CRIs, LCIs, LHs), recebendo juros e correções.\n"
    "- **Desenvolvimento:** financiam projetos imobiliários em construção, obtendo lucro na entrega das unidades.\n"
    "- **Fundo de Fundos (FOF):** investem em cotas de outros FIIs, diversificando em várias estratégias.\n"
    "- **Multiestratégia:** combinam ativos imobiliários e derivativos, buscando otimizar retorno e risco.\n"
    "- **Outros:** agrupam fundos com características não classificadas nas categorias acima."
))

st.header("🏷️ Setores de Atuação")
st.write(fix_real(
    "Os **setores** representam o segmento de mercado ou tipo de ativo em que o FII atua.\n"
    "- **Logísticos:** galpões para armazenamento e distribuição de mercadorias.\n"
    "- **Varejo/Shopping:** centros comerciais e lojas em shoppings.\n"
    "- **Lajes Corporativas:** escritórios e espaços corporativos.\n"
    "- **Residencial:** empreendimentos habitacionais.\n"
    "- **Hotéis:** ativos hoteleiros e resorts.\n"
    "- **Recebíveis Imobiliários:** títulos lastreados em crédito imobiliário (CRI/LCI).\n"
    "- **Títulos e Valores Mobiliários:** investimento em papéis diversos do setor imobiliário."
))

st.header("📊 Indicadores e Fórmulas")

st.subheader("1️⃣ VPA (Valor Patrimonial por Cota)")
st.write(
    "\nFórmula: VPA = Patrimônio Líquido (PL) ÷ Quantidade de Cotas\n"
    "\nO que significa: mostra quanto, teoricamente, cada cota do fundo representa do total de patrimônio do FII.\n "
    "\nÉ como se você pegasse todo o valor do fundo e dividisse igualmente entre todas as cotas emitidas.\n"
    "\nExemplo prático: se um fundo tem R\$ 100 milhões de patrimônio líquido e 1 milhão de cotas, cada cota vale, patrimonialmente, R\$ 100.\n"
    "\nDica para iniciantes: o VPA é um parâmetro para comparar com o preço de mercado da cota (usado no cálculo do P/VP). Quando o preço de mercado está abaixo do VPA, a cota está sendo negociada com desconto em relação ao valor contábil do fundo."
)
st.subheader("2️⃣ Dividend Yield (DY)")
st.write(fix_real(
    "\nFórmula: (Total de dividendos pagos ÷ preço da cota) × 100\n"
    "\nO que significa: representa o percentual de retorno em proventos em relação ao preço pago pela cota.\n"
    "\nExemplo fácil: se o fundo paga R\$ 1 de dividendos e cada cota custa R\$ 100, o DY será 1% (1 ÷ 100 × 100).\n"
    "\nDica para iniciantes: compare o DY com a taxa Selic para avaliar se é melhor investir em FIIs ou na renda fixa do Tesouro Direto."
))

st.subheader("3️⃣ P/VP (Preço sobre Valor Patrimonial)")
st.write(fix_real(
    "\nFórmula: preço da cota ÷ valor patrimonial por cota\n"
    "\nO que mostra: indica se a cota está sendo negociada com desconto (<1) ou ágio (>1) em relação ao valor contábil.\n"
    "\nExemplo: P/VP de 0,8 significa que o mercado paga 20% a menos que o valor patrimonial."
))
st.success(
    "Para iniciantes: cotas com P/VP abaixo de 1 podem indicar oportunidade de compra, mas pesquise o motivo do desconto."
)

st.subheader("4️⃣ Vacância Física / Ocupação")
st.write(
    "Fórmula: vacância (%) = 100 – ocupação (%)\n"
    "O que é: percentual de área dos imóveis do fundo que está desocupada.\n"
    "Exemplo: se a ocupação é 90%, a vacância é 10%."
)
st.warning(
    "Atenção: vacância alta reduz a geração de renda e pode impactar seus dividendos."
)

st.subheader("5️⃣ Número de Cotistas")
st.write(
    "O que é: quantidade de pessoas que possuem cotas do fundo.\n"
    "Por que importa: mais cotistas normalmente significam maior liquidez, ou seja, mais facilidade para comprar ou vender cotas."
)

st.subheader("6️⃣ Patrimônio Líquido (PL)")
st.write(fix_real(
    "O que é: soma do valor de todos os ativos do fundo (imóveis e títulos).\n"
    "Exemplo: um FII com patrimônio líquido de R$ 200 milhões possui esse montante investido em bens imobiliários."
))
st.success(
    "Dica para iniciantes: fundos maiores podem ter projetos e contratos mais estáis, mas avalie também o setor de atuação."
)

st.subheader("7️⃣ Cap Rate")
st.write(fix_real(
    "Fórmula: (receita anual de aluguéis ÷ valor de mercado dos imóveis) × 100\n"
    "O que mede: retorno anual esperado apenas com a renda de aluguéis.\n"
    "Exemplo: R$ 10 milhões de aluguel ÷ R$ 200 milhões de imóveis = cap rate de 5%.\n"
    "Dica iniciante: cap rate alto pode parecer atrativo, mas verifique vacância, localização e risco de inadimplência."
))

st.subheader("8️⃣ Volatilidade")
st.write(
    "Fórmula: desvio padrão dos retornos mensais da cota\n"
    "O que é: mede a variação do preço da cota ao longo do tempo.\n"
    "Exemplo: volatilidade de 2% ao mês indica flutuações médias de 2%."
)
st.warning(
    "Para iniciantes: maior volatilidade significa mais risco de oscilações bruscas. Considere fundos mais estáveis se preferir segurança."
)

st.header("🛠️ Como usar o Dashboard")
st.write(
    "1. Selecione o período (6 meses, 1 ano, 5 anos).\n"
    "2. Filtre por setor (logística, shoppings, recebíveis).\n"
    "3. Compare fundos no ‘Comparador’ para ver diferenças lado a lado.\n"
    "4. Consulte o ‘Ranking’ para identificar os melhores FIIs segundo cada indicador.\n"
    "5. Exporte em CSV para estudar offline ou incluir em relatórios.\n"
    "Dica final: use múltiplos indicadores juntos para uma análise mais robusta antes de tomar decisões de investimento."
)
