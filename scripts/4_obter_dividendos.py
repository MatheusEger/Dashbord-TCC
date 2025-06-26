import requests
import sqlite3
import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv("PLEXA_EMAIL")
SENHA = os.getenv("PLEXA_SENHA")
TOKEN = os.getenv("PLEXA_TOKEN")

LOGIN_ENDPOINT = 'https://api.plexa.com.br/site/login'
DIVIDENDO_ENDPOINT = 'https://api.plexa.com.br/json/dividendo/{ticker}/{meses}'

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"
ENV_PATH = ROOT_DIR / ".env"

def autenticar():
    global TOKEN
    print(f"Tentando autenticar com email: {EMAIL}")
    response = requests.post(LOGIN_ENDPOINT, json={
        'usuEmail': EMAIL,
        'usuSenha': SENHA,
    }, headers={'Content-Type': 'application/json'})

    if response.status_code == 200 and 'accessToken' in response.json():
        TOKEN = response.json()['accessToken']
        with open(ENV_PATH, 'r') as file:
            linhas = file.readlines()
        with open(ENV_PATH, 'w') as file:
            for linha in linhas:
                if linha.startswith("PLEXA_TOKEN="):
                    file.write(f"PLEXA_TOKEN={TOKEN}\n")
                else:
                    file.write(linha)
        print("Autenticação bem sucedida!")
    else:
        print("Erro ao autenticar:", response.text)


def obter_dividendos(ticker, meses=3600):
    """Busca dados de dividendos para um ticker"""
    url = DIVIDENDO_ENDPOINT.format(ticker=ticker, meses=meses)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Authorization": f"Bearer {TOKEN}"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get('data', []) if data.get('ok') else []


def salvar_dividendos(pausa=float(os.getenv('PAUSA_API', 1))):
    """Salva dividendos no banco, evitando duplicações, usando dataPagamento como referência"""
    # Conecta ao banco
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Verifica tabela fiis_indicadores
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fiis_indicadores';")
    if not cur.fetchone():
        raise Exception(f"Tabela 'fiis_indicadores' não encontrada em {DB_PATH}.")

    # Carrega FIIs
    cur.execute("SELECT id, ticker FROM fiis")
    fiis = cur.fetchall()
    print(f"Total de FIIs para processar: {len(fiis)}")

    # Obtém/insere indicador 'Dividendos'
    cur.execute("SELECT id FROM indicadores WHERE nome = ?", ('Dividendos',))
    row = cur.fetchone()
    if row:
        indicador_id = row[0]
    else:
        cur.execute("INSERT INTO indicadores(nome, descricao) VALUES(?, ?)" ,
                    ('Dividendos', 'Rendimentos distribuídos mensalmente'))
        indicador_id = cur.lastrowid
        print(f"Indicador 'Dividendos' criado com id {indicador_id}")

    total_api = 0
    inserted = 0

    for fii_id, ticker in fiis:
        print(f"[{ticker}] iniciando coleta...")
        try:
            entries = obter_dividendos(ticker)
        except Exception as e:
            print(f"[{ticker}] erro na API: {e}")
            continue

        print(f"[{ticker}] registros na API: {len(entries)}")
        for item in entries:
            total_api += 1
            valor = item.get('valor')
            data_pag = item.get('dataPagamento')
            # Verifica dataPagamento válida
            if not data_pag or data_pag.strip() == '':
                print(f"[{ticker}] pulando sem dataPagamento: {item}")
                continue

            # Parse da data de pagamento
            try:
                dt = datetime.strptime(data_pag, '%d/%m/%Y')
            except ValueError:
                try:
                    dt = datetime.fromisoformat(data_pag)
                except Exception:
                    print(f"[{ticker}] formato de dataPagamento inválido: {data_pag}")
                    continue
            data_ref = dt.date().isoformat()

            # Converte valor, mesmo que zero
            try:
                val = float(str(valor).replace('.', '').replace(',', '.'))
            except Exception:
                print(f"[{ticker}] valor inválido: {valor}")
                continue

            # Verifica duplicação
            cur.execute(
                "SELECT 1 FROM fiis_indicadores WHERE fii_id = ? AND indicador_id = ? AND data_referencia = ?",
                (fii_id, indicador_id, data_ref)
            )
            if cur.fetchone():
                continue

            # Insere dividendos com dataPagamento
            cur.execute(
                "INSERT INTO fiis_indicadores(fii_id, indicador_id, data_referencia, valor) VALUES(?, ?, ?, ?)",
                (fii_id, indicador_id, data_ref, val)
            )
            inserted += 1

        # Pausa entre tickers
        if pausa > 0:
            time.sleep(pausa)

    conn.commit()
    conn.close()

    print(f"Total de registros API processados: {total_api}")
    print(f"Total inseridos no banco: {inserted}")

if __name__ == '__main__':
    if not TOKEN:
        autenticar()
    salvar_dividendos()