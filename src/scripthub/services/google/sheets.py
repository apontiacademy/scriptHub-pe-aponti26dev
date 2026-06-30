from __future__ import annotations

from pathlib import Path

import gspread


class GoogleSheetsClient:
    """Wrapper de autenticação e operações comuns do Google Sheets via gspread."""

    def __init__(self, creds_path: Path, scopes: list[str] | None = None) -> None:
        kwargs: dict = {"filename": str(creds_path)}
        if scopes:
            kwargs["scopes"] = scopes
        self._gc = gspread.service_account(**kwargs)

    def planilha(self, spreadsheet_id: str):
        """Abre e retorna uma planilha pelo ID. Lança RuntimeError se não existir."""
        try:
            return self._gc.open_by_key(spreadsheet_id)
        except gspread.exceptions.SpreadsheetNotFound:
            raise RuntimeError(f"Planilha não encontrada: {spreadsheet_id}")

    def obter_ou_criar_aba(self, planilha, nome: str, *, linhas: int = 1000, colunas: int = 20):
        """Retorna a aba existente ou cria uma nova com o nome fornecido."""
        try:
            return planilha.worksheet(nome)
        except gspread.exceptions.WorksheetNotFound:
            return planilha.add_worksheet(title=nome, rows=linhas, cols=colunas)
