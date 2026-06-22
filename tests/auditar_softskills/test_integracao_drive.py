from unittest.mock import MagicMock, patch

import gspread

from scripthub.scripts.auditar_softskills.config import Config, DriveConfig, MoodleConfig
from scripthub.scripts.auditar_softskills.integracao_drive import upload_to_drive


def _make_config(tmp_path):
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text("{}")
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            url="https://moodle.test",
            bootcamp_cat_id="136",
            aprovados_cat_id="140",
        ),
        drive=DriveConfig(folder_id="pasta-id-123", credentials_path=creds_file),
        output_dir=tmp_path / "bootcamps",
        aprovados_dir=tmp_path / "aprovados",
    )


def _make_drive_service(existing_files=None):
    service = MagicMock()
    files = service.files.return_value
    files.list.return_value.execute.return_value = {"files": existing_files or []}
    files.create.return_value.execute.return_value = {"id": "novo-id-123"}
    return service


def _make_sheets_mock(worksheet_exists=True):
    """Retorna mocks de gspread (gc, spreadsheet, worksheet)."""
    ws = MagicMock()
    sh = MagicMock()

    if worksheet_exists:
        sh.worksheet.return_value = ws
    else:
        sh.worksheet.side_effect = gspread.WorksheetNotFound
        sh.add_worksheet.return_value = ws

    gc = MagicMock()
    gc.open_by_key.return_value = sh
    return gc, sh, ws


@patch("automacao_de_softskills.integracao_drive.gspread.authorize")
@patch("automacao_de_softskills.integracao_drive.build")
@patch("automacao_de_softskills.integracao_drive.service_account.Credentials.from_service_account_file")
def test_upload_to_drive_cria_planilha_quando_nao_existe(mock_creds, mock_build, mock_authorize, tmp_path):
    csv_file = tmp_path / "aprovados_bootcamp_fap2026.csv"
    csv_file.write_text("Nome,Email\nJoão,joao@example.com")

    service = _make_drive_service(existing_files=[])
    mock_build.return_value = service
    gc, sh, ws = _make_sheets_mock()
    mock_authorize.return_value = gc

    config = _make_config(tmp_path)
    upload_to_drive(str(csv_file), config)

    service.files.return_value.create.assert_called_once()
    call_kwargs = service.files.return_value.create.call_args
    assert call_kwargs.kwargs["body"]["name"] == "aprovados_bootcamp_fap2026"
    assert call_kwargs.kwargs["body"]["parents"] == ["pasta-id-123"]
    assert call_kwargs.kwargs["body"]["mimeType"] == "application/vnd.google-apps.spreadsheet"


@patch("automacao_de_softskills.integracao_drive.gspread.authorize")
@patch("automacao_de_softskills.integracao_drive.build")
@patch("automacao_de_softskills.integracao_drive.service_account.Credentials.from_service_account_file")
def test_upload_to_drive_reutiliza_planilha_existente(mock_creds, mock_build, mock_authorize, tmp_path):
    csv_file = tmp_path / "aprovados_bootcamp_fap2026.csv"
    csv_file.write_text("Nome,Email\nJoão,joao@example.com")

    service = _make_drive_service(existing_files=[{"id": "planilha-existente-456"}])
    mock_build.return_value = service
    gc, sh, ws = _make_sheets_mock()
    mock_authorize.return_value = gc

    config = _make_config(tmp_path)
    upload_to_drive(str(csv_file), config)

    service.files.return_value.create.assert_not_called()
    gc.open_by_key.assert_called_once_with("planilha-existente-456")


@patch("automacao_de_softskills.integracao_drive.gspread.authorize")
@patch("automacao_de_softskills.integracao_drive.build")
@patch("automacao_de_softskills.integracao_drive.service_account.Credentials.from_service_account_file")
def test_upload_to_drive_atualiza_apenas_aba_dados(mock_creds, mock_build, mock_authorize, tmp_path):
    csv_file = tmp_path / "aprovados_bootcamp_fap2026.csv"
    csv_file.write_text("Nome,Email\nJoão,joao@example.com")

    mock_build.return_value = _make_drive_service(existing_files=[{"id": "abc"}])
    gc, sh, ws = _make_sheets_mock(worksheet_exists=True)
    mock_authorize.return_value = gc

    config = _make_config(tmp_path)
    upload_to_drive(str(csv_file), config)

    sh.worksheet.assert_called_once_with("Dados")
    ws.clear.assert_called_once()
    ws.update.assert_called_once()


@patch("automacao_de_softskills.integracao_drive.gspread.authorize")
@patch("automacao_de_softskills.integracao_drive.build")
@patch("automacao_de_softskills.integracao_drive.service_account.Credentials.from_service_account_file")
def test_upload_to_drive_cria_aba_dados_se_nao_existir(mock_creds, mock_build, mock_authorize, tmp_path):
    csv_file = tmp_path / "aprovados_bootcamp_fap2026.csv"
    csv_file.write_text("Nome,Email\nJoão,joao@example.com")

    mock_build.return_value = _make_drive_service(existing_files=[{"id": "abc"}])
    gc, sh, ws = _make_sheets_mock(worksheet_exists=False)
    mock_authorize.return_value = gc

    config = _make_config(tmp_path)
    upload_to_drive(str(csv_file), config)

    sh.add_worksheet.assert_called_once_with(title="Dados", rows=10000, cols=20)
    ws.clear.assert_called_once()
    ws.update.assert_called_once()


@patch("automacao_de_softskills.integracao_drive.gspread.authorize")
@patch("automacao_de_softskills.integracao_drive.build")
@patch("automacao_de_softskills.integracao_drive.service_account.Credentials.from_service_account_file")
def test_upload_to_drive_nunca_deleta(mock_creds, mock_build, mock_authorize, tmp_path):
    csv_file = tmp_path / "aprovados_bootcamp_fap2026.csv"
    csv_file.write_text("Nome,Email\nJoão,joao@example.com")

    service = _make_drive_service(existing_files=[{"id": "abc"}])
    mock_build.return_value = service
    gc, sh, ws = _make_sheets_mock()
    mock_authorize.return_value = gc

    config = _make_config(tmp_path)
    upload_to_drive(str(csv_file), config)

    service.files.return_value.delete.assert_not_called()
    sh.del_worksheet.assert_not_called()


@patch("automacao_de_softskills.integracao_drive.gspread.authorize")
@patch("automacao_de_softskills.integracao_drive.build")
@patch("automacao_de_softskills.integracao_drive.service_account.Credentials.from_service_account_file")
def test_upload_to_drive_autentica_com_scopes_corretos(mock_creds, mock_build, mock_authorize, tmp_path):
    csv_file = tmp_path / "aprovados_bootcamp_fap2026.csv"
    csv_file.write_text("Nome,Email\nJoão,joao@example.com")

    mock_build.return_value = _make_drive_service()
    mock_authorize.return_value = _make_sheets_mock()[0]

    config = _make_config(tmp_path)
    upload_to_drive(str(csv_file), config)

    _, kwargs = mock_creds.call_args
    assert "https://www.googleapis.com/auth/drive" in kwargs["scopes"]
    assert "https://www.googleapis.com/auth/spreadsheets" in kwargs["scopes"]
