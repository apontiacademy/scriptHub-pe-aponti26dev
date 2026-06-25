from __future__ import annotations

from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class GoogleDriveClient:
    """Wrapper de autenticação e operações comuns do Google Drive API."""

    def __init__(self, creds_path: Path, scopes: list[str]) -> None:
        creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
        self._service = build("drive", "v3", credentials=creds)

    def metadados(self, file_id: str, *, fields: str = "name") -> dict:
        """Retorna metadados de um arquivo/planilha do Drive."""
        return self._service.files().get(fileId=file_id, fields=fields, supportsAllDrives=True).execute()

    def exportar_xlsx(self, file_id: str) -> bytes:
        """Exporta uma planilha Google Sheets como XLSX e retorna os bytes."""
        return self._service.files().export_media(
            fileId=file_id,
            mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ).execute()

    def listar_arquivos(self, query: str) -> list[dict]:
        """Lista arquivos no Drive com a query fornecida. Retorna lista de dicts com 'id'."""
        return (
            self._service.files()
            .list(
                q=query,
                fields="files(id,name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
            .get("files", [])
        )

    def criar_arquivo(self, body: dict) -> str:
        """Cria um arquivo no Drive com o body fornecido. Retorna o ID criado."""
        return (
            self._service.files()
            .create(body=body, fields="id", supportsAllDrives=True)
            .execute()["id"]
        )
