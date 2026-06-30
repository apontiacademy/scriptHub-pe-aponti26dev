from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripthub.services.google.drive import GoogleDriveClient

_PATCH = "scripthub.services.google.drive"
_SCOPES = ["https://www.googleapis.com/auth/drive"]


def _setup(mocker, xlsx_content=b"xlsx"):
    mocker.patch(f"{_PATCH}.Credentials.from_service_account_file")
    mock_service = mocker.patch(f"{_PATCH}.build").return_value
    mock_service.files.return_value.get.return_value.execute.return_value = {"name": "Planilha"}
    mock_service.files.return_value.export_media.return_value.execute.return_value = xlsx_content
    mock_service.files.return_value.list.return_value.execute.return_value = {"files": []}
    mock_service.files.return_value.create.return_value.execute.return_value = {"id": "new-id"}
    return mock_service


# ── inicialização ─────────────────────────────────────────────────────────────


def test_init_autentica_com_service_account(mocker, tmp_path):
    creds = tmp_path / "creds.json"
    creds.write_text("{}")
    mock_creds = mocker.patch(f"{_PATCH}.Credentials.from_service_account_file")
    mocker.patch(f"{_PATCH}.build")

    GoogleDriveClient(creds, _SCOPES)

    mock_creds.assert_called_once_with(str(creds), scopes=_SCOPES)


def test_init_builda_servico_drive(mocker, tmp_path):
    creds = tmp_path / "creds.json"
    creds.write_text("{}")
    mocker.patch(f"{_PATCH}.Credentials.from_service_account_file")
    mock_build = mocker.patch(f"{_PATCH}.build")

    GoogleDriveClient(creds, _SCOPES)

    mock_build.assert_called_once()
    assert mock_build.call_args[0][0] == "drive"


# ── metadados ─────────────────────────────────────────────────────────────────


def test_metadados_retorna_nome_da_planilha(mocker):
    mock_service = _setup(mocker)
    mock_service.files.return_value.get.return_value.execute.return_value = {"name": "Minha Planilha"}
    client = GoogleDriveClient(Path("creds.json"), _SCOPES)

    resultado = client.metadados("file-id-123")

    assert resultado["name"] == "Minha Planilha"


# ── exportar_xlsx ─────────────────────────────────────────────────────────────


def test_exportar_xlsx_retorna_bytes(mocker):
    _setup(mocker, xlsx_content=b"PK\x03\x04binary-xlsx")
    client = GoogleDriveClient(Path("creds.json"), _SCOPES)

    conteudo = client.exportar_xlsx("file-id")

    assert conteudo == b"PK\x03\x04binary-xlsx"


# ── listar_arquivos ───────────────────────────────────────────────────────────


def test_listar_arquivos_retorna_lista(mocker):
    mock_service = _setup(mocker)
    mock_service.files.return_value.list.return_value.execute.return_value = {
        "files": [{"id": "id-1"}, {"id": "id-2"}]
    }
    client = GoogleDriveClient(Path("creds.json"), _SCOPES)

    resultado = client.listar_arquivos("name='test' and trashed=false")

    assert len(resultado) == 2


def test_listar_arquivos_retorna_lista_vazia_quando_nenhum(mocker):
    _setup(mocker)
    client = GoogleDriveClient(Path("creds.json"), _SCOPES)

    resultado = client.listar_arquivos("name='inexistente'")

    assert resultado == []


# ── criar_arquivo ─────────────────────────────────────────────────────────────


def test_criar_arquivo_retorna_id(mocker):
    mock_service = _setup(mocker)
    mock_service.files.return_value.create.return_value.execute.return_value = {"id": "created-id"}
    client = GoogleDriveClient(Path("creds.json"), _SCOPES)

    file_id = client.criar_arquivo({"name": "Novo Arquivo", "parents": ["pasta-id"]})

    assert file_id == "created-id"
