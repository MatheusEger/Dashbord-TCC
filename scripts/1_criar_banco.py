import sqlite3
from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "fiis.db"

def criar_banco():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        print(f"Removendo banco existente: {DB_PATH}")
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Setores 
    cur.execute("""
        CREATE TABLE IF NOT EXISTS setor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR UNIQUE
        );
    """)

    # Inserir setores padrão já formatados com iniciais maiúsculas
    setores_padrao = [
    "Agencias Bancarias", "Agronegocio", "Educacional", "Fundo De Fundos", "Hospital",
    "Hoteis", "Hibrido", "Incorporacao", "Incorporacao Residencial", "Infra",
    "Lajes Comerciais", "Lajes Corporativas", "Logisticos", "Outros",
    "Recebiveis Imobiliarios", "Residencial", "Shopping/Varejo"]

    for setor in setores_padrao:
        cur.execute("INSERT OR IGNORE INTO setor (nome) VALUES (?)", (setor,))

    # FIIs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fiis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker VARCHAR NOT NULL UNIQUE,
            nome VARCHAR,
            gestao VARCHAR,
            admin VARCHAR,
            setor_id INTEGER,
            created_at TIMESTAMP,
            FOREIGN KEY (setor_id) REFERENCES setor(id)
        );
    """)

    # Cotações históricas
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

    # Indicadores
    cur.execute("""
        CREATE TABLE IF NOT EXISTS indicadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR UNIQUE,
            descricao VARCHAR
        );
    """)

    # Indicadores padrão
    indicadores_padrao = [
        ('Dividendos', 'Rendimentos distribuídos mensalmente'),
        ("Quantidade de Cotas", "Número de cotas emitidas"),
        ("Patrimônio Líquido", "Valor total do patrimônio do fundo"),
        ("Quantidade de Cotistas", "Número de cotistas cadastrados"),
        ("Vacância Percentual", "Porcentagem de área vaga (%)"),
        ("Vacância m²", "Área vaga em metros quadrados"),
        ("Ocupação Percentual", "Porcentagem de área ocupada (%)"),
        ("Ocupação m²", "Área ocupada em metros quadrados"),
        ("P/VP", "Preço sobre Valor Patrimonial"),
        ("Dividend Yield Último", "Yield do último mês divulgado (%)"),
        ("Dividend Yield 3M", "Dividend Yield acumulado em 3 meses (%)"),
        ("Dividend Yield 6M", "Dividend Yield acumulado em 6 meses (%)"),
        ("Dividend Yield 12M", "Dividend Yield acumulado em 12 meses (%)")]

    for nome, descricao in indicadores_padrao:
        cur.execute("INSERT OR IGNORE INTO indicadores (nome, descricao) VALUES (?, ?)", (nome, descricao))
        
    # Indicadores por FII
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fiis_indicadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fii_id INTEGER,
            indicador_id INTEGER,
            data_referencia DATE,
            valor FLOAT,
            FOREIGN KEY (fii_id) REFERENCES fiis(id),
            FOREIGN KEY (indicador_id) REFERENCES indicadores(id)
        );
    """)

    conn.commit()
    conn.close()
    print(f"Banco de dados criado com sucesso em: {DB_PATH}")

if __name__ == "__main__":
    criar_banco()

