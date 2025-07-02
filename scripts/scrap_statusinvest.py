import requests
import time
import random
from bs4 import BeautifulSoup
import sys
import sqlite3
from pathlib import Path
import re

# --- Configurações ---
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent  # raiz do projeto
DB_PATH = ROOT_DIR / "data" / "fiis.db"
BASE_URL = "https://statusinvest.com.br/fundos-imobiliarios"

# Converte BR number to float
def parse_br(x: str) -> float:
    s = re.sub(r"\.(?=\d{3},)", "", x)
    s = s.replace(" ", "")
    s = s.replace(",", ".")
    s = re.sub(r"[^0-9.]", "", s)
    return float(s) if s else 0.0

# Scraping daemon
def scrape_statusinvest_info(ticker: str) -> dict:
    url = f"{BASE_URL}/{ticker.lower()}"
    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    info = {}
    # Split/Inplit
    card = next((d for d in soup.select('div.card.p-2.p-xs-3')
                 if d.select_one('h3') and 'DESDOBRAMENTO' in d.select_one('h3').get_text(strip=True).upper()), None)
    if card:
        tag_type = card.select_one('div.rounded span')
        info['type'] = tag_type.get_text(strip=True) if tag_type else 'Nenhum'
        # datas e fator
        for sm in card.select('small'):
            lbl = sm.get_text(strip=True).lower()
            stg = sm.find_next_sibling('strong')
            if not stg:
                continue
            val = stg.get_text(strip=True)
            if 'data do anúncio' in lbl:
                info['announcement_date'] = val
            elif 'data com' in lbl:
                info['com_date'] = val
            elif 'fator' in lbl:
                info['factor'] = val
        if 'announcement_date' not in info:
            info['announcement_date'] = None
        if 'com_date' not in info:
            info['com_date'] = None
        if 'factor' not in info or not info.get('factor'):
            info['factor'] = '1,0000 para 1,0000'
    else:
        info.update({'type':'Nenhum','announcement_date':None,'com_date':None,'factor':'1,0000 para 1,0000'})
    # Tipo de gestão
    info['tipo_gestao'] = None
    d2 = soup.select_one('div.card.bg-main-gd-h.white-text.rounded.pt-1.pb-1')
    if d2:
        for sp in d2.select('span.sub-value'):
            text = sp.get_text(strip=True).lower()
            if 'tipo da gestão' in text:
                sg = sp.find_next('strong', class_='value')
                info['tipo_gestao'] = sg.get_text(strip=True) if sg else None
                break
    # Taxas Administração
    info['taxas_administracao'] = '0'
    stx = soup.find('span', class_='sub-value', string=re.compile(r'Taxas', re.I))
    if stx:
        sg = stx.find_next('strong', class_='value')
        raw = sg.get_text(strip=True) if sg else ''
        if raw and not raw.strip().startswith('-'):
            info['taxas_administracao'] = raw
    return info

# Main ETL
def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Criar tabela capital_fiis referenciando fiis.id
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS capital_fiis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fii_id INTEGER UNIQUE,
            type TEXT,
            announcement_date TEXT,
            com_date TEXT,
            fator_antigo REAL,
            fator_novo REAL,
            tipo_gestao TEXT,
            taxas_administracao TEXT,
            FOREIGN KEY(fii_id) REFERENCES fiis(id)
        )
        '''
    )
    # Adicionar coluna taxas_administracao se faltar
    cols = [r[1] for r in cur.execute("PRAGMA table_info(capital_fiis)")]
    if 'taxas_administracao' not in cols:
        cur.execute("ALTER TABLE capital_fiis ADD COLUMN taxas_administracao TEXT")
    # Buscar lista de fiis com id e ticker
    cur.execute("SELECT id, ticker FROM fiis")
    entries = cur.fetchall()
    for fii_id, ticker in entries:
        try:
            data = scrape_statusinvest_info(ticker)
            # fator parse
            if data['type']=='Nenhum':
                antigo, novo = 1.0, 1.0
            else:
                fs = data.get('factor','')
                m = re.match(r"([\d\.,]+)\s*para\s*([\d\.,]+)", fs)
                if m:
                    antigo = parse_br(m.group(1))
                    novo = parse_br(m.group(2))
                else:
                    antigo, novo = 1.0, 1.0
            # inserir ou atualizar
            cur.execute(
                '''
                INSERT INTO capital_fiis
                (fii_id,type,announcement_date,com_date,fator_antigo,fator_novo,tipo_gestao,taxas_administracao)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(fii_id) DO UPDATE SET
                  type=excluded.type,
                  announcement_date=excluded.announcement_date,
                  com_date=excluded.com_date,
                  fator_antigo=excluded.fator_antigo,
                  fator_novo=excluded.fator_novo,
                  tipo_gestao=excluded.tipo_gestao,
                  taxas_administracao=excluded.taxas_administracao
                '''
                ,(fii_id,data['type'],data['announcement_date'],data['com_date'],antigo,novo,data['tipo_gestao'],data['taxas_administracao'])
            )
            print(f"[{ticker}] (ID {fii_id}) gravado. fator_antigo={antigo}, fator_novo={novo}")
            time.sleep(random.uniform(1,3))
        except Exception as e:
            print(f"Erro em {ticker}: {e}")
            time.sleep(random.uniform(1,3))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()
