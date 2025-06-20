import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Caminho para o arquivo JSON salvo da API
JSON_PATH = Path(__file__).resolve().parent.parent / "database" / "dados_fundos.json"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "fiis.db"

INDICADORES_RELEVANTES = [
    ("Quantidade de Cotas", "Número de cotas emitidas"),
    ("Patrimônio Líquido", "Valor total do patrimônio do fundo"),
    ("Quantidade de Cotistas", "Número de cotistas cadastrados")
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
            # Quantidade de Cotas
            qtd_cotas = fundo.get("ultimaCotasQtd", "").replace(".", "")
            data_cotas = fundo.get("ultimoPlDataRef", "")
            if qtd_cotas and data_cotas:
                qtd_cotas = float(qtd_cotas)
                data_ref = datetime.strptime("01/" + data_cotas, "%d/%m/%Y").date().isoformat()
                cur.execute("""
                    INSERT INTO fiis_indicadores (fii_id, indicador_id, data_referencia, valor)
                    VALUES (?, ?, ?, ?)
                """, (fii_id, id_indicadores["Quantidade de Cotas"], data_ref, qtd_cotas))
                inseridos += 1

            # Patrimônio Líquido
            patrimonio = fundo.get("ultimoPatrLiquido", "").replace(".", "").replace(",", ".")
            data_patr = fundo.get("ultimoPlDataRef", "")
            if patrimonio and data_patr:
                patrimonio = float(patrimonio)
                data_ref = datetime.strptime("01/" + data_patr, "%d/%m/%Y").date().isoformat()
                cur.execute("""
                    INSERT INTO fiis_indicadores (fii_id, indicador_id, data_referencia, valor)
                    VALUES (?, ?, ?, ?)
                """, (fii_id, id_indicadores["Patrimônio Líquido"], data_ref, patrimonio))
                inseridos += 1

            # Quantidade de Cotistas
            cotistas = fundo.get("UltimaQtdCotistas", "").replace(".", "")
            data_cotistas = fundo.get("UltimaQtdCotistasData", "")
            if cotistas and data_cotistas:
                cotistas = int(cotistas)
                data_ref = datetime.strptime("01/" + data_cotistas, "%d/%m/%Y").date().isoformat()
                cur.execute("""
                    INSERT INTO fiis_indicadores (fii_id, indicador_id, data_referencia, valor)
                    VALUES (?, ?, ?, ?)
                """, (fii_id, id_indicadores["Quantidade de Cotistas"], data_ref, cotistas))
                inseridos += 1

        except Exception as e:
            print(f"Erro ao processar {ticker}: {e}")

    conn.commit()
    conn.close()
    print(f"Indicadores calculados e inseridos: {inseridos}")


if __name__ == '__main__':
    calcular_indicadores()
