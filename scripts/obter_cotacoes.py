import requests
import sqlite3
import time
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
EMAIL = os.getenv("PLEXA_EMAIL")
SENHA = os.getenv("PLEXA_SENHA")
TOKEN = os.getenv("PLEXA_TOKEN")

LOGIN_ENDPOINT = 'https://api.plexa.com.br/site/login'
COTACAO_ENDPOINT = 'https://api.plexa.com.br/json/historico/{ticker}/3600'

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"
ENV_PATH = ROOT_DIR / ".env"

def salvar_token_no_env(token):
    with open(ENV_PATH, 'r') as file:
        linhas = file.readlines()
    with open(ENV_PATH, 'w') as file:
        for linha in linhas:
            if linha.startswith("PLEXA_TOKEN="):
                file.write(f"PLEXA_TOKEN={token}\n")
            else:
                file.write(linha)

def autenticar():
    global TOKEN
    print(f"Tentando autenticar com email: {EMAIL}")
    response = requests.post(LOGIN_ENDPOINT, json={
        'usuEmail': EMAIL,
        'usuSenha': SENHA,
    }, headers={'Content-Type': 'application/json'})

    if response.status_code == 200 and 'accessToken' in response.json():
        TOKEN = response.json()['accessToken']
        salvar_token_no_env(TOKEN)
        print("Autenticação bem sucedida!")
        return TOKEN
    else:
        print("Erro ao autenticar:", response.text)
        return None

def parse_float(valor):
    return float(valor.replace(".", "").replace(",", "."))

def salvar_cotacoes_todos():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, ticker FROM fiis")
    fiis = cur.fetchall()

    total_inseridos = 0

    for fii_id, ticker in fiis:
        print(f"Buscando cotações de {ticker}...")
        try:
            url = COTACAO_ENDPOINT.format(ticker=ticker)
            headers = {
                "Authorization": f"Bearer {TOKEN}",
                "User-Agent": "Mozilla/5.0"
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 401:
                print(f"Token expirado. Reautenticando...")
                autenticar()
                headers["Authorization"] = f"Bearer {TOKEN}"
                response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Erro {response.status_code} ao obter dados de {ticker}")
                continue

            dados = response.json().get("data", [])
            registros = []
            now = datetime.now().isoformat()

            for item in dados:
                try:
                    if not item["data"]:
                        continue
                    data = datetime.strptime(item["data"], "%d/%m/%Y").date().isoformat()
                    fechamento = parse_float(item["fechamento"])
                    abertura = parse_float(item["abertura"])
                    maxima = parse_float(item["maxima"])
                    minima = parse_float(item["minima"])
                    totNegocios = parse_float(item["totNegocios"])
                    qtdNegociada = parse_float(item["qtdNegociada"])
                    volume = parse_float(item["volume"])
                    registros.append((
                        fii_id, data, fechamento, abertura, maxima, minima,
                        totNegocios, qtdNegociada, volume, now
                    ))
                except Exception as e:
                    print(f"Erro ao processar cotação de {ticker}: {e}")

            cur.executemany("""
                INSERT INTO cotacoes (
                    fii_id, data, preco_fechamento, abertura, maxima, minima,
                    totNegocios, qtdNegociada, volume, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, registros)

            total_inseridos += len(registros)
            time.sleep(1)

        except Exception as e:
            print(f"Erro ao processar {ticker}: {e}")

    conn.commit()
    conn.close()
    print(f"Total de cotações inseridas: {total_inseridos}")

if __name__ == "__main__":
    if not TOKEN:
        TOKEN = autenticar()
    if TOKEN:
        salvar_cotacoes_todos()
    else:
        print("Token inválido.")
