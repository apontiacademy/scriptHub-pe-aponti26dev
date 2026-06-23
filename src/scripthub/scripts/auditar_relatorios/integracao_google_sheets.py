import sys
from pathlib import Path

import gspread
import pandas as pd

from scripthub.services import log

from .config import Config

DIRETORIO_BASE = Path(__file__).resolve().parent


def main(config: Config):
    """Função principal que orquestra o Escopo 3 (Integração com Google Sheets)."""
    caminho_csv = config.moodle.csv_saida_analise
    caminho_credenciais = config.gsheets.caminho_json_credenciais
    id_planilha = config.gsheets.id_planilha
    nome_aba = config.gsheets.nome_aba

    if not caminho_csv.exists():
        raise RuntimeError(
            f"Arquivo de auditoria não encontrado em: {caminho_csv}. "
            "Certifique-se de rodar o Escopo 2 antes."
        )

    if not caminho_credenciais.exists():
        raise RuntimeError(f"Arquivo de credenciais do Google não encontrado em: {caminho_credenciais}")

    if not id_planilha:
        raise RuntimeError("id_planilha não configurado no arquivo de configurações.")

    log.passo(f"Lendo dados locais de {caminho_csv.name}...")
    try:
        df = pd.read_csv(caminho_csv, encoding="utf-8-sig")
    except Exception:
        try:
            df = pd.read_csv(caminho_csv, encoding="latin1")
        except Exception as e:
            raise RuntimeError(f"Falha ao ler o arquivo CSV local: {e}")

    if df.shape[1] < 4:
        raise RuntimeError("O CSV de resultado possui menos de 4 colunas. Coluna D indisponível.")

    # Captura o cabeçalho da quarta coluna (Índice 3 = Coluna D) e seus respectivos valores
    cabecalho_coluna_d = df.columns[3]
    valores_coluna_d = df.iloc[:, 3].fillna("").astype(str).tolist()

    # Formata a estrutura de dados como uma lista de linhas exigida pela API do Google Sheets
    dados_para_upload = [[cabecalho_coluna_d]] + [[valor] for valor in valores_coluna_d]

    try:
        log.passo("Autenticando com a API do Google...")
        gc = gspread.service_account(filename=str(caminho_credenciais))

        log.passo("Abrindo a planilha por ID...")
        planilha = gc.open_by_key(id_planilha)
        aba = planilha.worksheet(nome_aba)

        log.passo(f"Limpando dados antigos da Coluna D na aba '{nome_aba}'...")
        aba.batch_clear(["D:D"])

        log.passo(f"Colando novos dados na Coluna D (Total de linhas: {len(dados_para_upload)})...")
        aba.update(range_name="D1", values=dados_para_upload)

        log.ok("Google Sheets atualizado com sucesso!")
        log.ok("Escopo 3 finalizado com sucesso!")

    except gspread.exceptions.WorksheetNotFound:
        raise RuntimeError(f"A aba '{nome_aba}' não foi encontrada na planilha fornecida.")
    except Exception as e:
        raise RuntimeError(f"Erro inesperado durante a integração com o Google Sheets: {e}")
