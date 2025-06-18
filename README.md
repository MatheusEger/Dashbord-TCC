# Dashboard TCC

Este projeto é um dashboard para análise de Fundos de Investimentos Imobiliarios.

## Requisitos

- Python 3.8 ou superior
- Git

## Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITÓRIO]
cd Dashbord-TCC
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione as seguintes variáveis com seus respectivos valores:
```
PLEXA_EMAIL=seu_email@exemplo.com
PLEXA_SENHA=sua_senha
PLEXA_TOKEN=seu_token
```

## Execução

Após a configuração, execute os seguintes comandos em ordem:

1. Criar o banco de dados:
```bash
python criar_banco.py
```

2. Coletar os dados:
```bash
python coletar_dados.py
```

3. Obter indicadores:
```bash
python obter_indicadores.py
```

4. Obter dados do clube FII:
```bash
python obter_clube_fii.py
```

## Observações

- Certifique-se de que todas as dependências foram instaladas corretamente
- Verifique se o arquivo `.env` está configurado com as credenciais corretas
- Execute os scripts na ordem especificada para garantir o funcionamento correto do sistema