import os
import json
import sqlite3
import requests

# Caminhos
BASE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
JSON_PATH = os.path.join(ROOT_DIR, 'database', 'dados_fundos.json')
DB_PATH = os.path.join(ROOT_DIR, 'data', 'fiis.db')

# Carrega segmentos do JSON
with open(JSON_PATH, 'r', encoding='utf-8') as f:
    dados = json.load(f)['data']
segmentos_por_ticker = {
    d['ticker']: d.get('segmento', '').strip().upper()
    for d in dados
}

# Mapeamento exato de segmento para tipo (conforme dados_fundos.json)
mapeamento_tipo = {
    'RECEBÍVEIS IMOBILIÁRIOS':      'Papel',
    'AGRONEGÓCIO':                  'Papel',
    'SHOPPING/VAREJO':              'Tijolo',
    'LAJES COMERCIAIS':             'Tijolo',
    'LAJES CORPORATIVAS':           'Tijolo',
    'LOGISTICOS':                   'Tijolo',
    'HOTEIS':                       'Tijolo',
    'INCORPORAÇÃO RESIDENCIAL':     'Tijolo',
    'INCORPORAÇÃO':                 'Tijolo',
    'RESIDENCIAL':                  'Tijolo',
    'FUNDO DE FUNDOS':              'Fundo de Fundos',
    'MULTIESTRATÉGIA':              'Multiestratégia',
    'HÍBRIDO':                      'Multiestratégia',
    'INFRA':                        'Papel',
    'TÍTULOS E VAL. MOB.':          'Papel',
    'N/D':                          'Outros',
    'OUTROS':                       'Outros',
}

def atualiza_tipos_de_fiis(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("UPDATE fiis SET tipo_id = NULL;")

    # Cria tabela tipo_fii se não existir
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tipo_fii (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        nome      TEXT NOT NULL UNIQUE,
        descricao TEXT
    );
    """)

    # Insere categorias padrão
    categorias = [
        ('Papel',            'Fundos de Papel (CRI, LCI, LIG etc.)'),
        ('Tijolo',           'Fundos de Tijolo (imóveis físicos)'),
        ('Fundo de Fundos',  'FOFs'),
        ('Multiestratégia',  'Fundos Multiestratégia / Híbridos'),
        ('Outros',           'Segmentos diversos não categorizados'),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO tipo_fii(nome,descricao) VALUES(?,?);",
        categorias
    )

    # Garante coluna tipo_id
    try:
        cur.execute("ALTER TABLE fiis ADD COLUMN tipo_id INTEGER;")
    except sqlite3.OperationalError:
        pass

    # Atualiza cada FII sem tipo
    cur.execute("SELECT id, ticker FROM fiis WHERE tipo_id IS NULL;")
    for fii_id, ticker in cur.fetchall():
        seg = segmentos_por_ticker.get(ticker, '')
        tipo_str = mapeamento_tipo.get(seg, 'Outros')
        print(f'  • {ticker}: segmento="{seg}" → tipo="{tipo_str}"')

        # Busca ou insere tipo_fii
        cur.execute("SELECT id FROM tipo_fii WHERE nome = ?;", (tipo_str,))
        row = cur.fetchone()
        if row:
            tipo_id = row[0]
        else:
            cur.execute("INSERT INTO tipo_fii(nome) VALUES(?);", (tipo_str,))
            tipo_id = cur.lastrowid
            print(f'  ✓ Novo tipo inserido: {tipo_str} (id={tipo_id})')

        # Atualiza fiis
        cur.execute(
            "UPDATE fiis SET tipo_id = ? WHERE id = ?;",
            (tipo_id, fii_id)
        )

    conn.commit()
    conn.close()
    print("Tipos de FIIs atualizados com sucesso.")

if __name__ == '__main__':
    atualiza_tipos_de_fiis()
