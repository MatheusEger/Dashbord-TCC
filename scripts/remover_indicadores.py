import sqlite3
from pathlib import Path

DB_PATH = Path("C:/Dashbord-TCC/data/fiis.db")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Nome do indicador que você quer limpar
nome_indicador = 'Dividendos'

cur.execute("""
    DELETE FROM fiis_indicadores
    WHERE indicador_id IN (
        SELECT id FROM indicadores WHERE nome = ?
    )
""", (nome_indicador,))

conn.commit()
conn.close()
print(f"✅ Removidos todos os '{nome_indicador}' de fiis_indicadores")
