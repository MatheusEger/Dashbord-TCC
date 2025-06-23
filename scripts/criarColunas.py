import sqlite3
from pathlib import Path

DB_PATH = Path("V:/Dashbord-TCC/data/fiis.db")  # ajuste se necessário

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE fiis ADD COLUMN gestao VARCHAR")
    print("Coluna 'gestao' adicionada.")
except sqlite3.OperationalError:
    print("Coluna 'gestao' já existe.")

try:
    cur.execute("ALTER TABLE fiis ADD COLUMN admin VARCHAR")
    print("Coluna 'admin' adicionada.")
except sqlite3.OperationalError:
    print("Coluna 'admin' já existe.")

conn.commit()
conn.close()