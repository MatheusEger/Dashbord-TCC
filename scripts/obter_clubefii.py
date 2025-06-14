from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
import sqlite3
from pathlib import Path

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
cursor.execute("SELECT ticker FROM fiis LIMIT 30;")
tickers = [row[0] for row in cursor.fetchall()]
conn.close()

# Loop pelos tickers
for ticker in tickers:
    driver = None
    try:

        # Inicialização do Chrome
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument("user-agent=Mozilla/5.0...")
        driver = webdriver.Chrome(options=options)

        print(f"Processando {ticker}...")
        driver.get(f"https://www.clubefii.com.br/fiis/{ticker}")
        time.sleep(3)  # Pequeno delay para garantir carregamento

        # Parsing do conteúdo HTML
        soup = BeautifulSoup(driver.page_source, "html.parser")
        info_div = soup.find("div", class_="info")
        
        if not info_div:
            print(f"[{ticker}] ⚠️ Nenhum bloco 'info' encontrado.")
            continue

        dados = info_div.find_all("div", recursive=False) if info_div else []

        vacancia_label = vacancia_percentual = vacancia_area = None
        ocupacao_label = ocupacao_percentual = ocupacao_area = None

        if len(dados) >= 1:
            try:
                vacancia_label = dados[0].find_all("strong")[0].text.strip()
                strongs_vac = dados[0].find_all("strong")
                if len(strongs_vac) >= 2:
                    vacancia_percentual = strongs_vac[1].text.strip()
                else:
                    vacancia_percentual = "0%"
                vacancia_area = dados[0].find("span").text.strip()
            except (IndexError, AttributeError):
                pass

        if len(dados) >= 2:
            try:
                ocupacao_label = dados[1].find_all("strong")[0].text.strip()
                strongs_ocup = dados[1].find_all("strong")
                if len(strongs_ocup) >= 2:
                    ocupacao_percentual = strongs_ocup[1].text.strip()
                else:
                    ocupacao_percentual = "0%"
                ocupacao_area = dados[1].find("span").text.strip()
            except (IndexError, AttributeError):
                pass

        if vacancia_percentual and vacancia_percentual.lower() != "none%" and vacancia_area:
            vacancia_percentual_valor = limpar_percentual(vacancia_percentual)
            vacancia_area_valor = limpar_area(vacancia_area)
            print(f"{ticker} - {vacancia_label}: {vacancia_percentual_valor}% ({vacancia_area_valor} m²)")

        if ocupacao_percentual and ocupacao_percentual.lower() != "none%" and ocupacao_area:
            ocupacao_percentual_valor = limpar_percentual(ocupacao_percentual)
            ocupacao_area_valor = limpar_area(ocupacao_area)
            print(f"{ticker} - {ocupacao_label}: {ocupacao_percentual_valor}% ({ocupacao_area_valor} m²)")

        driver.close()
    except Exception as e:
        print(f"Erro ao processar {ticker}: {e}")
    finally:
        if driver:
            driver.quit()
