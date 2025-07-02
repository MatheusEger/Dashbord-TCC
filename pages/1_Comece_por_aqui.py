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
st.title("Central de Ajuda e Glossário de Indicadores")

st.header("📌 Bem-vindo ao mundo dos FIIs")
st.markdown("""
Investir em Fundos de Investimento Imobiliário (FIIs) é uma forma de:
- Obter **renda passiva** por meio de aluguéis;
- Ter **diversificação** sem comprar um imóvel inteiro;
- Começar com valores acessíveis, a partir de poucas dezenas de reais.
""")

with st.expander("🔰 Conceitos básicos"):
    st.write("- **FII**: Fundo de Investimento Imobiliário, que reúne investidores para aplicar em imóveis ou papéis imobiliários.")
    st.write("- **Cota**: menor fração que você pode comprar de um FII.")
    st.write("- **Dividendo**: provento distribuído periodicamente aos cotistas, normalmente proveniente de aluguéis.")

st.markdown("Para um glossário completo de termos, clique na página **Glossário** no menu lateral.")
st.markdown("---")

# Seção: Por onde começar
st.header("🚀 Por onde começar")
st.info("Siga os passos abaixo clicando em cada item para ver mais detalhes:")

with st.expander("1. Defina seu valor inicial"):
    st.write("- Escolha um valor que não comprometa suas despesas. Comece com o que for confortável, por exemplo, **R$ 100,00**.")
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

st.header("Videos aulas sobre como abrir uma conta em uma corretora")

st.subheader("COMO abrir conta na RICO corretora de valores | NA PRÁTICA!")
st.video("https://www.youtube.com/watch?v=W4wgdekEjuI", format="youtube")
st.info("Postado em 16 de set. de 2019 - 11.353 visualizações")

st.subheader("COMO abrir conta na XP Corretora de valores | NA PRÁTICA!")
st.video("https://www.youtube.com/watch?v=Q7guEK_o3o0", format="youtube")
st.info("Postado em 22 de set. de 2019 - 16.498 visualizações ")

st.subheader("COMO abrir conta na EasyInvest corretora de valores | NA PRÁTICA!")
st.video("https://www.youtube.com/watch?v=AAT4iPy8vOs", format="youtube")
st.info("Postado em 19 de set. de 2019 - 3.290 visualizações  ")

st.header("Montagem de carteira diversificada")

st.subheader("Como montar sua carteira de investimentos")
st.video("https://www.youtube.com/watch?v=k_dku4WdyMk", format="youtube") 
st.info("Postado em 26 de jun. de 2018 - 73 mil visualizações  ")

st.header("Videoaulas sobre Fundos Imobiliários")

st.subheader("Aula sobre Fundos Imobiliários (do Zero para Iniciantes)")
st.video("https://www.youtube.com/watch?v=z3fTzc0q10M", format="youtube")
st.info("Postado em 3 de set. de 2024 - 1.3 mi visualizações  ")

st.header("Monitoramento e rebalanceamento")

st.subheader("Como rebalancear a carteira de FIIs? | 5 dúvidas dos investidore")
st.video("https://www.youtube.com/watch?v=SiNBvaAhvLo", format="youtube") 
st.info("Postado em 24 de fev. de 2023 - 8.1 mil visualizações  ")

st.markdown("---")

st.header("Bibliografia Recomendada de FIIs e Investimentos")
st.subheader("Obras essenciais para aprofundar seus conhecimentos")

st.markdown("""
- **GRAHAM, Benjamin. O Investidor Inteligente**. Rio de Janeiro: Elsevier, 2012.  
- **FISHER, Philip A. Ações Comuns, Lucros Extraordinários**. São Paulo: Ática, 2016.  
- **LYNCH, Peter. One Up on Wall Street: Como qualquer um pode investir com sucesso na bolsa de valores**. São Paulo: BestSeller, 2013.  
- **BARONI, Marcelo; BASTOS, Denis. Guia Suno Fundos Imobiliários: Introdução sobre investimentos seguros e rentáveis**. Paulínia, SP: Vivalendo, 2019.  
- **NAKAMA, Vanessa K. Do financiamento à financeirização: a reestruturação do espaço pelos FIIs em São Paulo**. São Paulo: USP, 2022.  
""")

