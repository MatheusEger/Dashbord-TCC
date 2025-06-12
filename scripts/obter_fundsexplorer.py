# %%
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time

# Configurações do navegador
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# Acessa a página
driver.get("https://www.fundsexplorer.com.br/ranking")

wait = WebDriverWait(driver, 20)

try:
    # Clica no botão de colunas
    botao_colunas = wait.until(EC.element_to_be_clickable((By.ID, "colunas-ranking__select-button")))
    botao_colunas.click()
    time.sleep(10)
    # Aguarda o menu de colunas aparecer
    wait.until(EC.visibility_of_element_located((By.ID, "colunas-ranking__select-options")))

    # Lista de colunas que você quer selecionar (automaticamente)
    colunas_para_ativar = [
        "DY (3M) Acumulado",
        "DY (6M) Acumulado",
        "DY (12M) Acumulado",
        "Último Dividendo",
        "DY Ano",
        "DY Patrimonial",
        "Rentab. Patr. Acumulada"
    ]

    # Marca as colunas desejadas (se não estiverem marcadas ainda)
    for coluna_id in colunas_para_ativar:
        try:
            checkbox = driver.find_element(By.ID, coluna_id)
            if not checkbox.is_selected():
                checkbox.click()
                time.sleep(0.3)
        except Exception as e:
            print(f"Erro ao selecionar '{coluna_id}': {e}")

    # Aguarda carregamento da tabela com as colunas novas
    time.sleep(10)

    # Extrai HTML atualizado
    html = driver.page_source

finally:
    driver.quit()

# Faz o parsing com BeautifulSoup e Pandas
soup = BeautifulSoup(html, "html.parser")
tabelas = pd.read_html(StringIO(str(soup)))

print(f"{len(tabelas)} tabelas encontradas")
for i, tabela in enumerate(tabelas):
    print(f"\n--- Tabela {i} ---")
    print(tabela.head())
