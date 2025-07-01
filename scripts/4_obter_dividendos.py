import os
import time
import requests
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from calendar import monthrange
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()
EMAIL = os.getenv("PLEXA_EMAIL")
SENHA = os.getenv("PLEXA_SENHA")
TOKEN = os.getenv("PLEXA_TOKEN")

LOGIN_ENDPOINT     = 'https://api.plexa.com.br/site/login'
DIVIDENDO_ENDPOINT = 'https://api.plexa.com.br/json/dividendo/{ticker}/{meses}'

ROOT_DIR      = Path(__file__).resolve().parent.parent
DB_PATH       = ROOT_DIR / "data" / "fiis.db"

PAUSA         = 1        # segundos entre chamadas
MESES_BUSCA   = 5000     # quantidade de meses para buscar
TIMEOUT       = 15       # timeout HTTP
MAX_RETRIES   = 3
BACKOFF_FACTOR= 0.3


def create_session():
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def abrir_conexao_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def autenticar(session):
    """Reautentica e atualiza TOKEN no .env"""
    global TOKEN
    resp = session.post(
        LOGIN_ENDPOINT,
        json={"usuEmail": EMAIL, "usuSenha": SENHA},
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT
    )
    resp.raise_for_status()
    data = resp.json()
    if 'accessToken' not in data:
        raise RuntimeError(f"Falha na autenticação: {data}")
    TOKEN = data['accessToken']
    # Atualiza .env
    env_path = ROOT_DIR / ".env"
    lines = env_path.read_text(encoding='utf-8').splitlines()
    with open(env_path, 'w', encoding='utf-8') as f:
        for l in lines:
            if l.startswith('PLEXA_TOKEN='):
                f.write(f"PLEXA_TOKEN={TOKEN}\n")
            else:
                f.write(l + "\n")

def obter_dividendos(session, ticker, meses=MESES_BUSCA):
    """Chama o endpoint e trata 401 para reautenticar automaticamente."""
    url = DIVIDENDO_ENDPOINT.format(ticker=ticker, meses=meses)
    headers = {"Authorization": f"Bearer {TOKEN}"}
    resp = session.get(url, headers=headers, timeout=TIMEOUT)
    if resp.status_code == 401:
        autenticar(session)
        headers["Authorization"] = f"Bearer {TOKEN}"
        resp = session.get(url, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get('data', []) if payload.get('ok') else []

def salvar_dividendos(pausa=PAUSA):
    conn = abrir_conexao_db()
    cur  = conn.cursor()
    session = create_session()

    # Garante índice de unicidade
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

    total_api      = 0
    total_inserted = 0

    for fii_id, ticker in fiis:
        print(f"\n🔎 Processando {ticker}…")
        try:
            entries = obter_dividendos(session, ticker, meses=MESES_BUSCA)
        except Exception as e:
            print(f"   ⚠ Erro ao obter {ticker}: {e}")
            time.sleep(pausa)
            continue

        total_api += len(entries)
        print(f"   → {len(entries)} registros na API")

        # data de referência máximo já gravado
        cur.execute(
            "SELECT MAX(data_referencia) FROM fiis_indicadores WHERE fii_id=? AND indicador_id=?",
            (fii_id, ind_id)
        )
        ultima = cur.fetchone()[0]

        registros = []
        for item in entries:
            # filtra apenas RENDIMENTO
            tipo_key = next((k for k in item if k.strip().lower()=='tipo'), None)
            tipo = item.get(tipo_key,'') if tipo_key else ''
            if 'RENDIMENTO' not in tipo.upper():
                continue

            # data_referencia
            mes_ref = item.get('mesReferencia','')
            try:
                m, y = mes_ref.split('/')
                ultimo_dia = monthrange(int(y), int(m))[1]
                dt = date(int(y), int(m), ultimo_dia)
            except:
                try:
                    dt = datetime.strptime(item.get('dataCom',''), '%d/%m/%Y').date()
                except:
                    continue

            # não grava meses futuros
            hoje      = date.today()
            ultimo_mes= (hoje.replace(day=1) - timedelta(days=1))
            if dt > ultimo_mes:
                continue

            date_ref = dt.isoformat()
            # pula duplicatas e já gravados
            if ultima and date_ref <= ultima:
                continue

            # valor numérico
            try:
                valor = float(item.get('valor','').replace('.','').replace(',','.'))
            except:
                continue

            registros.append((fii_id, ind_id, date_ref, valor))

        print(f"   → {len(registros)} novos para inserir")
        if registros:
            try:
                cur.executemany(
                    # ignora duplicatas pelo índice único
                    "INSERT OR IGNORE INTO fiis_indicadores(fii_id, indicador_id, data_referencia, valor) VALUES (?,?,?,?)",
                    registros
                )
                conn.commit()
                inseridos = cur.rowcount
                total_inserted += inseridos
                print(f"   + {inseridos} inseridos")
            except Exception as e:
                print(f"   ⚠ Erro ao inserir no banco: {e}")

        if pausa:
            time.sleep(pausa)

    conn.close()
    print(f"\n✅ Total analisados: {total_api}")
    print(f"✅ Total inseridos: {total_inserted}")

if __name__ == '__main__':
    # autentica antes, se necessário
    session = create_session()
    if not TOKEN:
        autenticar(session)
    salvar_dividendos()
