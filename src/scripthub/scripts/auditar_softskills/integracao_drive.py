import csv
from pathlib import Path

import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build

from scripthub.services import log

from .config import Config


def upload_to_drive(file_path: str, config: Config) -> None:
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]
    creds = service_account.Credentials.from_service_account_file(str(config.drive.credentials_path), scopes=scopes)
    drive_service = build("drive", "v3", credentials=creds)

    folder_id = config.drive.folder_id

    # Verifica se a pasta está acessível (suporta Shared Drives)
    try:
        folder_info = drive_service.files().get(fileId=folder_id, fields="id,name", supportsAllDrives=True).execute()
        log.passo(f"Pasta acessível: {folder_info['name']}")
    except Exception as e:
        log.erro(f"Pasta não acessível (verifique o compartilhamento): {e}")
        return

    sheet_name = Path(file_path).stem  # nome sem extensão

    existing = (
        drive_service.files()
        .list(
            q=(
                f"name='{sheet_name}' and '{folder_id}' in parents"
                " and trashed=false"
                " and mimeType='application/vnd.google-apps.spreadsheet'"
            ),
            fields="files(id)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
        .get("files", [])
    )

    if existing:
        sheet_id = existing[0]["id"]
        log.passo("Planilha existente encontrada.")
    else:
        sheet_id = (
            drive_service.files()
            .create(
                body={
                    "name": sheet_name,
                    "parents": [folder_id],
                    "mimeType": "application/vnd.google-apps.spreadsheet",
                },
                fields="id",
                supportsAllDrives=True,
            )
            .execute()["id"]
        )
        log.passo("Nova planilha criada no Drive.")

    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)

    try:
        ws = sh.worksheet("Dados")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="Dados", rows=10000, cols=20)

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

    ws.clear()
    ws.update([header] + data)

    # Aplica formato 0.00 nas colunas numéricas
    num_col_letters = [chr(ord("A") + i) for i in sorted(num_cols)]
    for col_letter in num_col_letters:
        ws.format(
            f"{col_letter}2:{col_letter}{len(data) + 1}",
            {"numberFormat": {"type": "NUMBER", "pattern": "0.00"}},
        )

    log.ok(f'Aba "Dados" atualizada com {len(data)} linhas.')
