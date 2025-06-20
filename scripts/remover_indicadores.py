import sqlite3
from pathlib import Path

# Caminho para o banco de dados
DB_PATH = Path("V:/Dashbord-TCC/data/fiis.db")

# Conecta ao banco
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()


# Excluir dados das tabelas
cur.execute("DELETE FROM fiis_indicadores WHERE indicador_id IN (1, 2, 3, 4, 12, 14, 15, 16)")
"""
indicadores_padrao = [
    ("Vacância Percentual", "Porcentagem de área vaga (%)"),
    ("Vacância m²", "Área vaga em metros quadrados"),
    ("Ocupação Percentual", "Porcentagem de área ocupada (%)"),
    ("Ocupação m²", "Área ocupada em metros quadrados"),
]
cur.executemany("INSERT OR IGNORE INTO indicadores (nome, descricao) VALUES (?, ?)", indicadores_padrao)
"""

#cur.execute("DELETE FROM cotacoes")

conn.commit()
conn.close()

print("Indicadores 1, 2, 3 e 4 e seus dados relacionados foram removidos com sucesso.")
