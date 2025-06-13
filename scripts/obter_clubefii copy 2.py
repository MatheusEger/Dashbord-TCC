# %%

from selenium import webdriver
from bs4 import BeautifulSoup
import time
import re
import sqlite3
import os

# Funções auxiliares

def limpar_percentual(texto):
    match = re.search(r'(\d{1,3},\d{1,2})%', texto)
    return match.group(1) if match else None

def limpar_area(texto):
    match = re.search(r'([\d\.]+,\d{2})\s*m²', texto)
    return match.group(1) if match else None

# Conecta ao banco e obtém os tickers
conn = sqlite3.connect("C:/Users/Matheus/Desktop/projeto_tcc/data/fiis.db")
cursor = conn.cursor()
cursor.execute("SELECT ticker FROM fiis;")
tickers = [row[0] for row in cursor.fetchall()]
conn.close()

# Inicia o navegador
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Roda em segundo plano
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=options)

# Loop pelos tickers
for ticker in tickers:
    try:
        print(f"Processando {ticker}...")
        driver.get(f"https://www.clubefii.com.br/fiis/{ticker}")
        time.sleep(1.5)  # Pequeno delay para garantir carregamento

        soup = BeautifulSoup(driver.page_source, "html.parser")
        info_div = soup.find("div", class_="info")
        dados = info_div.find_all("div", recursive=False) if info_div else []

        vacancia_label = vacancia_percentual = vacancia_area = None
        ocupacao_label = ocupacao_percentual = ocupacao_area = None

        if len(dados) >= 1:
            try:
                vacancia_label = dados[0].find_all("strong")[0].text.strip()
                vacancia_percentual = dados[0].find_all("strong")[1].text.strip()
                vacancia_area = dados[0].find("span").text.strip()
            except (IndexError, AttributeError):
                pass

        if len(dados) >= 2:
            try:
                ocupacao_label = dados[1].find_all("strong")[0].text.strip()
                ocupacao_percentual = dados[1].find_all("strong")[1].text.strip()
                ocupacao_area = dados[1].find("span").text.strip()
            except (IndexError, AttributeError):
                pass

        if vacancia_percentual and vacancia_area:
            vacancia_percentual_valor = limpar_percentual(vacancia_percentual)
            vacancia_area_valor = limpar_area(vacancia_area)
            print(f"{ticker} - {vacancia_label}: {vacancia_percentual_valor}% ({vacancia_area_valor} m²)")

        if ocupacao_percentual and ocupacao_area:
            ocupacao_percentual_valor = limpar_percentual(ocupacao_percentual)
            ocupacao_area_valor = limpar_area(ocupacao_area)
            print(f"{ticker} - {ocupacao_label}: {ocupacao_percentual_valor}% ({ocupacao_area_valor} m²)")

    except Exception as e:
        print(f"Erro ao processar {ticker}: {e}")

# Encerra o navegador
driver.quit()


