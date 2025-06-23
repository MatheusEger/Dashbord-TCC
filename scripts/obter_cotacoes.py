from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# URL da página de cotações
url = "https://fundamentus.com.br/fii_resultado.php"

# Configura Selenium (modo invisível/headless)
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=options)

# Acessa a página
driver.get(url)
time.sleep(2)  # tempo para o JS carregar a tabela
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# Encontra a tabela
tabela = soup.find("table", class_="w728")
if not tabela:
    print("❌ Tabela de cotações não encontrada.")
    exit()

# Cabeçalho
cabecalho = [th.text.strip() for th in tabela.find_all("th")]
print(" | ".join(cabecalho))

# Linhas da tabela
for linha in tabela.find_all("tr")[1:]:
    colunas = [td.text.strip() for td in linha.find_all("td")]
    print(" | ".join(colunas))
