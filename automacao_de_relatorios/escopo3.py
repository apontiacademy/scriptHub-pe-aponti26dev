import os
import sys
from pathlib import Path

import gspread
import pandas as pd
from dotenv import load_dotenv

# =========================================================================
# ANCORAGEM DINÂMICA DE ESCOPO
# =========================================================================
# Caminho absoluto da pasta 'automacao_de_relatorios'
PASTA_ESCOPO = Path(__file__).resolve().parent

# Força o carregamento do .env que está EXCLUSIVAMENTE dentro desta pasta
env_path = PASTA_ESCOPO / ".env"
load_dotenv(dotenv_path=env_path, override=True)


def tratar_caminho_relativo(valor_env: str | None, padrao: str) -> Path:
    """Se o caminho for relativo (começar com ./), ancora ele dentro da PASTA_ESCOPO."""
    caminho_str = valor_env if valor_env else padrao
    if caminho_str.startswith("./") or caminho_str.startswith("../"):
        caminho_limpo = caminho_str.lstrip("./")
        return (PASTA_ESCOPO / caminho_limpo).resolve()
    return Path(caminho_str).resolve()


def main():
    print("\n--- [Escopo 3: Sincronizando Coluna D com Google Sheets] ---")

    # 1. Carrega caminhos e configurações tratando os caminhos relativos para a pasta do escopo
    caminho_csv = tratar_caminho_relativo(os.getenv("MOODLE_ANALYSIS_OUTPUT_CSV"), "./dados/resultado.csv")
    credentials_path = tratar_caminho_relativo(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), "./credentials.json")
    
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    aba_name = os.getenv("GOOGLE_SHEETS_ABA_NAME", "Página1")

    if not caminho_csv.exists():
        print(f"ERRO: Arquivo de auditoria não encontrado em: {caminho_csv}")
        print("Certifique-se de rodar o Escopo 2 antes de iniciar o Escopo 3.")
        sys.exit(1)

    if not credentials_path.exists():
        print(f"ERRO: Arquivo de credenciais do Google não encontrado em: {credentials_path}")
        sys.exit(1)

    if not sheet_id:
        print("ERRO: GOOGLE_SHEETS_ID não configurado no arquivo .env.")
        sys.exit(1)

    # 2. Ler a coluna D do arquivo CSV local
    print(f"[Escopo 3] Lendo dados locais de {caminho_csv.name}...")
    try:
        df = pd.read_csv(caminho_csv, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(caminho_csv, encoding="latin1")

    if df.shape[1] < 4:
        print("ERRO: O CSV de resultado possui menos de 4 colunas. Coluna D indisponível.")
        sys.exit(1)

    # Captura o nome da quarta coluna (Índice 3 = Coluna D) e os valores
    nome_coluna_d = df.columns[3]
    valores_coluna_d = df.iloc[:, 3].fillna("").astype(str).tolist()

    # Monta a estrutura de lista de listas exigida pela API do Google para colunas: [[linha1], [linha2], ...]
    dados_para_enviar = [[nome_coluna_d]] + [[valor] for valor in valores_coluna_d]

    # 3. Autenticar e conectar ao Google Sheets
    try:
        print("[Escopo 3] Autenticando com a API do Google...")
        gc = gspread.service_account(filename=str(credentials_path))
        
        print("[Escopo 3] Abrindo a planilha por ID...")
        planilha = gc.open_by_key(sheet_id)
        worksheet = planilha.worksheet(aba_name)

        # 4. Sobrescrever a Coluna D com segurança
        print(f"[Escopo 3] Limpando dados antigos da Coluna D na aba '{aba_name}'...")
        worksheet.batch_clear(['D:D'])

        print(f"[Escopo 3] Colando os novos dados na Coluna D (Total de linhas: {len(dados_para_enviar)})...")
        worksheet.update(range_name='D1', values=dados_para_enviar)

        print("✨ [Escopo 3] Google Sheets atualizado com sucesso!")

    except gspread.exceptions.WorksheetNotFound:
        print(f"ERRO: A aba '{aba_name}' não foi encontrada na planilha fornecida.")
        sys.exit(1)
    except Exception as e:
        print(f"ERRO inesperado durante a integração com o Google Sheets: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()