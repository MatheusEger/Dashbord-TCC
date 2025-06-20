import streamlit as st
import pandas as pd
import plotly.express as px

#    [data-testid="stSidebar"] {
#        display: none;
#    }
#    [data-testid="collapsedControl"] {
#        display: none;
#    }

# Página inicial do dashboard
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="collapsedControl"] {
        display: none;
    }      
    .menu-container {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 3rem;
        flex-wrap: wrap;
    }
    .menu-button {
        background-color: #0E1117;
        border: 2px solid #6c63ff;
        border-radius: 15px;
        color: white;
        padding: 1.5rem 2rem;
        font-size: 1.2rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        min-width: 200px;
    }
    .menu-button:hover {
        background-color: #6c63ff;
        color: black;
    }
    .descricao {
        margin-top: 4rem;
        text-align: center;
        font-size: 1.1rem;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Bem-vindo(a) ao Dashboard de FIIs", layout="nome")

st.markdown("""
<div class="menu-container">
    <a href="/Analise_por_Fundo" class="menu-button">Análise por Fundo</a>
    <a href="/Ranking dos FIIs" class="menu-button">Ranking dos FIIs</a>
    <a href="/Comparador" class="menu-button">Comparador</a>
    <a href="/Ajuda" class="menu-button">Ajuda</a>
</div>

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
