import os
import time
import requests
import sqlite3
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Carrega variáveis de ambiente
load_dotenv()
EMAIL = os.getenv("PLEXA_EMAIL")
SENHA = os.getenv("PLEXA_SENHA")
TOKEN = os.getenv("PLEXA_TOKEN")

# Endpoints
LOGIN_ENDPOINT = 'https://api.plexa.com.br/site/login'
COTACAO_ENDPOINT = 'https://api.plexa.com.br/json/historico/{ticker}/{dias}'

# Configurações
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"
PAUSA = 1           # segundos entre chamadas
DIAS_BUSCA = 3650     # últimos dias
TIMEOUT = 15        # segundos para requisição
MAX_RETRIES = 3     # tentativas de retry
BACKOFF_FACTOR = 0.3

# Cria sessão com retries
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

# Autentica e atualiza token no .env
def autenticar(session):
    global TOKEN
    resp = session.post(
        LOGIN_ENDPOINT,
        json={"usuEmail": EMAIL, "usuSenha": SENHA},
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT
    )
    resp.raise_for_status()
    data = resp.json()
    if 'accessToken' in data:
        TOKEN = data['accessToken']
        env_path = ROOT_DIR / ".env"
        lines = env_path.read_text(encoding='utf-8').splitlines()
        with open(env_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.startswith('PLEXA_TOKEN='):
                    f.write(f"PLEXA_TOKEN={TOKEN}\n")
                else:
                    f.write(line + "\n")
        print("✔ Token atualizado no .env")
    else:
        raise RuntimeError(f"Falha na autenticação: {data}")

# Abre conexão SQLite com WAL
def abrir_conexao_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

# Obtém cotações com retries e tratamento de erros
def obter_cotacoes(session, ticker, dias=DIAS_BUSCA):
    url = COTACAO_ENDPOINT.format(ticker=ticker, dias=dias)
    headers = {"Authorization": f"Bearer {TOKEN}"}
    resp = session.get(url, headers=headers, timeout=TIMEOUT)
    if resp.status_code == 401:
        autenticar(session)
        headers["Authorization"] = f"Bearer {TOKEN}"
        resp = session.get(url, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get('data', []) if payload.get('ok') else []

# Salva cotações incrementalmente
def salvar_cotacoes():
    print(f"🚀 Iniciando importação de cotações em {DB_PATH}")
    conn = abrir_conexao_db()
    cur = conn.cursor()
    session = create_session()

    cur.execute("SELECT id, ticker FROM fiis")
    fiis = cur.fetchall()
    print(f"Total FIIs: {len(fiis)}")

    total_inserted = 0
    for fii_id, ticker in fiis:
        print(f"\n🔎 Processando {ticker}...")
        try:
            dados = obter_cotacoes(session, ticker)
        except Exception as e:
            print(f"   ⚠ Erro ao obter {ticker}: {e}")
            time.sleep(PAUSA)
            continue

        print(f"   → {len(dados)} itens brutos para {ticker}")
        cur.execute("SELECT MAX(data) FROM cotacoes WHERE fii_id = ?", (fii_id,))
        ultima = cur.fetchone()[0]

        registros = []
        for item in dados:
            try:
                dt = datetime.strptime(item['data'], "%d/%m/%Y").date().isoformat()
            except ValueError:
                continue
            if ultima and dt <= ultima:
                continue

            fechamento = float(item['fechamento'].replace('.', '').replace(',', '.'))
            abertura   = float(item['abertura'].replace('.', '').replace(',', '.'))
            maxima     = float(item['maxima'].replace('.', '').replace(',', '.'))
            minima     = float(item['minima'].replace('.', '').replace(',', '.'))
            totNeg     = int(item['totNegocios'].replace('.', ''))
            qtdNeg     = int(item['qtdNegociada'].replace('.', ''))
            volume     = float(item['volume'].replace('.', '').replace(',', '.'))

            registros.append((
                fii_id, dt, fechamento,
                abertura, maxima, minima,
                totNeg, qtdNeg, volume
            ))

        print(f"   → {len(registros)} registros novos para inserir")
        if registros:
            try:
                cur.executemany(
                    "INSERT INTO cotacoes (fii_id, data, preco_fechamento, abertura, maxima, minima, totNegocios, qtdNegociada, volume) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    registros
                )
                conn.commit()
                total_inserted += len(registros)
                print(f"   + {len(registros)} inseridos e commit realizado")
            except Exception as e:
                print(f"   ⚠ Erro ao inserir no banco: {e}")

        time.sleep(PAUSA)

    conn.close()
    print(f"\n✅ Total inseridos: {total_inserted}")

if __name__ == '__main__':
    if not TOKEN:
        session = create_session()
        autenticar(session)
    salvar_cotacoes()
