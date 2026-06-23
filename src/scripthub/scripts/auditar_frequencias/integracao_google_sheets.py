import sys
from pathlib import Path

import gspread
import pandas as pd

from scripthub.services import log

from .config import Config

DIRETORIO_BASE = Path(__file__).resolve().parent


def main(config: Config):
    """Função principal que orquestra o Escopo 2 (Integração com Google Sheets)."""
    log.secao("[ESCOPO 2] INTEGRAÇÃO (GOOGLE SHEETS)")

    caminho_exportacao = config.moodle.caminho_exportacao
    caminho_credenciais = config.gsheets.caminho_json_credenciais
    id_planilha = config.gsheets.id_planilha

    if not caminho_exportacao.exists():
        raise RuntimeError(f"Diretório de exportação não encontrado em: {caminho_exportacao}")

    if not caminho_credenciais.exists():
        raise RuntimeError(f"Arquivo de credenciais do Google não encontrado em: {caminho_credenciais}")

    if not id_planilha:
        raise RuntimeError("id_planilha não configurado no arquivo de configurações.")

    arquivos_xlsx = list(caminho_exportacao.glob("*.xlsx"))

    if not arquivos_xlsx:
        raise RuntimeError(
            "Nenhum arquivo XLSX encontrado no diretório de exportação. "
            "Certifique-se de rodar o Escopo 1 antes."
        )

    try:
        log.passo("Autenticando com a API do Google...")
        gc = gspread.service_account(filename=str(caminho_credenciais))

        log.passo("Abrindo a planilha por ID...")
        planilha = gc.open_by_key(id_planilha)

        for arquivo_xlsx in arquivos_xlsx:
            nome_arquivo = arquivo_xlsx.stem
            log.passo(f"Processando arquivo: {arquivo_xlsx.name}")

            try:
                df = pd.read_excel(arquivo_xlsx)
                df = df.fillna("")
                df.columns = df.columns.str.replace(r"^Unnamed: \d+$", "", regex=True)
                dados_para_upload = [df.columns.tolist()] + df.values.tolist()
            except Exception as e:
                log.erro(f"Falha ao ler o arquivo {arquivo_xlsx.name}: {e}")
                continue

            try:
                worksheet = planilha.worksheet(nome_arquivo)
                log.passo(f"Página '{nome_arquivo}' já existe, atualizando...")
            except gspread.exceptions.WorksheetNotFound:
                log.passo(f"Criando nova página: '{nome_arquivo}'")
                worksheet = planilha.add_worksheet(title=nome_arquivo, rows=100, cols=20)

            log.passo(f"Atualizando dados na página '{nome_arquivo}'...")
            worksheet.clear()
            worksheet.update(range_name="A1", values=dados_para_upload)
            log.ok(f"Página '{nome_arquivo}' atualizada com sucesso!")

        log.ok("Escopo 2 finalizado com sucesso!")

    except gspread.exceptions.SpreadsheetNotFound:
        raise RuntimeError(f"A planilha com ID '{id_planilha}' não foi encontrada.")
    except Exception as e:
        import traceback
        log.erro(f"Erro inesperado durante a integração com o Google Sheets: {e}")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    try:
        main(Config.load())
    except Exception as e:
        log.erro(str(e))
        sys.exit(1)
