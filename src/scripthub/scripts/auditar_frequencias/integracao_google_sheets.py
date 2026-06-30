import gspread
import pandas as pd

from scripthub.services import log
from scripthub.services.google.sheets import GoogleSheetsClient

from .config import Config


def main(config: Config) -> None:
    """Integra os arquivos XLSX de frequência com o Google Sheets."""
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

    log.passo("Autenticando com a API do Google...")
    client = GoogleSheetsClient(caminho_credenciais)

    log.passo("Abrindo a planilha por ID...")
    planilha = client.planilha(id_planilha)

    falhas = []
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
            falhas.append(arquivo_xlsx.name)
            continue

        aba = client.obter_ou_criar_aba(planilha, nome_arquivo)
        log.passo(f"Atualizando dados na página '{nome_arquivo}'...")
        aba.clear()
        aba.update(range_name="A1", values=dados_para_upload)
        log.ok(f"Página '{nome_arquivo}' atualizada com sucesso!")

    if falhas:
        raise RuntimeError(f"{len(falhas)} arquivo(s) falharam: {', '.join(falhas)}")

    log.ok("Escopo 2 finalizado com sucesso!")
