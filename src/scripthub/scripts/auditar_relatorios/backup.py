from datetime import datetime
from pathlib import Path

from scripthub.services import log
from scripthub.services.google.drive import GoogleDriveClient

from .config import Config

_ESCOPOS_DRIVE = ["https://www.googleapis.com/auth/drive"]


def realizar_backup_xlsx_local(caminho_credenciais: Path, id_planilha: str, diretorio_backup: Path) -> str | None:
    """Exporta a planilha do Google Sheets como XLSX e salva localmente."""
    try:
        log.passo("Autenticando com a conta de serviço...")
        drive = GoogleDriveClient(caminho_credenciais, _ESCOPOS_DRIVE)

        log.passo("Buscando informações da planilha original...")
        metadados = drive.metadados(id_planilha)
        nome_original = metadados.get("name", "Planilha_Sem_Nome")

        data_formatada = datetime.now().strftime("%Y-%m-%d %H-%M")
        nome_arquivo = f"[BACKUP {data_formatada}] {nome_original}.xlsx"
        caminho_final = diretorio_backup / nome_arquivo

        log.passo("Exportando planilha do Google Sheets para XLSX...")
        conteudo_binario = drive.exportar_xlsx(id_planilha)

        log.passo("Gravando arquivo no disco...")
        with open(caminho_final, "wb") as f:
            f.write(conteudo_binario)

        log.ok(f"Cópia local gerada: {nome_arquivo}")
        return nome_arquivo

    except Exception as e:
        log.erro(f"Falha no processo de backup local: {e}")
        return None


def main(config: Config) -> None:
    """Gera backup local da planilha de resultados."""
    caminho_credenciais = config.gsheets.caminho_json_credenciais
    id_planilha = config.gsheets.id_planilha
    diretorio_backup = config.gsheets.caminho_backup_local

    if not caminho_credenciais.exists():
        raise RuntimeError(f"O arquivo de credenciais não foi encontrado em: {caminho_credenciais}")

    if not id_planilha:
        raise RuntimeError("id_planilha não configurado no arquivo de configurações.")

    diretorio_backup.mkdir(parents=True, exist_ok=True)

    arquivo_gerado = realizar_backup_xlsx_local(caminho_credenciais, id_planilha, diretorio_backup)

    if arquivo_gerado:
        log.ok("Escopo 4 finalizado com sucesso!")
    else:
        log.aviso("Escopo 4 terminou com falhas (veja os logs acima).")
