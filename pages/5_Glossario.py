# --- Arquivo: pages/4_por_onde_comecar.py ---
import streamlit as st

# Deve ser a primeira chamada Streamlit no arquivo
st.set_page_config(page_title="Por onde começar", layout="wide")

# Aviso de compliance
st.warning(
    "Este conteúdo é apenas informativo e não constitui recomendação de investimento. "
    "Para receber recomendações, consulte um profissional certificado CNPI."
)

# Cabeçalho
st.title("🚀 Por onde começar a investir em FIIs")

st.markdown(
    "O mercado de Fundos de Investimento Imobiliário (FIIs) oferece oportunidades de renda passiva e diversificação. "
    "Siga estes passos iniciais para começar com segurança:"  
)

with st.expander("1. Defina seu valor inicial"):
    st.write(
        "- Determine um valor que não comprometa seu orçamento mensal."
        "\n- Verifique o investimento mínimo exigido pela corretora."
    )

with st.expander("2. Escolha uma corretora confiável"):
    st.write(
        "- Opte por plataformas reconhecidas (XP, Clear, Rico etc.)."
        "\n- Conclua o cadastro e habilite investimentos em FIIs."
    )

with st.expander("3. Entenda os tipos de FIIs"):
    st.write(
        "- Logística, Shoppings, Recebíveis, Escritórios, Híbridos etc."
        "\n- Cada setor apresenta riscos e rendimentos distintos."
    )

with st.expander("4. Diversifique sua carteira"):
    st.write(
        "- Não concentre todo o capital em um único FII."
        "\n- Defina percentuais de alocação por setor."
    )

with st.expander("5. Monitoramento e rebalanceamento"):
    st.write(
        "- Acompanhe seus investimentos a cada 6–12 meses."
        "\n- Reinvista os proventos de acordo com indicadores."
    )

# Recursos de apoio
st.header("📺 Vídeos para iniciantes")
st.video("https://www.youtube.com/watch?v=W4wgdekEjuI")
st.video("https://www.youtube.com/watch?v=Q7guEK_o3o0")


# --- Arquivo: pages/5_glossario.py ---
import streamlit as st

# Deve ser a primeira chamada Streamlit no arquivo
st.set_page_config(page_title="Glossário de FIIs", layout="wide")

# Cabeçalho
st.title("📖 Glossário Completo de FIIs e Indicadores")

# Definições básicas
st.header("O que é um FII?")
st.write(
    "Fundo de Investimento Imobiliário (FII) é um condomínio fechado que capta recursos de investidores "
    "para aplicar em empreendimentos imobiliários ou ativos do setor."
)

st.header("O que é um Ticker?")
st.write(
    "O ticker é o código de negociação do FII na bolsa. Geralmente tem 4 letras seguidas de '11'. "
    "As primeiras letras identificam a gestora ou nome do fundo, e '11' indica que é um FII."
)

# Indicadores principais
st.header("📊 Indicadores e Fórmulas")
indicators = {
    "Dividend Yield (DY)": "(Total de dividendos pagos no período ÷ preço da cota) × 100",
    "P/VP": "Preço da cota ÷ Valor Patrimonial por cota",
    "Vacância Física": "% de área vaga = 100% - % de ocupação",
    "Número de Cotistas": "Total de investidores detentores de cotas",
    "Valor Patrimonial por Ação (VPA)": "Patrimônio Líquido ÷ número de cotas",
    "Cap Rate": "Receita anual de aluguéis ÷ valor de mercado dos imóveis",
    "Volatilidade": "Desvio padrão dos retornos mensais da cota",
}
for name, formula in indicators.items():
    st.subheader(name)
    st.write(f"**Fórmula:** {formula}")
    st.write("- Definição e interpretação do indicador.")

# Como usar no dashboard
st.header("Como interpretar no Dashboard")
st.write(
    "Use filtros de setor e período, compare diferentes indicadores e selecione o FII que melhor se encaixa "
    "no seu perfil de risco e objetivo financeiro."
)
