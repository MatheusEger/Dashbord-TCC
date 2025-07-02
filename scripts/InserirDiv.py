import sqlite3
import pandas as pd
from pathlib import Path

# Caminhos
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"
CSV_PATH = ROOT_DIR / "database" / "fiis_dividendos.csv"

# Lê o CSV
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
df['Pagamento'] = pd.to_datetime(df['Pagamento'], errors='coerce')

# Conecta ao banco
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Garante os indicadores no banco
def garantir_indicador(nome, descricao):
    cur.execute("SELECT id FROM indicadores WHERE LOWER(nome)=?", (nome.lower(),))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO indicadores(nome,descricao) VALUES (?,?)", (nome, descricao))
    conn.commit()
    return cur.lastrowid

ind_div = garantir_indicador('Dividendos', 'Rendimentos distribuídos mensalmente')
ind_liq = garantir_indicador('Liquidez Média Diária', 'Volume médio de negociações diárias no período')

# Monta um dict para mapear ticker para id
cur.execute("SELECT id, ticker FROM fiis")
fii_map = {ticker.upper(): fii_id for fii_id, ticker in cur.fetchall()}

# Salva dividendos
dividendos = []
for idx, row in df.dropna(subset=['Valor', 'Pagamento']).iterrows():
    ticker = row['Ticker'].upper()
    if ticker not in fii_map:
        continue
    fii_id = fii_map[ticker]
    data_ref = row['Pagamento'][:10] if isinstance(row['Pagamento'], str) else row['Pagamento'].date().isoformat()
    valor = float(row['Valor'])
    dividendos.append((fii_id, ind_div, data_ref, valor))

if dividendos:
    cur.executemany(
        "INSERT OR IGNORE INTO fiis_indicadores(fii_id, indicador_id, data_referencia, valor) VALUES (?,?,?,?)",
        dividendos
    )
    print(f"Inseridos {len(dividendos)} dividendos")

conn.commit()
conn.close()
print("✅ Finalizado!")
