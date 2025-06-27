import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL-base com placeholder para o ticker
URL_TEMPLATE = (
    "https://fundamentus.com.br/"
    "fii_imoveis_detalhes.php?papel={ticker}"
    "&interface=mobile&interface=classic"
)

def fetch_imoveis_table(ticker: str) -> pd.DataFrame | None:
    """Busca a página de imóveis do FII e retorna um DataFrame com a tabela."""
    url = URL_TEMPLATE.format(ticker=ticker.upper())
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(url, headers=headers)
    # O Fundamentus costuma usar ISO-8859-1
    resp.encoding = resp.apparent_encoding or "latin1"
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Encontra a primeira tabela na página
    table = soup.find("table")
    if table is None:
        print(f"[{ticker}] Nenhuma tabela encontrada em {url}")
        return None

    # Extrai cabeçalhos
    headers = [th.get_text(strip=True) for th in table.find_all("th")]

    # Extrai linhas
    rows = []
    for tr in table.find_all("tr")[1:]:
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if cols:
            rows.append(cols)

    # Monta DataFrame
    df = pd.DataFrame(rows, columns=headers)
    return df

if __name__ == "__main__":
    import sys

    # Recebe ticker como argumento, ou usa HGLG11 por padrão
    ticker = sys.argv[1] if len(sys.argv) > 1 else "HGLG11"
    df = fetch_imoveis_table(ticker)
    if df is not None:
        # Exibe no terminal e salva CSV para inspeção
        print(df.to_string(index=False))
        df.to_csv(f"{ticker}_imoveis.csv", index=False, sep=";")
