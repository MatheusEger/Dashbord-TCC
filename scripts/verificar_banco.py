import sqlite3
from pathlib import Path

# Caminho do banco de dados
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"

# Conectar ao banco
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Verificar tabelas
print("Tabelas no banco:")
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
for table in tables:
    print(f"\nTabela: {table[0]}")
    cur.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cur.fetchone()[0]
    print(f"Total de registros: {count}")
    
"""    # Mostrar alguns registros de exemplo
    cur.execute(f"SELECT * FROM {table[0]} LIMIT 5")
    rows = cur.fetchall()
    print("Exemplo de registros:")
    for row in rows:
        print(row)"""

conn.close() 