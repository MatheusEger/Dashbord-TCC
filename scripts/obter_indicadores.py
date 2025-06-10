import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Caminho para o arquivo JSON salvo da API
JSON_PATH = Path(__file__).resolve().parent.parent / "database" / "dados_fundos.json"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "fiis.db"

INDICADORES_RELEVANTES = [
    ("Dividend Yield", "Rendimento sobre o preço da cota"),
    ("P/VP", "Preço sobre Valor Patrimonial"),
    ("Nº Cotistas", "Quantidade de cotistas no último mês")
]

def limpar_float(texto):
    return float(texto.replace(".", "").replace(",", "."))

def calcular_indicadores():
    if not JSON_PATH.exists():
        print("Arquivo JSON de dados da API não encontrado.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        dados = json.load(f).get("data", [])

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Cadastrar indicadores se não existirem
    for nome, desc in INDICADORES_RELEVANTES:
        cur.execute("INSERT OR IGNORE INTO indicadores (nome, descricao) VALUES (?, ?)", (nome, desc))

    cur.execute("SELECT id, nome FROM indicadores")
    id_indicadores = {nome: id_ for id_, nome in cur.fetchall()}

    hoje = datetime.now().date().isoformat()
    mes_referencia = hoje[:7] + "-01"
    inseridos = 0

    for fundo in dados:
        ticker = fundo.get("ticker", "").strip()
        if not ticker:
            continue

        # Obter ID do FII pelo ticker
        cur.execute("SELECT id FROM fiis WHERE ticker = ?", (ticker,))
        row = cur.fetchone()
        if not row:
            continue
        fii_id = row[0]

        try:
            # Dividend Yield
            dy = float(str(fundo.get("ultimoRendYield", "0")).replace(",", "."))
            cur.execute("""
                INSERT INTO fiis_indicadores (fii_id, indicador_id, data_referencia, valor)
                VALUES (?, ?, ?, ?)
            """, (fii_id, id_indicadores["Dividend Yield"], mes_referencia, dy))
            inseridos += 1

            # P/VP
            fechamento = limpar_float(str(fundo.get("ultimoFechamento", "0")))
            cota_patr = limpar_float(str(fundo.get("cotaPatr", "0")))
            dy = limpar_float(str(fundo.get("ultimoRendYield", "0")))
            if cota_patr > 0:
                pvp = round(fechamento / cota_patr, 2)
                cur.execute("""
                    INSERT INTO fiis_indicadores (fii_id, indicador_id, data_referencia, valor)
                    VALUES (?, ?, ?, ?)
                """, (fii_id, id_indicadores["P/VP"], mes_referencia, pvp))
                inseridos += 1

            # Nº Cotistas
            cotistas = int(str(fundo.get("UltimaQtdCotistas", "0")).replace(".", ""))
            cur.execute("""
                INSERT INTO fiis_indicadores (fii_id, indicador_id, data_referencia, valor)
                VALUES (?, ?, ?, ?)
            """, (fii_id, id_indicadores["Nº Cotistas"], mes_referencia, cotistas))
            inseridos += 1

        except Exception as e:
            print(f"Erro ao processar {ticker}: {e}")

    conn.commit()
    conn.close()
    print(f"Indicadores calculados e inseridos: {inseridos}")

if __name__ == '__main__':
    calcular_indicadores()
