import sqlite3
from pathlib import Path

# Caminho para o banco de dados
DB_PATH = Path("V:/Dashbord-TCC/data/fiis.db")

# Conectar ao banco
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
""""""
# Apagar a tabela (se existir)
cur.execute("DROP TABLE IF EXISTS cotacoes;")

""# Criar a tabela novamente
cur.execute("""
    CREATE TABLE IF NOT EXISTS cotacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fii_id INTEGER,
        data DATE,
        preco_fechamento FLOAT,
        abertura FLOAT,
        maxima FLOAT,
        minima FLOAT,
        totNegocios FLOAT,
        qtdNegociada FLOAT,
        volume FLOAT,
        created_at TIMESTAMP,
        FOREIGN KEY (fii_id) REFERENCES fiis(id)
    );
    """)

"""# Inserir os indicadores padrão
indicadores_padrao = [
    ("Vacância Percentual", "Porcentagem de área vaga (%)"),
    ("Vacância m²", "Área vaga em metros quadrados"),
    ("Ocupação Percentual", "Porcentagem de área ocupada (%)"),
    ("Ocupação m²", "Área ocupada em metros quadrados")
]

for nome, descricao in indicadores_padrao:
    cur.execute("INSERT INTO indicadores (nome, descricao) VALUES (?, ?)", (nome, descricao))

# Inserir "Dividendos"
cur.execute("INSERT INTO indicadores (nome, descricao) VALUES (?, ?)", 
            ('Dividendos', 'Rendimentos distribuídos mensalmente'))
"""
conn.commit()
conn.close()

print("Tabela 'indicadores' resetada e preenchida com sucesso.")
