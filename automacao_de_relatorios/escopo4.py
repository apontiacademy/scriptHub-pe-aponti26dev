import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# =========================================================================
# ANCORAGEM DINÂMICA DE ESCOPO
# =========================================================================
# Caminho absoluto da pasta 'automacao_de_relatorios'
PASTA_ESCOPO = Path(__file__).resolve().parent

# Força o carregamento do .env que está EXCLUSIVAMENTE dentro desta pasta
env_path = PASTA_ESCOPO / ".env"
load_dotenv(dotenv_path=env_path, override=True)


def realizar_backup_local_xlsx(credentials_path: Path, spreadsheet_id: str, backup_dir: Path) -> str | None:
    """
    Escopo 4: Busca a planilha do Google Sheets, exporta como formato .xlsx (Excel)
    e salva localmente na pasta de backups com data e hora no nome.
    """
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    try:
        print("  [Drive API] Autenticando com a conta de serviço...")
        creds = Credentials.from_service_account_file(str(credentials_path), scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        
        print("  [Drive API] Buscando informações da planilha original...")
        file_metadata = service.files().get(
            fileId=spreadsheet_id, 
            fields='name',
            supportsAllDrives=True
        ).execute()
        nome_original = file_metadata.get('name', 'Planilha_Sem_Nome')
        
        # Formatar a data/hora atual conforme padrão
        agora = datetime.now()
        data_formatada = agora.strftime("%Y-%m-%d %H-%M")
        
        nome_arquivo = f"[BACKUP {data_formatada}] {nome_original}.xlsx"
        caminho_final = backup_dir / nome_arquivo
        
        print("  [Drive API] Exportando planilha do Google Sheets para XLSX (Excel)...")
        # O método 'export_media' faz a conversão em tempo real nos servidores do Google
        request = service.files().export_media(
            fileId=spreadsheet_id,
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        conteudo_binario = request.execute()
        
        print("  [Local] Gravando arquivo digital no disco...")
        with open(caminho_final, "wb") as f:
            f.write(conteudo_binario)
            
        print("➔ Cópia local gerada com sucesso!")
        return nome_arquivo
        
    except Exception as e:
        print(f"❌ ERRO no processo de backup local: {e}", file=sys.stderr)
        return None


def main():
    print("=" * 80)
    print("INICIANDO ESCOPO 4: BACKUP LOCAL EM EXCEL (.XLSX)")
    print("=" * 80)

    # Coleta as variáveis com fallback de string vazia para agradar o linter (Pylance/Pyright)
    credentials_raw = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID", "")
    
    # Nova variável ou fallback seguindo exatamente o padrão do Escopo 1
    backup_dir_raw = os.getenv("LOCAL_BACKUP_DIR", "./dados/backups/")

    erros = []
    if not credentials_raw:
        erros.append("- GOOGLE_APPLICATION_CREDENTIALS (caminho do seu JSON)")
    if not spreadsheet_id:
        erros.append("- GOOGLE_SHEETS_ID (ID da planilha original)")

    if erros:
        print("❌ ERRO: Faltam configurações essenciais no seu arquivo .env:")
        for erro in erros:
            print(erro)
        sys.exit(1)

    # TRATAMENTO DE PATHS RELATIVOS (Igualzinho ao Escopo 1):
    # Trata as credenciais
    credenciais_limpo = credentials_raw.lstrip("./")
    credentials_path = (PASTA_ESCOPO / credenciais_limpo).resolve()

    # Trata a pasta de saída do backup local
    diretorio_limpo = backup_dir_raw.lstrip("./")
    backup_dir = (PASTA_ESCOPO / diretorio_limpo).resolve()

    if not credentials_path.exists():
        print(f"❌ ERRO: O arquivo de credenciais não foi encontrado em: {credentials_path}")
        sys.exit(1)

    # Cria as pastas locais se não existirem (dados/backups/)
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Executa a função passando os paths absolutos tratados
    arquivo_gerado = realizar_backup_local_xlsx(credentials_path, spreadsheet_id, backup_dir)
    
    if arquivo_gerado:
        print(f"\n✓ Escopo 4 finalizado! Arquivo: {arquivo_gerado}")
    else:
        print("\n⚠️ Escopo 4 terminou com falhas (veja os logs acima).")
    print("=" * 80)


if __name__ == "__main__":
    main()