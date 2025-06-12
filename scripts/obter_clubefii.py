# %%

from selenium import webdriver
from bs4 import BeautifulSoup
import time

# Inicia o navegador e abre a página
driver = webdriver.Chrome()
driver.get("https://www.clubefii.com.br/fiis/HGLG11")
time.sleep(5)  # aguarda o carregamento da página
html = driver.page_source
driver.quit()

# Processa o HTML com BeautifulSoup
soup = BeautifulSoup(html, "html.parser")

# Encontra o bloco com os dados de vacância e ocupação
info_div = soup.find("div", class_="info")
dados = info_div.find_all("div", recursive=False)

# Extrai vacância
vacancia_label = dados[0].find_all("strong")[0].text.strip()
vacancia_percentual = dados[0].find_all("strong")[1].text.strip()
vacancia_area = dados[0].find("span").text.strip()

# Extrai ocupação
ocupacao_label = dados[1].find_all("strong")[0].text.strip()
ocupacao_percentual = dados[1].find_all("strong")[1].text.strip()
ocupacao_area = dados[1].find("span").text.strip()

# Exibe os resultados
print(f"{vacancia_label}: {vacancia_percentual} ({vacancia_area})")
print(f"{ocupacao_label}: {ocupacao_percentual} ({ocupacao_area})")

