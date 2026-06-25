from pathlib import Path
from unittest.mock import MagicMock

import gspread
import pytest

from scripthub.services.google.sheets import GoogleSheetsClient

_PATCH = "scripthub.services.google.sheets"


def _client(mocker, creds_path=Path("creds.json")):
    mocker.patch(f"{_PATCH}.gspread.service_account", return_value=MagicMock())
    return GoogleSheetsClient(creds_path)


# ── inicialização ─────────────────────────────────────────────────────────────


def test_init_autentica_com_service_account(mocker, tmp_path):
    creds = tmp_path / "creds.json"
    creds.write_text("{}")
    mock_auth = mocker.patch(f"{_PATCH}.gspread.service_account", return_value=MagicMock())

    GoogleSheetsClient(creds)

    mock_auth.assert_called_once_with(filename=str(creds))


# ── planilha ──────────────────────────────────────────────────────────────────


def test_planilha_abre_por_chave(mocker):
    mock_gc = MagicMock()
    mocker.patch(f"{_PATCH}.gspread.service_account", return_value=mock_gc)
    client = GoogleSheetsClient(Path("creds.json"))

    client.planilha("id-abc123")

    mock_gc.open_by_key.assert_called_once_with("id-abc123")


def test_planilha_levanta_runtime_error_quando_nao_encontrada(mocker):
    mock_gc = MagicMock()
    mock_gc.open_by_key.side_effect = gspread.exceptions.SpreadsheetNotFound
    mocker.patch(f"{_PATCH}.gspread.service_account", return_value=mock_gc)
    client = GoogleSheetsClient(Path("creds.json"))

    with pytest.raises(RuntimeError, match="[Pp]lanilha"):
        client.planilha("id-inexistente")


# ── obter_ou_criar_aba ────────────────────────────────────────────────────────


def test_obter_ou_criar_aba_retorna_aba_existente(mocker):
    mock_gc = MagicMock()
    mocker.patch(f"{_PATCH}.gspread.service_account", return_value=mock_gc)
    client = GoogleSheetsClient(Path("creds.json"))
    mock_planilha = MagicMock()
    mock_ws = MagicMock()
    mock_planilha.worksheet.return_value = mock_ws

    resultado = client.obter_ou_criar_aba(mock_planilha, "Turma 01")

    assert resultado is mock_ws
    mock_planilha.add_worksheet.assert_not_called()


def test_obter_ou_criar_aba_cria_nova_quando_nao_existe(mocker):
    mock_gc = MagicMock()
    mocker.patch(f"{_PATCH}.gspread.service_account", return_value=mock_gc)
    client = GoogleSheetsClient(Path("creds.json"))
    mock_planilha = MagicMock()
    mock_planilha.worksheet.side_effect = gspread.exceptions.WorksheetNotFound
    nova_aba = MagicMock()
    mock_planilha.add_worksheet.return_value = nova_aba

    resultado = client.obter_ou_criar_aba(mock_planilha, "Nova Turma", linhas=500, colunas=10)

    mock_planilha.add_worksheet.assert_called_once_with(title="Nova Turma", rows=500, cols=10)
    assert resultado is nova_aba


def test_obter_ou_criar_aba_usa_defaults_de_tamanho(mocker):
    mock_gc = MagicMock()
    mocker.patch(f"{_PATCH}.gspread.service_account", return_value=mock_gc)
    client = GoogleSheetsClient(Path("creds.json"))
    mock_planilha = MagicMock()
    mock_planilha.worksheet.side_effect = gspread.exceptions.WorksheetNotFound

    client.obter_ou_criar_aba(mock_planilha, "Aba")

    _, kwargs = mock_planilha.add_worksheet.call_args
    assert kwargs["rows"] >= 100
    assert kwargs["cols"] >= 20
