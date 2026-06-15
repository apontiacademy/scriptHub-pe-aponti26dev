import sys
from datetime import datetime
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from .config import Config

BASE_DIR = Path(__file__).resolve().parent


def realizar_backup_xlsx_local(
    caminho_credenciais: Path, id_planilha: str, diretorio_backup: Path
) -> str | None:
    """Busca a planilha do Google Sheets, exporta como um arquivo .xlsx e salva localmente com um timestamp."""
    escopos = ["https://www.googleapis.com/auth/drive"]

    try:
        print("  • Autenticando com a conta de serviço...")
        credenciais = Credentials.from_service_account_file(
            str(caminho_credenciais), scopes=escopos
        )
        servico = build("drive", "v3", credentials=credenciais)

        print("  • Buscando informações da planilha original...")
        metadados_arquivo = (
            servico.files()
            .get(fileId=id_planilha, fields="name", supportsAllDrives=True)
            .execute()
        )
        nome_original = metadados_arquivo.get("name", "Planilha_Sem_Nome")

        # Formata o timestamp atual para o nome do arquivo
        horario_atual = datetime.now()
        data_formatada = horario_atual.strftime("%Y-%m-%d %H-%M")

        nome_arquivo = f"[BACKUP {data_formatada}] {nome_original}.xlsx"
        caminho_final = diretorio_backup / nome_arquivo

        print("  • Exportando planilha do Google Sheets para XLSX (Excel)...")
        # O método 'export_media' realiza a conversão em tempo real nos servidores do Google
        requisicao = servico.files().export_media(
            fileId=id_planilha,
            mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        conteudo_binario = requisicao.execute()

        print("  • Gravando arquivo digital no disco...")
        with open(caminho_final, "wb") as f:
            f.write(conteudo_binario)

        print(f"  ✔ Cópia local gerada: {nome_arquivo}")
        return nome_arquivo

    except Exception as e:
        print(f"  ❌ ERRO: Falha no processo de backup local: {e}", file=sys.stderr)
        return None


def main(config: Config):
    """Função principal que orquestra o Escopo 4 (Backup Local Automatizado)."""
    print("=" * 80)
    print("▶ [ESCOPO 4] BACKUP AUTOMÁTICO (.XLSX)")
    print("=" * 80)

    caminho_credenciais = config.gsheets.caminho_json_credenciais
    id_planilha = config.gsheets.id_planilha
    diretorio_backup = config.gsheets.caminho_backup_local

    # Validação de pré-requisitos do sistema de arquivos
    if not caminho_credenciais.exists():
        print(
            f"  ❌ ERRO: O arquivo de credenciais não foi encontrado em: {caminho_credenciais}",
            file=sys.stderr,
        )
        print("=" * 80)
        sys.exit(1)

    if not id_planilha:
        print(
            "  ❌ ERRO: id_planilha não configurado no arquivo de configurações.",
            file=sys.stderr,
        )
        print("=" * 80)
        sys.exit(1)

    # Garante de forma automática que a estrutura do diretório de backup exista
    diretorio_backup.mkdir(parents=True, exist_ok=True)

    # Executa a tarefa principal de backup passando as configurações injetadas
    arquivo_gerado = realizar_backup_xlsx_local(
        caminho_credenciais, id_planilha, diretorio_backup
    )

    if arquivo_gerado:
        print("\n✔ Escopo 4 finalizado com sucesso!")
    else:
        print("\n⚠️ Escopo 4 terminou com falhas (veja os logs acima).", file=sys.stderr)

    print("=" * 80)


if __name__ == "__main__":
    # Carrega as configurações unificadas e injeta na main
    configuracao_carregada = Config.load()
    main(configuracao_carregada)
