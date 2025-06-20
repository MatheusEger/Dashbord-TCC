import requests
import sqlite3
import time
from datetime import datetime
from dotenv import load_dotenv
import os
from pathlib import Path
import unicodedata
import json

# === CARREGAR VARIÁVEIS DO .env ===
load_dotenv()
EMAIL = os.getenv("PLEXA_EMAIL")
SENHA = os.getenv("PLEXA_SENHA")
TOKEN = os.getenv("PLEXA_TOKEN")

# === ENDPOINTS ===
LOGIN_ENDPOINT = 'https://api.plexa.com.br/site/login'
ENDPOINT = 'https://api.plexa.com.br/json/fundo'

# === CAMINHO ABSOLUTO DO BANCO ===
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "fiis.db"
ENV_PATH = ROOT_DIR / ".env"

def salvar_token_no_env(token):
    with open(ENV_PATH, 'r') as file:
        linhas = file.readlines()
    with open(ENV_PATH, 'w') as file:
        for linha in linhas:
            if linha.startswith("PLEXA_TOKEN="):
                file.write(f"PLEXA_TOKEN={token}\n")
            else:
                file.write(linha)

def autenticar():
    global TOKEN
    print(f"Tentando autenticar com email: {EMAIL}")
    response = requests.post(LOGIN_ENDPOINT, json={
        'usuEmail': EMAIL,
        'usuSenha': SENHA,
    }, headers={'Content-Type': 'application/json'})

    if response.status_code == 200 and 'accessToken' in response.json():
        TOKEN = response.json()['accessToken']
        salvar_token_no_env(TOKEN)
        print("Autenticação bem sucedida!")
        return TOKEN
    else:
        print("Erro ao autenticar:", response.text)
        return None

def obter_dados(token):
    print("Obtendo dados com token da Plexa")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    response = requests.get(ENDPOINT, headers=headers)
    if response.status_code == 200:
        dados = response.json().get("data", [])
        print(f"{len(dados)} FIIs obtidos da API.")
        if len(dados) > 0:
            print("Exemplo do primeiro FII:", dados[0])
        return dados
    else:
        print("Erro ao obter dados:", response.text)
        return []
    
def normalizar_texto(texto):
    if not texto or texto.strip().upper() in ["N/D", "N.D", "NAO DEFINIDO", "NÃO DEFINIDO"]:
        return "Outros"

    texto_normalizado = unicodedata.normalize('NFKD', texto.strip().title()).encode('ASCII', 'ignore').decode('utf-8')
    return texto_normalizado

def salvar_dados_no_banco(dados):
    print(f"Tentando salvar {len(dados)} FIIs no banco...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    count_fiis = 0
    count_setores = 0

    for fundo in dados:
        ticker = fundo.get('ticker', '').strip()
        nome = fundo.get('nome', '').strip()
        setor_bruto = fundo.get('segmento', 'Outros')
        setor_nome = normalizar_texto(setor_bruto)
        data_atual = datetime.now().isoformat()
        gestao = fundo.get("gestao", "").strip()
        admin = fundo.get("admin", "").strip()

        if not ticker:
            print(f"Pulando FII sem ticker: {fundo}")
            continue

        print(f"Processando FII: {ticker} - {nome} - Setor: {setor_nome} - Gestão: {gestao} - Admin: {admin}")

        # Insere setor, se novo
        cur.execute("INSERT OR IGNORE INTO setor (nome) VALUES (?)", (setor_nome,))
        if cur.rowcount:
            count_setores += 1
            print(f"Novo setor adicionado: {setor_nome}")

        cur.execute("SELECT id FROM setor WHERE nome = ?", (setor_nome,))
        setor_id = cur.fetchone()[0]

        # Insere FII
        cur.execute("""
        INSERT OR IGNORE INTO fiis (ticker, nome, gestao, admin, setor_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (ticker, nome, gestao, admin, setor_id, data_atual))
        if cur.rowcount:
            count_fiis += 1
            print(f"Novo FII adicionado: {ticker}")

    conn.commit()
    conn.close()
    print(f"Dados salvos com sucesso no banco: {count_fiis} novos FIIs | {count_setores} novos setores.")

if __name__ == '__main__':
    if not TOKEN:
        print("Token não encontrado, tentando autenticar...")
        TOKEN = autenticar()
    if TOKEN:
        dados = obter_dados(TOKEN)
        if dados:
            salvar_dados_no_banco(dados)
    else:
        print("Não foi possível obter o token de autenticação.")

    json_path = Path(__file__).resolve().parent.parent / "database" / "dados_fundos.json"
    json_path.parent.mkdir(exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"data": dados}, f, ensure_ascii=False, indent=2)
    print(f"Arquivo JSON salvo em: {json_path}")

def salvar_cotacoes_e_indicadores(dados):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Criar indicadores padrão, se não existirem
    indicadores = {
        "Dividend Yield": "Rendimento sobre o preço da cota",
        "P/VP": "Preço sobre Valor Patrimonial",
        "Nº Cotistas": "Número de cotistas registrados"
    }
    for nome, descricao in indicadores.items():
        cur.execute("INSERT OR IGNORE INTO indicadores (nome, descricao) VALUES (?, ?)", (nome, descricao))

    # Obter IDs dos indicadores
    cur.execute("SELECT id, nome FROM indicadores")
    id_indicadores = {nome: id_ for id_, nome in cur.fetchall()}

    hoje = datetime.now().date().isoformat()
    agora = datetime.now().isoformat()

    for fundo in dados:
        ticker = fundo.get('ticker', '').strip()
        if not ticker:
            continue

        # Buscar ID do FII
        cur.execute("SELECT id FROM fiis WHERE ticker = ?", (ticker,))
        resultado = cur.fetchone()
        if not resultado:
            continue
        fii_id = resultado[0]

        # 2. Cotação
        try:
            preco_fechamento = float(str(fundo.get('ultimoFechamento', '0')).replace(',', '.'))
            rendimento = float(str(fundo.get('ultimoRendValor', '0')).replace(',', '.'))
        except ValueError:
            continue

        cur.execute("""
            INSERT INTO cotacoes (fii_id, data, preco_fechamento, rendimento, volume, created_at)
            VALUES (?, ?, ?, ?, NULL, ?)
        """, (fii_id, hoje, preco_fechamento, rendimento, agora))

        # 3. Indicadores por FII
        def inserir_indicador(nome_indicador, valor_raw):
            valor = float(str(valor_raw).replace(',', '.')) if valor_raw else None
            if valor is not None:
                cur.execute("""
                    INSERT INTO fiis_indicadores (fii_id, indicador_id, data_referencia, valor)
                    VALUES (?, ?, ?, ?)
                """, (fii_id, id_indicadores[nome_indicador], hoje[:7] + "-01", valor))

        inserir_indicador("Dividend Yield", fundo.get('ultimoRendYield'))
        inserir_indicador("P/VP", fundo.get('cotaPatr'))
        inserir_indicador("Nº Cotistas", fundo.get('UltimaQtdCotistas'))

    conn.commit()
    conn.close()
    print("Cotações e indicadores salvos com sucesso.")

    