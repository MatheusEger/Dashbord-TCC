from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
import sqlite3
from pathlib import Path
from datetime import datetime

# Funções auxiliares
def limpar_percentual(texto):
    match = re.search(r'(\d{1,3},\d{1,2})%', texto)
    return match.group(1) if match else None

def limpar_area(texto):
    match = re.search(r'([\d\.]+,\d{2})\s*m²', texto)
    return match.group(1) if match else None

# Caminho absoluto do banco
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"

# Conecta ao banco e obtém os tickers
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT ticker FROM fiis;")
tickers = [row[0] for row in cursor.fetchall()]
conn.close()

# Loop pelos tickers
for ticker in tickers:
    driver = None
    try:
        # Inicializa navegador
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument("user-agent=Mozilla/5.0...")
        driver = webdriver.Chrome(options=options)

        print(f"Processando {ticker}...")
        driver.get(f"https://www.clubefii.com.br/fiis/{ticker}")
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        info_div = soup.find("div", class_="info")
        if not info_div:
            print(f"[{ticker}] ⚠️ Nenhum bloco 'info' encontrado.")
            continue

        dados = info_div.find_all("div", recursive=False)
        vacancia_area = dados[0].find("span").text.strip() if len(dados) >= 1 else None
        ocupacao_area = dados[1].find("span").text.strip() if len(dados) >= 2 else None

        vacancia_area_valor = limpar_area(vacancia_area) if vacancia_area else None
        ocupacao_area_valor = limpar_area(ocupacao_area) if ocupacao_area else None

        if vacancia_area_valor and ocupacao_area_valor:
            vaga = float(vacancia_area_valor.replace('.', '').replace(',', '.'))
            ocupa = float(ocupacao_area_valor.replace('.', '').replace(',', '.'))
            total = vaga + ocupa
            vacancia_percentual_valor = round((vaga / total) * 100, 2)
            ocupacao_percentual_valor = round((ocupa / total) * 100, 2)

            print(f"{ticker} - vacância: {vacancia_percentual_valor}% ({vacancia_area_valor} m²)")
            print(f"{ticker} - ocupação: {ocupacao_percentual_valor}% ({ocupacao_area_valor} m²)")

            # Conecta para salvar no banco
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()

            # Busca id do FII
            cur.execute("SELECT id FROM fiis WHERE ticker = ?", (ticker,))
            row = cur.fetchone()
            if not row:
                print(f"[{ticker}] ⚠️ FII não encontrado no banco.")
                conn.close()
                continue
            fii_id = row[0]

            # Busca ids dos indicadores
            cur.execute("SELECT id, nome FROM indicadores WHERE nome IN (?, ?, ?, ?)", (
                "Vacância Percentual", "Vacância m²", "Ocupação Percentual", "Ocupação m²"
            ))
            indicadores = {nome: id for id, nome in cur.fetchall()}

            # Data de referência
            data_ref = datetime.today().strftime("%Y-%m-%d")

            # Função auxiliar
            def inserir(nome, valor):
                if nome in indicadores:
                    cur.execute("""
                        SELECT 1 FROM fiis_indicadores
                        WHERE fii_id = ? AND indicador_id = ? AND data_referencia = ?
                    """, (fii_id, indicadores[nome], data_ref))
                    exists = cur.fetchone()
                    if not exists:
                        cur.execute("""
                            INSERT INTO fiis_indicadores (fii_id, indicador_id, data_referencia, valor)
                            VALUES (?, ?, ?, ?)
                        """, (fii_id, indicadores[nome], data_ref, valor))
                    else:
                        print(f"{ticker} - {nome} já registrado para {data_ref}.")

            inserir("Vacância Percentual", vacancia_percentual_valor)
            inserir("Vacância m²", vaga)
            inserir("Ocupação Percentual", ocupacao_percentual_valor)
            inserir("Ocupação m²", ocupa)

            conn.commit()
            conn.close()

    except Exception as e:
        print(f"Erro ao processar {ticker}: {e}")
    finally:
        if driver:
            driver.quit()