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

    # Tipos básicos
    tipos_padrao = [
        ("Papel",           "Fundos de Papel (CRI, LCI etc.)"),
        ("Tijolo",          "Fundos de Tijolo (imóveis físicos)"),
        ("Fundo de Fundos", "FOFs"),
        ("Multiestratégia","Fundos Multiestratégia/Híbridos"),
        ("Outros",         "Segmentos diversos não categorizados")
   ]
    for nome, desc in tipos_padrao:
        cur.execute("INSERT OR IGNORE INTO tipo_fii(nome, descricao) VALUES (?, ?)", (nome, desc))

    # Tabela de Tipos de FII
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tipo_fii (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nome      VARCHAR UNIQUE,
            descricao VARCHAR
        );
    """)

    # FIIs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fiis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker VARCHAR NOT NULL UNIQUE,
            nome VARCHAR,
            gestao VARCHAR,
            admin VARCHAR,
            setor_id INTEGER,
            tipo_id INTEGER,
            created_at TIMESTAMP,
            FOREIGN KEY (setor_id) REFERENCES setor(id),
            FOREIGN KEY (tipo_id)  REFERENCES tipo_fii(id)
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
        ("Quantidade de Cotistas", "Número de cotistas cadastrados")]

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

    # Imoveis
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fiis_imoveis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fii_id INTEGER NOT NULL,
        nome_imovel TEXT    NOT NULL,
        endereco    TEXT    NOT NULL,
        area_m2     REAL,
        num_unidades INTEGER,
        tx_ocupacao    REAL,    -- ex: 94.05 (para 94,05%)
        tx_inadimplencia REAL,  -- ex:  0.00 (para  0,00%)
        pct_receitas   REAL,    -- ex:  9.57 (para  9,57%)
        FOREIGN KEY (fii_id) REFERENCES fiis(id)
        );
    """)

    # E criamos também o índice para tornar JOINs/filtros por fii_id mais rápidos:
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_fiis_imoveis_fii_id
    ON fiis_imoveis(fii_id);
    """)
    conn.commit()
    conn.close()
    print(f"Banco de dados criado com sucesso em: {DB_PATH}")

if __name__ == "__main__":
    criar_banco()

