import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

#cur.execute("DELETE FROM sqlite_sequence WHERE name = ?", ('fiis_indicadores',))
#cur.execute("DELETE capital_fiis")
cur.execute("DROP TABLE capital_fiis")

#cur.execute("DELETE FROM fiis_indicadores WHERE name = ?", ('fiis_indicadores',))
#cur.execute("""
#        CREATE TABLE IF NOT EXISTS fiis_indicadores (
#            id INTEGER PRIMARY KEY AUTOINCREMENT,
#            fii_id INTEGER,
#            indicador_id INTEGER,
#            data_referencia DATE,
#            valor FLOAT,
#            FOREIGN KEY (fii_id) REFERENCES fiis(id),
#            FOREIGN KEY (indicador_id) REFERENCES indicadores(id)
#        );
#    """)
#

conn.commit()
cur.execute("VACUUM")

conn.close()
print(f"✅ Remoção realizada com sucesso.")
