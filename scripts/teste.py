# %%

import requests

tickers = ["HGLG11", "KNRI11", "XPML11"]  # ou do banco
for ticker in tickers:
    url = f"https://api.plexa.com.br/json/fundo/{ticker}"
    try:
        response = requests.get(url)
        dados = response.json()

        vacancia = dados.get("vacancia_fisica")
        ocupacao = dados.get("ocupacao_fisica")

        print(f"{ticker} - Vacância: {vacancia}% | Ocupação: {ocupacao}%")
    except Exception as e:
        print(f"Erro com {ticker}: {e}")


# %%
