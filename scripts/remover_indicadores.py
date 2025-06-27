import sqlite3
from pathlib import Path

# Caminho para o banco de dados
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"

# Conecta ao banco
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()


# Excluir dados das tabelas
cur.execute("DELETE FROM indicadores WHERE id IN (1)")
# cur.execute("DELETE FROM indicadores WHERE id IN (5, 6 , 7, 8, 9, 10, 11, 12, 13)")

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

print("Indicadores 5, 6 , 7, 8, 9, 10, 11, 12, 13 e seus dados relacionados foram removidos com sucesso.")
