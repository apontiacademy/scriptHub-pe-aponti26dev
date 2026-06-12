import sys
from pathlib import Path

import gspread
import pandas as pd
from config import Config

BASE_DIR = Path(__file__).resolve().parent


def main(config: Config):
    """Main function that orchestrates Scope 3 (Google Sheets Integration)."""
    print("=" * 80)
    print("▶ [ESCOPO 3] INTEGRAÇÃO (GOOGLE SHEETS)")
    print("=" * 80)

    csv_path = config.moodle.report_analysis_output_csv
    credentials_path = config.gsheets.credentials_json_path
    sheet_id = config.gsheets.spreadsheet_id
    worksheet_name = config.gsheets.sheet_name

    if not csv_path.exists():
        print(f"  ❌ ERRO: Arquivo de auditoria não encontrado em: {csv_path}", file=sys.stderr)
        print("  • Certifique-se de rodar o Escopo 2 antes de iniciar o Escopo 3.", file=sys.stderr)
        print("=" * 80)
        sys.exit(1)

    if not credentials_path.exists():
        print(f"  ❌ ERRO: Arquivo de credenciais do Google não encontrado em: {credentials_path}", file=sys.stderr)
        print("=" * 80)
        sys.exit(1)

    if not sheet_id:
        print("  ❌ ERRO: GOOGLE_SHEETS_ID não configurado no arquivo de configurações.", file=sys.stderr)
        print("=" * 80)
        sys.exit(1)

    print(f"  • Lendo dados locais de {csv_path.name}...")
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except Exception:
        try:
            df = pd.read_csv(csv_path, encoding="latin1")
        except Exception as e:
            print(f"  ❌ ERRO: Falha ao ler o arquivo CSV local: {e}", file=sys.stderr)
            print("=" * 80)
            sys.exit(1)

    if df.shape[1] < 4:
        print("  ❌ ERRO: O CSV de resultado possui menos de 4 colunas. Coluna D indisponível.", file=sys.stderr)
        print("=" * 80)
        sys.exit(1)

    column_d_header = df.columns[3]
    column_d_values = df.iloc[:, 3].fillna("").astype(str).tolist()

    payload_to_upload = [[column_d_header]] + [[value] for value in column_d_values]

    try:
        print("  • Autenticando com a API do Google...")
        gc = gspread.service_account(filename=str(credentials_path))
        
        print("  • Abrindo a planilha por ID...")
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)

        print(f"  • Limpando dados antigos da Coluna D na aba '{worksheet_name}'...")
        worksheet.batch_clear(['D:D'])

        print(f"  • Colando novos dados na Coluna D (Total de linhas: {len(payload_to_upload)})...")
        worksheet.update(range_name='D1', values=payload_to_upload)

        print("  ✔ Google Sheets atualizado com sucesso!")
        print("\n✔ Escopo 3 finalizado com sucesso!")

    except gspread.exceptions.WorksheetNotFound:
        print(f"  ❌ ERRO: A aba '{worksheet_name}' não foi encontrada na planilha fornecida.", file=sys.stderr)
        print("=" * 80)
        sys.exit(1)
    except Exception as e:
        print(f"  ❌ ERRO inesperado durante a integração com o Google Sheets: {e}", file=sys.stderr)
        print("=" * 80)
        sys.exit(1)

    print("=" * 80)


if __name__ == "__main__":
    loaded_config = Config.load()
    main(loaded_config)