import os
import time
import requests
import sqlite3
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

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

# Conecta DB e ativa WAL
def abrir_conexao_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

# Autentica na Plexa
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

# Obtém dividendos da API
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

# Salva dataCom + valor, sem duplicar, usando SELECT antes de INSERT
def salvar_dividendos(pausa=1):
    print(f"🚀 Iniciando importação de dividendos em {DB_PATH}")
    conn = abrir_conexao_db()
    cur = conn.cursor()

    # Carrega FIIs
    cur.execute("SELECT id, ticker FROM fiis")
    fiis = cur.fetchall()
    print(f"Total FIIs: {len(fiis)}")

    # Busca indicador 'Dividendos'
    cur.execute("SELECT id FROM indicadores WHERE LOWER(nome)='dividendos'")
    row = cur.fetchone()
    if row:
        ind_id = row[0]
    else:
        cur.execute(
            "INSERT INTO indicadores(nome,descricao) VALUES(?,?)", 
            ("Dividendos","Rendimentos distribuídos mensalmente")
        )
        ind_id = cur.lastrowid
        print(f"✔ Indicador 'Dividendos' criado: id={ind_id}")
    print(f"🔍 Usando indicador_id = {ind_id}")

    count_api = 0
    count_inserted = 0

    for fii_id, ticker in fiis:
        print(f"\n🔎 Processando {ticker}…")
        entries = obter_dividendos(ticker)
        print(f"   → {len(entries)} registros na API para {ticker}")

        for item in entries:
            data_com = item.get('dataCom', '').strip()
            valor_str = item.get('valor', '').strip()
            if not data_com or not valor_str:
                continue
            count_api += 1

            # Parse dataCom
            try:
                dt = datetime.strptime(data_com, '%d/%m/%Y')
                date_ref = dt.date().isoformat()
            except Exception:
                print(f"   ⚠ dataCom inválida para {ticker}: {data_com}")
                continue

            # Parse valor
            try:
                valor = float(valor_str.replace('.', '').replace(',', '.'))
            except Exception:
                print(f"   ⚠ valor inválido para {ticker}: {valor_str}")
                continue

            # Verifica duplicação via SELECT
            cur.execute(
                "SELECT 1 FROM fiis_indicadores WHERE fii_id=? AND indicador_id=? AND data_referencia=?",
                (fii_id, ind_id, date_ref)
            )
            if cur.fetchone():
                # já existe
                continue

            # Insere novo registro
            cur.execute(
                "INSERT INTO fiis_indicadores (fii_id, indicador_id, data_referencia, valor) VALUES (?, ?, ?, ?)",
                (fii_id, ind_id, date_ref, valor)
            )
            print(f"   + Inseriu: {ticker} | {date_ref} | R$ {valor}")
            count_inserted += 1

        if pausa > 0:
            time.sleep(pausa)

    conn.commit()
    conn.close()

    print(f"\n✅ Total API registros: {count_api}")
    print(f"✅ Total novos inseridos: {count_inserted}")

if __name__ == '__main__':
    if not TOKEN:
        autenticar()
    salvar_dividendos()
