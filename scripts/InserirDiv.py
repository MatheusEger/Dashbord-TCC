import sqlite3
import pandas as pd
from pathlib import Path

# --- Caminhos ---
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR   = SCRIPT_DIR.parent
DB_PATH    = ROOT_DIR / "data" / "fiis.db"
CSV_PATH   = ROOT_DIR / "database" / "fiis_dividendos.csv"

# --- Leitura forçando todas as colunas como string ---
df = pd.read_csv(
    CSV_PATH,
    sep=',',               # separador de colunas
    encoding="utf-8-sig",
    dtype=str              # força leitura de tudo como texto
)

# --- Parse da data de pagamento (DD/MM/AAAA) ---
df['Pagamento'] = pd.to_datetime(
    df['Pagamento'],
    dayfirst=True,
    errors='coerce'
)

# --- Função genérica para limpar e converter Valor ---
def parse_valor(s):
    if pd.isna(s):
        return pd.NA
    s = s.strip()
    # caso tenha ponto E vírgula: é formato BR (ex: "1.234,56")
    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    # caso tenha só vírgula: decimal BR (ex: "1234,56")
    elif ',' in s:
        s = s.replace(',', '.')
    # caso tenha só ponto: decimal padrão (ex: "1.1" ou "1234.56")
    #    deixamos como está
    try:
        return float(s)
    except ValueError:
        return pd.NA

# --- Aplica e descarta linhas inválidas ---
df['Valor'] = df['Valor'].apply(parse_valor)
df = df.dropna(subset=['Pagamento', 'Valor'])

# --- Conexão com SQLite (mesmo do seu InserirDiv.py) ---
conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

def garantir_indicador(nome, descricao):
    cur.execute("SELECT id FROM indicadores WHERE LOWER(nome)=?", (nome.lower(),))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO indicadores(nome,descricao) VALUES (?,?)",
        (nome, descricao)
    )
    conn.commit()
    return cur.lastrowid

ind_div = garantir_indicador(
    'Dividendos',
    'Rendimentos (proventos) distribuídos periodicamente'
)

cur.execute("SELECT id, ticker FROM fiis")
fii_map = {ticker.upper(): fii_id for fii_id, ticker in cur.fetchall()}

inserts = []
for _, row in df.iterrows():
    ticker = row['Ticker'].strip().upper()
    fii_id = fii_map.get(ticker)
    if not fii_id:
        continue
    data_ref = row['Pagamento'].strftime('%Y-%m-%d')
    inserts.append((fii_id, ind_div, data_ref, row['Valor']))

if inserts:
    cur.executemany(
        "INSERT OR IGNORE INTO fiis_indicadores(fii_id, indicador_id, data_referencia, valor) VALUES (?,?,?,?)",
        inserts
    )
    print(f"Inseridos {len(inserts)} registros de dividendos.")

conn.commit()
conn.close()
print("✅ Finalizado!")
