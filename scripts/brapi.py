import requests
token = '6y6BitSyPRbvKcixSTg9W3'
ticker = 'hglg11'
url = f'https://brapi.dev/api/quote/{ticker}?token={token}'
response = requests.get(url)
data = response.json()
print(data)