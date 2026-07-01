import gspread

from scripthub.scripts.auditar_softskills.config import Config, DriveConfig, MoodleConfig
from scripthub.scripts.auditar_softskills.integracao_drive import upload_to_drive

_PATCH_BASE = "scripthub.scripts.auditar_softskills.integracao_drive"


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


def _make_csv(tmp_path, nome="aprovados_bootcamp_fap2026.csv"):
    csv_file = tmp_path / nome
    csv_file.write_text("Nome,Email\nJoão,joao@example.com", encoding="utf-8")
    return csv_file


def _setup_drive_mocks(mocker, existing_files=None):
    mocker.patch(f"{_PATCH_BASE}.service_account.Credentials.from_service_account_file")
    mock_drive = mocker.patch(f"{_PATCH_BASE}.build").return_value
    files = mock_drive.files.return_value
    files.get.return_value.execute.return_value = {"id": "folder", "name": "Folder"}
    files.list.return_value.execute.return_value = {"files": existing_files or []}
    files.create.return_value.execute.return_value = {"id": "novo-id-123"}
    return mock_drive


def _setup_gspread_mock(mocker, worksheet_exists=True):
    ws = mocker.MagicMock()
    sh = mocker.MagicMock()
    if worksheet_exists:
        sh.worksheet.return_value = ws
    else:
        sh.worksheet.side_effect = gspread.WorksheetNotFound
        sh.add_worksheet.return_value = ws
    gc = mocker.MagicMock()
    gc.open_by_key.return_value = sh
    mocker.patch(f"{_PATCH_BASE}.gspread.authorize", return_value=gc)
    return gc, sh, ws


def test_upload_to_drive_cria_planilha_quando_nao_existe(tmp_path, mocker):
    csv_file = _make_csv(tmp_path)
    mock_drive = _setup_drive_mocks(mocker, existing_files=[])
    _, _, _ = _setup_gspread_mock(mocker)

    upload_to_drive(str(csv_file), _make_config(tmp_path))

    mock_drive.files.return_value.create.assert_called_once()
    kwargs = mock_drive.files.return_value.create.call_args.kwargs
    assert kwargs["body"]["name"] == "aprovados_bootcamp_fap2026"
    assert kwargs["body"]["parents"] == ["pasta-id-123"]
    assert kwargs["body"]["mimeType"] == "application/vnd.google-apps.spreadsheet"


def test_upload_to_drive_reutiliza_planilha_existente(tmp_path, mocker):
    csv_file = _make_csv(tmp_path)
    _setup_drive_mocks(mocker, existing_files=[{"id": "planilha-existente-456"}])
    gc, _, _ = _setup_gspread_mock(mocker)

    upload_to_drive(str(csv_file), _make_config(tmp_path))

    mock_drive_create = mocker.patch(f"{_PATCH_BASE}.build").return_value.files.return_value.create
    mock_drive_create.assert_not_called()
    gc.open_by_key.assert_called_once_with("planilha-existente-456")


def test_upload_to_drive_atualiza_aba_dados(tmp_path, mocker):
    csv_file = _make_csv(tmp_path)
    _setup_drive_mocks(mocker, existing_files=[{"id": "abc"}])
    _, sh, ws = _setup_gspread_mock(mocker, worksheet_exists=True)

    upload_to_drive(str(csv_file), _make_config(tmp_path))

    sh.worksheet.assert_called_once_with("Dados")
    ws.clear.assert_called_once()
    ws.update.assert_called_once()


def test_upload_to_drive_cria_aba_dados_se_nao_existir(tmp_path, mocker):
    csv_file = _make_csv(tmp_path)
    _setup_drive_mocks(mocker, existing_files=[{"id": "abc"}])
    _, sh, ws = _setup_gspread_mock(mocker, worksheet_exists=False)

    upload_to_drive(str(csv_file), _make_config(tmp_path))

    sh.add_worksheet.assert_called_once_with(title="Dados", rows=10000, cols=20)
    ws.clear.assert_called_once()
    ws.update.assert_called_once()


def test_upload_to_drive_nunca_deleta_arquivos(tmp_path, mocker):
    csv_file = _make_csv(tmp_path)
    mock_drive = _setup_drive_mocks(mocker, existing_files=[{"id": "abc"}])
    _, sh, _ = _setup_gspread_mock(mocker)

    upload_to_drive(str(csv_file), _make_config(tmp_path))

    mock_drive.files.return_value.delete.assert_not_called()
    sh.del_worksheet.assert_not_called()


def test_upload_to_drive_autentica_com_scopes_corretos(tmp_path, mocker):
    csv_file = _make_csv(tmp_path)
    mock_creds = mocker.patch(
        f"{_PATCH_BASE}.service_account.Credentials.from_service_account_file"
    )
    mocker.patch(f"{_PATCH_BASE}.build").return_value.files.return_value.get.return_value.execute.return_value = {
        "id": "f",
        "name": "F",
    }
    mocker.patch(f"{_PATCH_BASE}.build").return_value.files.return_value.list.return_value.execute.return_value = {
        "files": [{"id": "x"}]
    }
    _setup_gspread_mock(mocker)

    upload_to_drive(str(csv_file), _make_config(tmp_path))

    _, kwargs = mock_creds.call_args
    assert "https://www.googleapis.com/auth/drive" in kwargs["scopes"]
    assert "https://www.googleapis.com/auth/spreadsheets" in kwargs["scopes"]
