import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

#cur.execute("DELETE FROM sqlite_sequence WHERE name = ?", ('tipo_fii',))

cur.execute("DELETE FROM fiis_indicadores")
cur.execute("DELETE FROM sqlite_sequence WHERE name = ?", ('fiis_indicadores',))

conn.commit()
cur.execute("VACUUM")

conn.close()
print(f"✅ Remoção realizada com sucesso.")
