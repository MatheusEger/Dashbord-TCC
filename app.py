import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

# === Caminho do banco
DB_PATH = Path("data/fiis.db").resolve()

# === Conectar e carregar dados
def carregar_fiis():
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            f.ticker AS Ticker,
            f.nome AS Nome,
            s.nome AS Setor
        FROM fiis f
        LEFT JOIN setor s ON f.setor_id = s.id
        ORDER BY f.ticker;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# === Streamlit UI
st.set_page_config(page_title="Dashboard FIIs", layout="wide")
st.title("📊 Dashboard de Fundos Imobiliários")

df_fiis = carregar_fiis()

st.subheader(f"Total de FIIs: {len(df_fiis)}")
st.dataframe(df_fiis, use_container_width=True)
