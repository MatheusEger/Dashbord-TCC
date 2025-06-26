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
    """Retorna lista de dividendos."""
    url = DIVIDENDO_ENDPOINT.format(ticker=ticker, meses=meses)
    headers = {"Authorization": f"Bearer {TOKEN}", "User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    dados = resp.json()
    return dados.get('data', []) if dados.get('ok') else []


def salvar_dividendos():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Lista FIIs
    cur.execute("SELECT id, ticker FROM fiis")
    fiis = cur.fetchall()

    # Indicador
    cur.execute("SELECT id FROM indicadores WHERE nome='Dividendos'")
    row = cur.fetchone()
    if row:
        ind_id = row[0]
    else:
        cur.execute("INSERT INTO indicadores(nome,descricao) VALUES(?,?)",
                    ('Dividendos','Rendimentos distribuídos mensalmente'))
        ind_id = cur.lastrowid

    total = 0
    added = 0

    for fii_id, ticker in fiis:
        print(f"Processando {ticker}...")
        divs = obter_dividendos(ticker)
        print(f"  encontrados {len(divs)} registros")
        for item in divs:
            total += 1
            valor = item.get('valor')
            data_com = item.get('dataCom')
            if not valor or not data_com:
                continue

            # parse data
            try:
                dt = datetime.strptime(data_com, '%d/%m/%Y')
            except ValueError:
                continue
            date_ref = dt.date().isoformat()

            # checagem duplicação
            cur.execute(
                "SELECT 1 FROM fiis_indicadores WHERE fii_id=? AND indicador_id=? AND data_referencia=?",
                (fii_id, ind_id, date_ref)
            )
            if cur.fetchone():
                continue

            # insere
            val = float(str(valor).replace('.', '').replace(',', '.'))
            cur.execute(
                "INSERT INTO fiis_indicadores(fii_id,indicador_id,data_referencia,valor) VALUES(?,?,?,?)",
                (fii_id, ind_id, date_ref, val)
            )
            added += 1
        time.sleep(1)

    conn.commit()
    conn.close()
    print(f"Total processados: {total}, inseridos: {added}")

if __name__ == '__main__':
    if not TOKEN:
        autenticar()
    salvar_dividendos()
