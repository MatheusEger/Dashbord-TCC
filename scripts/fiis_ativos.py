#!/usr/bin/env python
from pathlib import Path
import sqlite3
import pandas as pd

# 1) Ajuste o caminho para o seu banco
BASE_DIR = Path(__file__).resolve().parent.parent
db_path  = BASE_DIR / "data" / "fiis.db"

# 2) Conecta
conn = sqlite3.connect(str(db_path))

# 3) Cria a coluna 'ativo' se ainda não existir
try:
    conn.execute("ALTER TABLE fiis ADD COLUMN ativo INTEGER DEFAULT 0;")
except sqlite3.OperationalError:
    # coluna já existe
    pass

# 4) Lê a última data de cotação de cada FII
df_ult = pd.read_sql("""
    SELECT fii_id, MAX(data) AS ultima_data
    FROM cotacoes
    GROUP BY fii_id
""", conn, parse_dates=['ultima_data'])

# 5) Define o cutoff de 90 dias
corte = pd.Timestamp.today().normalize() - pd.Timedelta(days=90)

# 6) Marca 1 para ativos (cotação dentro dos últimos 90 dias), 0 caso contrário
df_ult['ativo'] = (df_ult['ultima_data'] >= corte).astype(int)

# 7) Atualiza o banco
for _, row in df_ult.iterrows():
    conn.execute(
        "UPDATE fiis SET ativo = ? WHERE id = ?;",
        (int(row['ativo']), int(row['fii_id']))
    )

conn.commit()
conn.close()
print(f"Processo concluído: atualizado 'ativo' para {len(df_ult)} FIIs.")
