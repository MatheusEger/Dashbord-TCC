import streamlit as st
from streamlit_extras.stylable_container import stylable_container

st.set_page_config(page_title="Dashboard de FIIs", layout="centered")

# Estilo customizado

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
    }

    .menu-container {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 2rem;
        margin-top: 3rem;
    }

    .descricao {
        margin-top: 4rem;
        text-align: center;
        font-size: 1.1rem;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Bem-vindo(a) ao Dashboard de FIIs")

# Navegação com botões internos estilizados
with stylable_container("menu-container", css_styles=""):
    st.page_link("pages/1_Analise_por_Fundo.py", label="Análise por Fundo")
    st.page_link("pages/2_Comparador.py", label="Ranking dos FIIs")
    st.page_link("pages/3_Ranking_dos_FIIs.py", label="Comparador")
    st.page_link("pages/4_Ajuda.py", label="Ajuda")

# Descrição inferior
st.markdown("""
<div class="descricao">
    <p>
        Este dashboard foi desenvolvido para facilitar a análise de Fundos Imobiliários (FIIs), com foco em <strong>investidores iniciantes</strong>.
        Explore os fundos, compare indicadores e descubra oportunidades de forma simples e visual.
    </p>
    <p>
        Cada seção foi pensada para ser intuitiva, interativa e educativa — aproveite a jornada rumo ao seu crescimento financeiro!
    </p>
</div>
""", unsafe_allow_html=True)
