import os
import json
import sqlite3
import requests

# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
# Configurações de caminho
BASE_DIR   = os.path.dirname(__file__)
ROOT_DIR   = os.path.abspath(os.path.join(BASE_DIR, '..'))          # volta para a raiz do projeto
JSON_PATH  = os.path.join(ROOT_DIR, 'database', 'dados_fundos.json') # agora aponta para database/
DB_PATH    = os.path.join(ROOT_DIR, 'data', 'fiis.db')  

# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
# 1) Carrega JSON e monta dicionário {ticker: segmento}
with open(JSON_PATH, 'r', encoding='utf-8') as f:
    dados = json.load(f)['data']

segmentos_por_ticker = {
    d['ticker']: d.get('segmento', '').strip().upper()
    for d in dados
}

# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
# 2) Define mapeamento segmento → tipo
mapeamento_tipo = {
    # FUNDOS DE PAPEL
    'RECEBÍVEIS IMOBILIÁRIOS': 'Papel',
    'TÍTULOS E VAL. MOB.':     'Papel',
    'INFRA':                    'Papel',
    'AGRONEGÓCIO':              'Papel',
    # FUNDOS DE TIJOLO
    'SHOPPING/VAREJO':          'Tijolo',
    'LAJES COMERCIAIS':         'Tijolo',
    'LAJES CORPORATIVAS':       'Tijolo',
    'LOGÍSTICOS':               'Tijolo',
    'INCORPORAÇÃO':             'Tijolo',
    'INCORPORAÇÃO RESIDENCIAL': 'Tijolo',
    'RESIDENCIAL':              'Tijolo',
    'HOTEIS':                   'Tijolo',
    # FUNDO DE FUNDOS
    'FUNDO DE FUNDOS':          'Fundo de Fundos',
    # MULTI / HÍBRIDO
    'MULTIESTRATÉGIA':          'Multiestratégia',
    'HÍBRIDO':                  'Multiestratégia',
    # genéricos agora mapeiam para 'Outros'
    'N/D':                      'Outros',
    'OUTROS':                   'Outros',
}

def atualiza_tipos_de_fiis(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # — Cria tabela de tipos (se não existir)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tipo_fii (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        nome      TEXT NOT NULL UNIQUE,
        descricao TEXT
    );
    """)

    # — Povoamento inicial com categoria “Outros”
    categorias = [
        ('Papel',           'Fundos de Papel (CRI, LCI, LIG etc.)'),
        ('Tijolo',          'Fundos de Tijolo (imóveis físicos)'),
        ('Fundo de Fundos', 'FOFs'),
        ('Multiestratégia','Fundos Multiestratégia / Híbridos'),
        ('Outros',          'Segmentos diversos não categorizados'),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO tipo_fii(nome,descricao) VALUES(?,?);",
        categorias
    )

    # — Garante coluna tipo_id em fiis
    try:
        cur.execute("ALTER TABLE fiis ADD COLUMN tipo_id INTEGER;")
    except sqlite3.OperationalError:
        pass  # coluna já existe

    # — Atualiza cada FII sem tipo atribuído
    cur.execute("SELECT id, ticker FROM fiis WHERE tipo_id IS NULL;")
    for fii_id, ticker in cur.fetchall():
        tipo_str = None

        # (1) Tenta obter via API Plexa
        resp = requests.get(f'https://api.plexa.com.br/json/fundos/{ticker}')
        if resp.ok:
            tipo_str = resp.json().get('tipoFundo')

        # (2) Se API não tiver, faz fallback via JSON + mapeamento
        if not tipo_str:
            seg = segmentos_por_ticker.get(ticker, '')
            tipo_str = mapeamento_tipo.get(seg, 'Outros')
            print(f'  • {ticker}: segmento="{seg}" → tipo="{tipo_str}"')

        # — Busca (ou insere) o ID na tabela tipo_fii
        cur.execute("SELECT id FROM tipo_fii WHERE nome = ?;", (tipo_str,))
        row = cur.fetchone()
        if row:
            tipo_id = row[0]
        else:
            cur.execute("INSERT INTO tipo_fii(nome) VALUES(?);", (tipo_str,))
            tipo_id = cur.lastrowid
            print(f'  ✓ Novo tipo inserido: {tipo_str} (id={tipo_id})')

        # — Atualiza o registro de FII
        cur.execute(
            "UPDATE fiis SET tipo_id = ? WHERE id = ?;",
            (tipo_id, fii_id)
        )

    conn.commit()
    conn.close()
    print("Tipos de FIIs atualizados com sucesso.")


# —––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
if __name__ == '__main__':
    # … aqui vem o seu fluxo normal de ETL/carregamento de dados …
    
    # E então:
    atualiza_tipos_de_fiis()
