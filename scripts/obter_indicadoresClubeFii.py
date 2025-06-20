
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"

def formatar_valor(valor_float):
    return f"{valor_float:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT ticker FROM fiis;")
tickers = [row[0] for row in cursor.fetchall()]
conn.close()

for ticker in tickers:
    driver = None
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument("user-agent=Mozilla/5.0...")
        driver = webdriver.Chrome(options=options)

        print(f"Processando {ticker}...")
        driver.get(f"https://www.clubefii.com.br/fiis/{ticker}")
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # === P/VP e DY Último/12M ===
        pvp = dy_ultimo = dy_12m = None
        tabela = soup.find("table", {"id": "primaryTable"})
        if tabela:
            for linha in tabela.find_all("tr"):
                th = linha.find("th")
                td = linha.find("td")
                if th and td:
                    nome = th.text.strip().lower()
                    valor = td.text.strip()
                    if "p/vp" in nome:
                        pvp = valor.replace(",", ".")
                    if "dividend yield" in nome:
                        partes = re.findall(r"(\d+,\d+)%", valor)
                        if len(partes) >= 2:
                            dy_ultimo = partes[0].replace(",", ".")
                            dy_12m = partes[1].replace(",", ".")

        # === DYs acumulados ===
        dy_1m = dy_3m = dy_6m = dy_12m_acum = None
        div_yield_section = soup.find("li", onclick=re.compile("abre_secao_proventos"))
        if div_yield_section:
            for div in div_yield_section.select("div.resp > div"):
                label = div.find("strong")
                val = div.find("span")
                if label and val:
                    nome = label.text.strip().lower()
                    valor = val.text.strip().replace("%", "").replace(",", ".")
                    if "1 mês" in nome:
                        dy_1m = valor
                    elif "3 meses" in nome:
                        dy_3m = valor
                    elif "6 meses" in nome:
                        dy_6m = valor
                    elif "12 meses" in nome:
                        dy_12m_acum = valor

        # === Conecta banco ===
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id FROM fiis WHERE ticker = ?", (ticker,))
        row = cur.fetchone()
        if not row:
            print(f"[{ticker}] ⚠️ FII não encontrado no banco.")
            conn.close()
            continue
        fii_id = row[0]

        data_ref = datetime.today().strftime("%Y-%m-%d")
        data_ref_span = soup.select_one("div#vacancia > span")
        if data_ref_span:
            match = re.search(r'Data Referência:\s*(\d{2}/\d{2}/\d{4})', data_ref_span.text)
            if match:
                data_ref = datetime.strptime(match.group(1), "%d/%m/%Y").date().isoformat()

        nomes_indicadores = [
            "P/VP", "Dividend Yield Último", "Dividend Yield 1M",
            "Dividend Yield 3M", "Dividend Yield 6M", "Dividend Yield 12M",
            "Vacância Percentual", "Vacância m²", "Ocupação Percentual", "Ocupação m²"
        ]
        cur.execute("SELECT id, nome FROM indicadores WHERE nome IN ({})".format(','.join(['?']*len(nomes_indicadores))), nomes_indicadores)
        indicadores = {nome: id for id, nome in cur.fetchall()}

        def inserir(nome, valor):
            if nome in indicadores:
                if valor:
                    try:
                        valor_float = float(str(valor).replace(".", "").replace(",", "."))
                        valor_formatado = formatar_valor(valor_float)
                        print(f"{ticker} - {nome}: {valor_formatado}")
                        cur.execute("SELECT 1 FROM fiis_indicadores WHERE fii_id = ? AND indicador_id = ? AND data_referencia = ?",
                                    (fii_id, indicadores[nome], data_ref))
                        if not cur.fetchone():
                            cur.execute("INSERT INTO fiis_indicadores (fii_id, indicador_id, data_referencia, valor) VALUES (?, ?, ?, ?)",
                                        (fii_id, indicadores[nome], data_ref, valor_formatado))
                    except Exception as e:
                        print(f"{ticker} - {nome}: Erro ao formatar valor ({valor})")
                else:
                    print(f"{ticker} - {nome}: ❌ Não encontrado")

        inserir("P/VP", pvp)
        inserir("Dividend Yield Último", dy_1m)
        inserir("Dividend Yield 3M", dy_3m)
        inserir("Dividend Yield 6M", dy_6m)
        inserir("Dividend Yield 12M", dy_12m_acum)

        # === Vacância e Ocupação ===
        def limpar_area(texto):
            match = re.search(r'([\d\.]+,\d{2})\s*m²', texto)
            return match.group(1) if match else None

        info_div = soup.find("div", class_="info")
        if info_div:
            dados = info_div.find_all("div", recursive=False)
            vacancia_area = dados[0].find("span").text.strip() if len(dados) >= 1 else None
            ocupacao_area = dados[1].find("span").text.strip() if len(dados) >= 2 else None

            vacancia_area_valor = limpar_area(vacancia_area) if vacancia_area else None
            ocupacao_area_valor = limpar_area(ocupacao_area) if ocupacao_area else None

            if vacancia_area_valor and ocupacao_area_valor:
                vaga = vacancia_area_valor
                ocupa = ocupacao_area_valor

                vaga_num = float(vaga.replace('.', '').replace(',', '.'))
                ocupa_num = float(ocupa.replace('.', '').replace(',', '.'))
                total = vaga_num + ocupa_num
                vacancia_percentual = f"{(vaga_num / total) * 100:.2f}".replace('.', ',')
                ocupacao_percentual = f"{(ocupa_num / total) * 100:.2f}".replace('.', ',')

                inserir("Vacância Percentual", vacancia_percentual)
                inserir("Vacância m²", vaga)
                inserir("Ocupação Percentual", ocupacao_percentual)
                inserir("Ocupação m²", ocupa)

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Erro ao processar {ticker}: {e}")
    finally:
        if driver:
            driver.quit()
