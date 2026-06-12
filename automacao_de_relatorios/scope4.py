import sys
from datetime import datetime
from pathlib import Path

from config import Config
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent


def run_local_xlsx_backup(credentials_path: Path, spreadsheet_id: str, backup_dir: Path) -> str | None:
    """Fetches the Google Sheet, exports it as an .xlsx file, and saves it locally with a timestamp."""
    scopes = ['https://www.googleapis.com/auth/drive']
    
    try:
        print("  • Autenticando com a conta de serviço...")
        creds = Credentials.from_service_account_file(str(credentials_path), scopes=scopes)
        service = build('drive', 'v3', credentials=creds)
        
        print("  • Buscando informações da planilha original...")
        file_metadata = service.files().get(
            fileId=spreadsheet_id, 
            fields='name',
            supportsAllDrives=True
        ).execute()
        original_name = file_metadata.get('name', 'Planilha_Sem_Nome')
        
        current_time = datetime.now()
        formatted_date = current_time.strftime("%Y-%m-%d %H-%M")
        
        filename = f"[BACKUP {formatted_date}] {original_name}.xlsx"
        final_path = backup_dir / filename
        
        print("  • Exportando planilha do Google Sheets para XLSX (Excel)...")
        request = service.files().export_media(
            fileId=spreadsheet_id,
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        binary_content = request.execute()
        
        print("  • Gravando arquivo digital no disco...")
        with open(final_path, "wb") as f:
            f.write(binary_content)
            
        print(f"  ✔ Cópia local gerada: {filename}")
        return filename
        
    except Exception as e:
        print(f"  ❌ ERRO: Falha no processo de backup local: {e}", file=sys.stderr)
        return None


def main(config: Config):
    """Main function that orchestrates Scope 4 (Automated Local Backup)."""
    print("=" * 80)
    print("▶ [ESCOPO 4] BACKUP AUTOMÁTICO (.XLSX)")
    print("=" * 80)

    credentials_path = config.gsheets.credentials_json_path
    spreadsheet_id = config.gsheets.spreadsheet_id
    backup_dir = config.gsheets.local_backup_path

    if not credentials_path.exists():
        print(f"  ❌ ERRO: O arquivo de credenciais não foi encontrado em: {credentials_path}", file=sys.stderr)
        print("=" * 80)
        sys.exit(1)

    if not spreadsheet_id:
        print("  ❌ ERRO: GOOGLE_SHEETS_ID não configurado no arquivo de configurações.", file=sys.stderr)
        print("=" * 80)
        sys.exit(1)

    backup_dir.mkdir(parents=True, exist_ok=True)

    generated_file = run_local_xlsx_backup(credentials_path, spreadsheet_id, backup_dir)
    
    if generated_file:
        print("\n✔ Escopo 4 finalizado com sucesso!")
    else:
        print("\n⚠️ Escopo 4 terminou com falhas (veja os logs acima).", file=sys.stderr)
        
    print("=" * 80)


if __name__ == "__main__":
    loaded_config = Config.load()
    main(loaded_config)