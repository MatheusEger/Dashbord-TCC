import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

st.title("📋 Lista Completa de FIIs")

# Conexão com banco
def carregar_dados():
    DB_PATH = Path(__file__).parents[1] / "data" / "fiis.db"
    conn = sqlite3.connect(DB_PATH)
    fiis = pd.read_sql("""
        SELECT f.ticker, f.nome, s.nome as setor
        FROM fiis f
        JOIN setor s ON f.setor_id = s.id
    """, conn)
    conn.close()
    return fiis

fiis = carregar_dados()

# Filtro por segmento
disponiveis = sorted(fiis['setor'].unique())
segmento_filtro = st.multiselect("Filtrar por Segmento:", options=disponiveis, default=disponiveis)
fiis_filtrados = fiis[fiis['setor'].isin(segmento_filtro)]

st.dataframe(fiis_filtrados, use_container_width=True)
