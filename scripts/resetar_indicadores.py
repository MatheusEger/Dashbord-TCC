import sqlite3
from pathlib import Path

# Caminho para o banco de dados
DB_PATH = Path("V:/Dashbord-TCC/data/fiis.db")

# Conectar ao banco
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()


# Apagar a tabela (se existir)
#cur.execute("DROP TABLE IF EXISTS fiis;")

# Criar a tabela novamente
#cur.execute("""
#        );
#    """)

# Inserir os indicadores padrão
indicadores_padrao = [
    ("P/VP", "Preço sobre Valor Patrimonial"),
    ("Dividend Yield Último", "Yield do último mês divulgado (%)"),
    ("Dividend Yield 3M", "Dividend Yield acumulado em 3 meses (%)"),
    ("Dividend Yield 6M", "Dividend Yield acumulado em 6 meses (%)"),
    ("Dividend Yield 12M", "Dividend Yield acumulado em 12 meses (%)")
]

for nome, descricao in indicadores_padrao:
    cur.execute("INSERT INTO indicadores (nome, descricao) VALUES (?, ?)", (nome, descricao))

# Inserir "Dividendos"
#cur.execute("INSERT INTO indicadores (nome, descricao) VALUES (?, ?)", 
#            ('Dividendos', 'Rendimentos distribuídos mensalmente'))

conn.commit()
conn.close()

print("Tabela 'indicadores' resetada e preenchida com sucesso.")
