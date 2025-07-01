#!/usr/bin/env python3
"""
Orquestração do pipeline:
1) criar banco
2) coletar dados de FIIs
3) obter indicadores da API
4) obter dividendos
5) obter cotações
6) scrap de imóveis
7) marcar ativos
8) atribuir tipo (apenas via adicionaTIpo.py)
"""
import subprocess
import sys
import os
import traceback

def run_script(script_path, error_file):
    """Executa o script e, em caso de erro, registra em error_file."""
    print(f"▶️ Executando: {script_path}")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            error_file.write(f"\n==== ERRO: {script_path} ====\n")
            error_file.write(result.stdout)
            error_file.write(result.stderr)
            error_file.write("\n")
            print(f"❌ Erro em {script_path}. Veja error_log.txt")
        else:
            print(f"✅ Sucesso: {script_path}")
    except Exception as e:
        error_file.write(f"\n==== EXCEÇÃO: {script_path} ====\n")
        error_file.write(traceback.format_exc())
        error_file.write("\n")
        print(f"❌ Exceção em {script_path}. Veja error_log.txt")

if __name__ == '__main__':
    # Caminho raiz (onde este script está)
    root_dir = os.path.dirname(os.path.abspath(__file__))

    # Scripts na ordem desejada
    scripts = [
        './scripts/1_criar_banco.py',
        './scripts/2_coletar_dados.py',
        './scripts/3_obter_indicadoresAPI.py',
        './scripts/4_obter_dividendos.py',
        './scripts/5_obter_cotacoes.py',
        './scripts/6_Imoveis_fundamentus.py',
        './scripts/fiis_ativos.py',
        './scripts/adicionaTIpo.py',       # Somente aqui fazemos a atribuição de tipos
    ]

    # Abre (ou cria) o log de erros
    log_path = os.path.join(root_dir, 'error_log.txt')
    with open(log_path, 'w', encoding='utf-8') as errf:
        errf.write(f"Log de erros iniciado em {sys.argv[0]}\n")
        # Executa cada um
        for rel in scripts:
            full = os.path.join(root_dir, rel)
            if not os.path.isfile(full):
                errf.write(f"\n==== NÃO ENCONTRADO: {full} ====\n")
                print(f"⚠️ Script não encontrado: {full}")
                continue
            run_script(full, errf)

    print("\n🔎 Execução concluída.")
    print("   • Verifique error_log.txt para eventuais falhas.")
