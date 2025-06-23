from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Configurações do Selenium (modo headless)
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument("user-agent=Mozilla/5.0")

driver = webdriver.Chrome(options=options)

# Acessa o site
url = "https://fundamentus.com.br/fii_resultado.php"
driver.get(url)
time.sleep(3)

# Pega o HTML
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Encontra todas as tabelas com a classe w728 (usada pelo Fundamentus)
tabelas = soup.find_all("table", class_="w728")

# Itera e imprime cada tabela formatada
for i, tabela in enumerate(tabelas, 1):
    print(f"\n📊 Tabela {i}:")
    for linha in tabela.find_all("tr"):
        colunas = linha.find_all(["td", "th"])
        texto_linha = [col.get_text(strip=True) for col in colunas]
        print(" | ".join(texto_linha))

driver.quit()
