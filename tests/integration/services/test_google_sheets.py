from unittest.mock import MagicMock

from scripthub.services.google.sheets import GoogleSheetsClient

_PATCH = "scripthub.services.google.sheets"


# ── inicialização ─────────────────────────────────────────────────────────────


def test_init_autentica_com_service_account(mocker, tmp_path):
    creds = tmp_path / "creds.json"
    creds.write_text("{}")
    mock_auth = mocker.patch(f"{_PATCH}.gspread.service_account", return_value=MagicMock())

    GoogleSheetsClient(creds)

    mock_auth.assert_called_once_with(filename=str(creds))
