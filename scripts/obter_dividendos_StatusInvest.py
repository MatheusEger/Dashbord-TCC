from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
from datetime import datetime, timedelta
import time
import sqlite3
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent  # raiz do projeto
DB_PATH = ROOT_DIR / "data" / "fiis.db"

# Conectando ao banco e lendo tickers
con = sqlite3.connect(DB_PATH)
cur = con.cursor()
cur.execute("SELECT id, ticker FROM fiis")
entries = cur.fetchall()
con.close()

# Separando os tickers (e IDs, se quiser)

def obter_todos_indicadores_statusinvest(ticker, driver):
    url = f"https://statusinvest.com.br/fundos-imobiliarios/{ticker.lower()}"
    driver.get(url)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    # --- 1. Dividendos dos últimos 12 meses ---
    tabelas = driver.find_elements(By.TAG_NAME, 'table')
    tabela_certa = None
    for t in tabelas:
        try:
            thead = t.find_element(By.TAG_NAME, 'thead')
            headers = [th.text.strip().upper() for th in thead.find_elements(By.TAG_NAME, 'th')]
            if headers == ["TIPO", "DATA COM", "PAGAMENTO", "VALOR"]:
                tabela_certa = t
                break
        except Exception:
            continue
    dividendos = []
    if tabela_certa:
        trs = tabela_certa.find_elements(By.TAG_NAME, 'tr')
        for tr in trs[1:]:
            try:
                tds = tr.find_elements(By.TAG_NAME, 'td')
                if len(tds) == 4:
                    tipo = tds[0].text.strip()
                    data_com = tds[1].text.strip()
                    pagamento = tds[2].text.strip()
                    # Extraia o valor IMEDIATAMENTE!
                    divs = tds[3].find_elements(By.TAG_NAME, 'div')
                    if divs:
                        valor = divs[0].text.strip()
                    else:
                        valor = tds[3].text.strip()
                    valor = valor.replace('.', '').replace(',', '.')
                    try:
                        valor_float = float(valor)
                        data_com_dt = pd.to_datetime(data_com, format='%d/%m/%Y', errors='coerce')
                        dividendos.append({
                            "Ticker": ticker.upper(),
                            "Tipo": tipo,
                            "Data Com": data_com_dt,
                            "Pagamento": pagamento,
                            "Valor": valor_float
                        })
                    except Exception:
                        continue
            except Exception as e:
                print(f"[WARNING] Problema ao processar linha do fundo {ticker}: {e}")
                continue

    # --- 2. Indicadores gerais (segmento, tipo de gestão, público-alvo e extras) ---
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    # Pega todos os cards de indicadores (inclui segmento, gestão, público-alvo, rendimento, taxas etc)
    all_cards = driver.find_elements(By.CSS_SELECTOR, ".card.bg-main-gd-h.white-text.rounded")
    segmento = tipo_gestao = publico_alvo = None
    rendimento_24m = taxa_adm = liquidez_md = participacao_ifix = None

    for card in all_cards:
        infos = card.find_elements(By.CLASS_NAME, "info")
        for info in infos:
            try:
                # Subtítulo: pode ser "sub-value" ou "title"
                subtitulo = ""
                try:
                    subtitulo = info.find_element(By.CLASS_NAME, "sub-value").text.strip().lower()
                except:
                    try:
                        subtitulo = info.find_element(By.CLASS_NAME, "title").text.strip().lower()
                    except:
                        pass
                value = info.find_element(By.CLASS_NAME, "value").text.strip()
                # Agora detecta cada campo pelo subtítulo ou label
                if "segmento" in subtitulo:
                    segmento = value
                elif "gestão" in subtitulo:
                    tipo_gestao = value
                elif "público-alvo" in subtitulo:
                    publico_alvo = value
                elif "24m" in subtitulo or "médio" in subtitulo:
                    rendimento_24m = value
                elif "adm" in subtitulo or "administra" in subtitulo:
                    taxa_adm = value
                elif "liq" in subtitulo or "liquidez" in subtitulo:
                    liquidez_md = value
                elif "ifix" in subtitulo:
                    participacao_ifix = value
            except Exception:
                continue

    linhas = []
    if dividendos:
        for div in dividendos:
            linhas.append({
                **div,
                "Segmento": segmento,
                "Tipo da Gestão": tipo_gestao,
                "Público-alvo": publico_alvo,
                "Rendimento Médio 24M": rendimento_24m,
                "Taxa Administração": taxa_adm,
                "Liquidez Média Diária": liquidez_md,
                "Participação IFIX": participacao_ifix
            })
    else:
        linhas.append({
            "Ticker": ticker.upper(),
            "Tipo": None,
            "Data Com": None,
            "Pagamento": None,
            "Valor": None,
            "Segmento": segmento,
            "Tipo da Gestão": tipo_gestao,
            "Público-alvo": publico_alvo,
            "Rendimento Médio 24M": rendimento_24m,
            "Taxa Administração": taxa_adm,
            "Liquidez Média Diária": liquidez_md,
            "Participação IFIX": participacao_ifix
        })
    return linhas


# Exemplo de integração
if __name__ == "__main__":
    options = Options()
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    fiis_tickers = [ticker for fii_id, ticker in entries]

    todas_linhas = []
    for ticker in fiis_tickers:
        print(f"Processando {ticker}...")
        todas_linhas.extend(obter_todos_indicadores_statusinvest(ticker, driver))
        time.sleep(1)

    driver.quit()

    df_final = pd.DataFrame(todas_linhas)
    df_final.to_csv("fiis_dividendos.csv", index=False, encoding="utf-8-sig")
    print("Arquivo CSV gerado: fiis_dividendo.csv")
