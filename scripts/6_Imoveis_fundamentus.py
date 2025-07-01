import time
import sqlite3
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# 1) Configurações de caminho
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"

# 2) Funções de parsing
def parse_area(area_str: str) -> float | None:
    """Converte '132.353' em 132353.0"""
    s = area_str.strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

def parse_int(s: str) -> int | None:
    try:
        return int(s.strip().replace(".", "").replace(",", ""))
    except ValueError:
        return None

def parse_percent(p: str) -> float | None:
    """
    Converte '94,05%' ou '100,00%' em 94.05 ou 100.0
    """
    s = p.strip().replace("%", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

# 3) Script principal
def main():
    # Conecta ao banco
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    # Busca todos os FIIs (id + ticker)
    cur.execute("SELECT id, ticker FROM fiis;")
    fiis = cur.fetchall()

    for fii_id, ticker in fiis:
        driver = None
        try:
            # Configura WebDriver headless
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            driver = webdriver.Chrome(options=options)

            url = (
                f"https://fundamentus.com.br/"
                f"fii_imoveis_detalhes.php?papel={ticker}"
                f"&interface=mobile&interface=classic"
            )
            print(f"Processando imóveis de {ticker}...")
            driver.get(url)
            time.sleep(3)  # espera o conteúdo carregar

            soup = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.find("table")
            if not table:
                print(f"[{ticker}] Tabela não encontrada em {url}")
                continue

            # Cabeçalhos e índice de colunas
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            idx = {h: i for i, h in enumerate(headers)}

            # Para cada linha da tabela
            for tr in table.find_all("tr")[1:]:
                cols = [td.get_text(strip=True) for td in tr.find_all("td")]
                if not cols:
                    continue

                nome_imovel = cols[idx["Imóvel"]]
                endereco    = cols[idx["Endereço"]]
                area_m2     = parse_area(cols[idx["Área"]])
                num_unidades= parse_int(cols[idx["Num Unidades"]])
                tx_ocup     = parse_percent(cols[idx["% tx ocupação"]])
                tx_inad     = parse_percent(cols[idx["% inadimplência"]])
                pct_rec     = parse_percent(cols[idx["% das receitas do fii"]])

                # Insere no banco
                cur.execute("""
                    INSERT INTO fiis_imoveis (
                        fii_id, nome_imovel, endereco,
                        area_m2, num_unidades,
                        tx_ocupacao, tx_inadimplencia, pct_receitas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fii_id, nome_imovel, endereco,
                    area_m2, num_unidades,
                    tx_ocup, tx_inad, pct_rec
                ))

            # confirma para cada ticker
            conn.commit()

        except Exception as e:
            print(f"Erro ao processar {ticker}: {e}")
        finally:
            if driver:
                driver.quit()

    conn.close()
    print("✅ Scraping de imóveis concluído.")

if __name__ == "__main__":
    main()
