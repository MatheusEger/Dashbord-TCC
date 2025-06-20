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
    url = f"https://api.plexa.com.br/json/dividendo/{ticker}/{meses}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Authorization": f"Bearer {TOKEN}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        dados = response.json()

        if not dados.get("ok") or not dados.get("data"):
            print(f"Nenhum dado válido retornado para {ticker}")
            return []

        return dados["data"]

    except Exception as e:
        print(f"Erro ao obter dados de {ticker}: {e}")
        return []

def salvar_dividendos():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, ticker FROM fiis")
    fiis = cur.fetchall()

    # Buscar ou criar o indicador "Dividendos"
    cur.execute("SELECT id FROM indicadores WHERE nome = 'Dividendos'")
    row = cur.fetchone()
    if row:
        indicador_id_dividendo = row[0]
    else:
        cur.execute("INSERT INTO indicadores (nome, descricao) VALUES (?, ?)", ('Dividendos', 'Rendimentos distribuídos mensalmente'))
        indicador_id_dividendo = cur.lastrowid

    inseridos = 0

    for fii_id, ticker in fiis:
        print(f"Processando {ticker}...")
        try:
            dividendos = obter_dividendos(ticker)
            for item in dividendos:
                valor = item.get("valor")
                data_com = item.get("dataCom")

                if valor and data_com:
                    try:
                        data_referencia = datetime.strptime(data_com, "%d/%m/%Y").date().isoformat()
                        valor_parse = float(str(valor).replace('.', '').replace(',', '.'))
                        cur.execute("""
                            INSERT INTO fiis_indicadores (
                                fii_id, indicador_id, data_referencia, valor
                            ) VALUES (?, ?, ?, ?)
                        """, (fii_id, indicador_id_dividendo, data_referencia, valor_parse))
                        inseridos += 1
                    except Exception as e:
                        print(f"Erro ao inserir dado de {ticker} ({data_com}): {e}")
                else:
                    print(f"Dados ausentes ou inválidos para {ticker}: {item}")
            time.sleep(1)

        except Exception as e:
            print(f"Erro ao processar {ticker}: {e}")

    conn.commit()
    conn.close()
    print(f"Dividendos inseridos: {inseridos}")

if __name__ == "__main__":
    if not TOKEN:
        autenticar()
    if TOKEN:
        salvar_dividendos()
    else:
        print("Token inválido.")
