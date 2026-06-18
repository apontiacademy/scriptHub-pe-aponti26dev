import csv
from pathlib import Path

import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build

from .config import Config


def upload_to_drive(file_path: str, config: Config) -> None:
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]
    creds = service_account.Credentials.from_service_account_file(
        str(config.drive.credentials_path), scopes=scopes
    )
    drive_service = build("drive", "v3", credentials=creds)

    folder_id = config.drive.folder_id

    try:
        folder_info = drive_service.files().get(
            fileId=folder_id, fields="id,name", supportsAllDrives=True
        ).execute()
        print(f"  • Pasta acessível: {folder_info['name']}")
    except Exception as e:
        print(f"  ❌ Pasta não acessível (verifique o compartilhamento): {e}")
        return

    sheet_name = Path(file_path).stem

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
        print("  • Planilha existente encontrada.")
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
        print("  • Nova planilha criada no Drive.")

    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)

    def _parse(value: str):
        try:
            return float(value.replace(",", "."))
        except (ValueError, AttributeError):
            return value

    with open(file_path, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        num_cols = {i for i, col in enumerate(header) if col.startswith("Nota")}
        data = [
            [_parse(cell) if i in num_cols else cell for i, cell in enumerate(row)]
            for row in reader
        ]

    try:
        ws = sh.worksheet("Dados")
        if ws.col_count < len(header):
            ws.resize(cols=len(header) + 5)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="Dados", rows=10000, cols=len(header) + 5)

    ws.clear()
    ws.update([header] + data)

    if num_cols and data:
        nota_cols = sorted(num_cols)
        first_col = nota_cols[0] + 1   # gspread usa índice 1-based
        last_col = nota_cols[-1] + 1
        last_row = len(data) + 1
        ws.format(
            f"R2C{first_col}:R{last_row}C{last_col}",
            {"numberFormat": {"type": "NUMBER", "pattern": "0.00"}},
        )

    print(f'  ✔ Aba "Dados" atualizada com {len(data)} linhas e {len(header)} colunas.')
