import os
import time
import requests
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from dotenv import load_dotenv
from calendar import monthrange

# Carrega variáveis de ambiente
load_dotenv()
EMAIL = os.getenv("PLEXA_EMAIL")
SENHA = os.getenv("PLEXA_SENHA")
TOKEN = os.getenv("PLEXA_TOKEN")

LOGIN_ENDPOINT = 'https://api.plexa.com.br/site/login'
DIVIDENDO_ENDPOINT = 'https://api.plexa.com.br/json/dividendo/{ticker}/{meses}'

# Caminho do banco de dados
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"
ENV_PATH = ROOT_DIR / ".env"

def abrir_conexao_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def autenticar():
    global TOKEN
    resp = requests.post(
        LOGIN_ENDPOINT,
        json={"usuEmail": EMAIL, "usuSenha": SENHA},
        headers={"Content-Type": "application/json"},
        timeout=15
    )
    resp.raise_for_status()
    data = resp.json()
    if 'accessToken' in data:
        TOKEN = data['accessToken']
        linhas = ENV_PATH.read_text(encoding='utf-8').splitlines()
        with open(ENV_PATH, 'w', encoding='utf-8') as f:
            for l in linhas:
                if l.startswith('PLEXA_TOKEN='):
                    f.write(f"PLEXA_TOKEN={TOKEN}\n")
                else:
                    f.write(l + "\n")
        print("✔ Token atualizado.")
    else:
        raise RuntimeError(f"Falha na autenticação: {data}")

def obter_dividendos(ticker, meses=3600):
    url = DIVIDENDO_ENDPOINT.format(ticker=ticker, meses=meses)
    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {TOKEN}"},
            timeout=15
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"[{ticker}] nada encontrado (404)")
            return []
        else:
            raise
    payload = resp.json()
    return payload.get('data', []) if payload.get('ok') else []

def salvar_dividendos(pausa=1):
    print(f"🚀 Iniciando importação de dividendos em {DB_PATH}")
    conn = abrir_conexao_db()
    cur = conn.cursor()

    # Índice único para evitar duplicatas
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_divs_unicidade
        ON fiis_indicadores(fii_id, indicador_id, data_referencia)
    """)

    # Carrega FIIs
    cur.execute("SELECT id, ticker FROM fiis")
    fiis = cur.fetchall()

    # Busca ou cria indicador 'Dividendos'
    cur.execute("SELECT id FROM indicadores WHERE LOWER(nome)='dividendos'")
    row = cur.fetchone()
    if row:
        ind_id = row[0]
    else:
        cur.execute(
            "INSERT INTO indicadores(nome,descricao) VALUES(?,?)",
            ("Dividendos", "Rendimentos distribuídos mensalmente")
        )
        ind_id = cur.lastrowid
        print(f"✔ Indicador 'Dividendos' criado: id={ind_id}")

    total_api = 0
    total_inserted = 0

    for fii_id, ticker in fiis:
        print(f"\n🔎 Processando {ticker}…")
        entries = obter_dividendos(ticker, meses=3600)
        total_api += len(entries)
        print(f"   → {len(entries)} registros na API para {ticker}")

        # contador local para este ticker
        inserted_this = 0

        for item in entries:
            # Filtrar apenas rendimentos (detecta chave 'tipo' com ou sem espaço)
            tipo_key = next((k for k in item.keys() if k.strip().lower() == 'tipo'), None)
            tipo = item.get(tipo_key, '') if tipo_key else ''
            if 'RENDIMENTO' not in tipo.upper():
                continue

            # Extrai data_referencia (prioriza mesReferencia)
            mes_ref = item.get('mesReferencia', '')
            try:
                m, y = mes_ref.split('/')
                ultimo_dia = monthrange(int(y), int(m))[1]
                dt = date(int(y), int(m), ultimo_dia)
            except Exception:
                # fallback para dataCom
                try:
                    dt = datetime.strptime(item.get('dataCom', ''), '%d/%m/%Y').date()
                except Exception:
                    continue

            # Filtra meses futuros
            hoje = date.today()
            ultimo_mes = (hoje.replace(day=1) - timedelta(days=1))
            if dt > ultimo_mes:
                continue

            date_ref = dt.isoformat()
            val_str = item.get('valor', '')
            try:
                valor = float(val_str.replace('.', '').replace(',', '.'))
            except Exception:
                continue

            # Verifica duplicata
            cur.execute(
                "SELECT 1 FROM fiis_indicadores WHERE fii_id=? AND indicador_id=? AND data_referencia=?",
                (fii_id, ind_id, date_ref)
            )
            if cur.fetchone():
                continue

            # Insere registro
            cur.execute(
                "INSERT INTO fiis_indicadores(fii_id, indicador_id, data_referencia, valor) VALUES(?,?,?,?)",
                (fii_id, ind_id, date_ref, valor)
            )
            inserted_this += 1
            total_inserted += 1
            print(f"   + Inseriu: {ticker} | {date_ref} | R$ {valor}")

        # resumo por ticker
        print(f"   → Inseridos para {ticker}: {inserted_this}")

        if pausa:
            time.sleep(pausa)

    conn.commit()
    conn.close()

    print(f"\n✅ Total registros API analisados: {total_api}")
    print(f"✅ Total novos inseridos: {total_inserted}")

if __name__ == '__main__':
    if not TOKEN:
        autenticar()
    salvar_dividendos()
