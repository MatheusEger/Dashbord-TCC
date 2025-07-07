import time
import sqlite3
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# —————————————————————————————————————————
# CONFIGURAÇÕES DE CAMINHO
# —————————————————————————————————————————
# Ajuste este caminho se seu banco estiver em outro diretório
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = ROOT_DIR / "data" / "fiis.db"

# —————————————————————————————————————————
# FUNÇÕES AUXILIARES
# —————————————————————————————————————————
def parse_percent(p: str) -> float | None:
    """
    Converte '5,00%' ou '100,00%' em 5.0 ou 100.0.
    Retorna None se não conseguir converter.
    """
    s = p.strip().replace("%", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

def get_cap_rate(ticker: str) -> float | None:
    """
    Faz scraping na página de detalhes do Fundamentus e retorna
    o Cap Rate (float). Se não encontrar, retorna None.
    """
    url = f"https://fundamentus.com.br/detalhes.php?papel={ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    span_cr = soup.find("span", class_="txt", string="Cap Rate")
    if not span_cr:
        return None

    td_label = span_cr.find_parent("td")
    td_value = td_label.find_next_sibling("td") if td_label else None
    if not td_value:
        return None

    return parse_percent(td_value.get_text(strip=True))

# —————————————————————————————————————————
# SCRIPT PRINCIPAL
# —————————————————————————————————————————
def main():
    # 1) Abre conexão com SQLite
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    # 2) Carrega todos os FIIs (id + ticker)
    cur.execute("SELECT id, ticker FROM fiis;")
    fiis = cur.fetchall()

    # 3) Garante existência do indicador “Cap Rate”
    cur.execute("SELECT id FROM indicadores WHERE nome = ?", ("Cap Rate",))
    row = cur.fetchone()
    if row:
        cap_rate_id = row[0]
    else:
        cur.execute("INSERT INTO indicadores (nome) VALUES (?)", ("Cap Rate",))
        cap_rate_id = cur.lastrowid
        conn.commit()  # salva o novo indicador

    # 4) Para cada FII, busca e salva o Cap Rate
    for fii_id, ticker in fiis:
        try:
            cap = get_cap_rate(ticker)
            if cap is None:
                print(f"⚠️  Cap Rate não encontrado para {ticker}.")
                continue

            data_ref = time.strftime("%Y-%m-%d")
            cur.execute("""
                INSERT OR REPLACE INTO fiis_indicadores
                    (fii_id, indicador_id, valor, data_referencia)
                VALUES (?, ?, ?, ?)
            """, (fii_id, cap_rate_id, cap, data_ref))
            conn.commit()
            print(f"✅ {ticker}: Cap Rate {cap:.2f}% salvo (ref. {data_ref}).")

        except Exception as e:
            print(f"❌ Erro ao processar {ticker}: {e}")

    # 5) Fecha conexão
    conn.close()
    print("🔚 Processamento concluído.")

if __name__ == "__main__":
    main()
