import csv
from pathlib import Path

from scripthub.services import log
from scripthub.services.google.drive import GoogleDriveClient
from scripthub.services.google.sheets import GoogleSheetsClient

from .config import Config

_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def upload_to_drive(file_path: str, config: Config) -> None:
    """Faz upload do CSV de resultados para uma planilha Google no Drive."""
    drive = GoogleDriveClient(config.drive.credentials_path, _SCOPES)
    folder_id = config.drive.folder_id

    try:
        folder_info = drive.metadados(folder_id, fields="id,name")
        log.passo(f"Pasta acessível: {folder_info['name']}")
    except Exception as e:
        log.erro(f"Pasta não acessível (verifique o compartilhamento): {e}")
        return

    sheet_name = Path(file_path).stem

    existing = drive.listar_arquivos(
        f"name='{sheet_name}' and '{folder_id}' in parents"
        " and trashed=false"
        " and mimeType='application/vnd.google-apps.spreadsheet'"
    )

    if existing:
        sheet_id = existing[0]["id"]
        log.passo("Planilha existente encontrada.")
    else:
        sheet_id = drive.criar_arquivo(
            {
                "name": sheet_name,
                "parents": [folder_id],
                "mimeType": "application/vnd.google-apps.spreadsheet",
            }
        )
        log.passo("Nova planilha criada no Drive.")

    gc = GoogleSheetsClient(config.drive.credentials_path, _SCOPES)
    sh = gc.planilha(sheet_id)
    ws = gc.obter_ou_criar_aba(sh, "Dados", linhas=10000, colunas=20)

    def _parse(value):
        try:
            return float(value.replace(",", "."))
        except (ValueError, AttributeError):
            return value

    with open(file_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        num_cols = {i for i, col in enumerate(header) if col.startswith("Nota") or col == "Turma Trilha"}
        data = [[_parse(cell) if i in num_cols else cell for i, cell in enumerate(row)] for row in reader]

    # Limpa apenas as colunas de dados (A:L), preservando M em diante (ex: Lista Filtrada)
    ws.batch_clear(["A:L"])
    ws.update([header] + data)

    num_col_letters = [chr(ord("A") + i) for i in sorted(num_cols)]
    for col_letter in num_col_letters:
        ws.format(
            f"{col_letter}2:{col_letter}{len(data) + 1}",
            {"numberFormat": {"type": "NUMBER", "pattern": "0.00"}},
        )

    log.ok(f'Aba "Dados" atualizada com {len(data)} linhas.')
