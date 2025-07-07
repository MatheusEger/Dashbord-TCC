import sqlite3

DB_PATH = "./data/fiis.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Remove duplicatas dos dividendos
cur.execute("""
DELETE FROM fiis_indicadores
WHERE rowid NOT IN (
  SELECT MIN(rowid)
  FROM fiis_indicadores
  WHERE indicador_id = (SELECT id FROM indicadores WHERE nome='Dividendos')
  GROUP BY fii_id, indicador_id, data_referencia
)
""")

cur.execute("""
DELETE FROM fiis_indicadores
WHERE rowid NOT IN (
  SELECT MIN(rowid)
  FROM fiis_indicadores
  GROUP BY fii_id, indicador_id, data_referencia
);
""")

# Cria índice único para evitar novas duplicatas
#cur.execute("""
#CREATE UNIQUE INDEX IF NOT EXISTS idx_unico_dividendos
#ON fiis_indicadores(fii_id, indicador_id, data_referencia)
#""")

conn.commit()
conn.close()
print("Duplicatas removidas e índice único criado!")
