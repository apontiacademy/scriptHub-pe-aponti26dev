from pathlib import Path

import pytest

from scripthub.scripts.auditar_softskills.config import Config, DriveConfig, MoodleConfig
from scripthub.scripts.auditar_softskills.integracao_drive import upload_to_drive

_PATCH = "scripthub.scripts.auditar_softskills.integracao_drive"


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


def _setup_mock(mocker, existing_files=None):
    mock_drive = mocker.patch(f"{_PATCH}.GoogleDriveClient").return_value
    mock_sheets = mocker.patch(f"{_PATCH}.GoogleSheetsClient").return_value
    mock_drive.metadados.return_value = {"id": "folder", "name": "Folder"}
    mock_drive.listar_arquivos.return_value = existing_files or []
    mock_drive.criar_arquivo.return_value = "novo-id-123"
    mock_ws = mocker.MagicMock()
    mock_planilha = mocker.MagicMock()
    mock_sheets.planilha.return_value = mock_planilha
    mock_sheets.obter_ou_criar_aba.return_value = mock_ws
    return mock_drive, mock_sheets, mock_planilha, mock_ws


def test_upload_to_drive_cria_planilha_quando_nao_existe(tmp_path, mocker):
    csv_file = _make_csv(tmp_path)
    mock_drive, _, _, _ = _setup_mock(mocker, existing_files=[])

    upload_to_drive(str(csv_file), _make_config(tmp_path))

    mock_drive.criar_arquivo.assert_called_once()
    call_args = mock_drive.criar_arquivo.call_args[0][0]
    assert call_args["name"] == "aprovados_bootcamp_fap2026"
    assert call_args["parents"] == ["pasta-id-123"]
    assert call_args["mimeType"] == "application/vnd.google-apps.spreadsheet"


def test_upload_to_drive_reutiliza_planilha_existente(tmp_path, mocker):
    csv_file = _make_csv(tmp_path)
    mock_drive, mock_sheets, _, _ = _setup_mock(mocker, existing_files=[{"id": "planilha-existente-456"}])

    upload_to_drive(str(csv_file), _make_config(tmp_path))

    mock_drive.criar_arquivo.assert_not_called()
    mock_sheets.planilha.assert_called_once_with("planilha-existente-456")


def test_upload_to_drive_atualiza_aba_dados(tmp_path, mocker):
    csv_file = _make_csv(tmp_path)
    _, _, mock_planilha, mock_ws = _setup_mock(mocker, existing_files=[{"id": "abc"}])

    upload_to_drive(str(csv_file), _make_config(tmp_path))

    mock_ws.clear.assert_called_once()
    mock_ws.update.assert_called_once()


def test_upload_to_drive_cria_aba_dados_se_nao_existir(tmp_path, mocker):
    csv_file = _make_csv(tmp_path)
    _, mock_sheets, _, mock_ws = _setup_mock(mocker, existing_files=[{"id": "abc"}])

    upload_to_drive(str(csv_file), _make_config(tmp_path))

    mock_sheets.obter_ou_criar_aba.assert_called_once()
    assert mock_sheets.obter_ou_criar_aba.call_args[0][1] == "Dados"
    mock_ws.clear.assert_called_once()
    mock_ws.update.assert_called_once()


def test_upload_to_drive_retorna_sem_erro_quando_pasta_inacessivel(tmp_path, mocker):
    csv_file = _make_csv(tmp_path)
    mock_drive = mocker.patch(f"{_PATCH}.GoogleDriveClient").return_value
    mocker.patch(f"{_PATCH}.GoogleSheetsClient")
    mock_drive.metadados.side_effect = RuntimeError("Pasta não acessível")

    # Deve retornar sem lançar exceção
    upload_to_drive(str(csv_file), _make_config(tmp_path))


def test_upload_to_drive_autentica_com_scopes_corretos(tmp_path, mocker):
    csv_file = _make_csv(tmp_path)
    mock_drive_cls = mocker.patch(f"{_PATCH}.GoogleDriveClient")
    mock_drive = mock_drive_cls.return_value
    mock_drive.metadados.return_value = {"id": "folder", "name": "Folder"}
    mock_drive.listar_arquivos.return_value = [{"id": "x"}]
    mock_sheets = mocker.patch(f"{_PATCH}.GoogleSheetsClient").return_value
    mock_sheets.planilha.return_value = mocker.MagicMock()
    mock_sheets.obter_ou_criar_aba.return_value = mocker.MagicMock()

    upload_to_drive(str(csv_file), _make_config(tmp_path))

    _, call_kwargs = mock_drive_cls.call_args
    scopes = call_kwargs.get("scopes", mock_drive_cls.call_args[0][1] if mock_drive_cls.call_args[0] else [])
    if not scopes:
        args = mock_drive_cls.call_args[0]
        scopes = args[1] if len(args) > 1 else []
    assert "https://www.googleapis.com/auth/drive" in scopes
