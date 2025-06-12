# %%
import requests
import pandas as pd
# %%
URL = "https://www.oceans14.com.br/fundos-imobiliarios/hglg11"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
response = requests.get(URL, headers=headers)
#time.sleep(60)
response.raise_for_status() 

tabelas = pd.read_html(response.text)

tabelas
# %%
len(tabelas)

# %%

tabelas[5]

# %%

type(tabelas[5])

# %%

df_indicadores = tabelas[5]