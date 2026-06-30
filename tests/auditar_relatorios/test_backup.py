from pathlib import Path

import pytest

from scripthub.scripts.auditar_relatorios.backup import main, realizar_backup_xlsx_local
from scripthub.scripts.auditar_relatorios.config import Config, GsheetsConfig, MoodleConfig

_PATCH = "scripthub.scripts.auditar_relatorios.backup"


def _make_config(tmp_path, id_planilha="planilha-id-123"):
    creds = tmp_path / "credentials.json"
    creds.write_text("{}")
    backup_dir = tmp_path / "backups"
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            caminho_download_relatorio=tmp_path / "relatorios",
            csv_residentes=tmp_path / "residentes.csv",
            csv_saida_analise=tmp_path / "resultado.csv",
            url_login="https://example.com/login",
            urls_relatorios=["https://example.com/r1"],
            exportar_analise_relatorio=False,
            caminho_exportacao_analise=None,
        ),
        gsheets=GsheetsConfig(
            id_planilha=id_planilha,
            nome_aba="Resultados",
            caminho_backup_local=backup_dir,
            caminho_json_credenciais=creds,
        ),
    )


def _setup_drive_mock(mocker, sheet_name="Planilha Teste", xlsx_content=b"xlsx-content"):
    mock_drive = mocker.patch(f"{_PATCH}.GoogleDriveClient").return_value
    mock_drive.metadados.return_value = {"name": sheet_name}
    mock_drive.exportar_xlsx.return_value = xlsx_content
    return mock_drive


def test_backup_salva_arquivo_xlsx_no_diretorio(tmp_path, mocker):
    _setup_drive_mock(mocker)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    creds = tmp_path / "credentials.json"
    creds.write_text("{}")

    nome = realizar_backup_xlsx_local(creds, "planilha-id", backup_dir)

    assert nome is not None
    assert nome.endswith(".xlsx")
    assert (backup_dir / nome).exists()


def test_backup_nome_arquivo_contem_marcador_de_backup(tmp_path, mocker):
    _setup_drive_mock(mocker, sheet_name="Minha Planilha")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    creds = tmp_path / "credentials.json"
    creds.write_text("{}")

    nome = realizar_backup_xlsx_local(creds, "planilha-id", backup_dir)

    assert "[BACKUP" in nome
    assert "Minha Planilha" in nome


def test_backup_falha_api_retorna_none(tmp_path, mocker):
    mock_drive = mocker.patch(f"{_PATCH}.GoogleDriveClient")
    mock_drive.side_effect = RuntimeError("API Error")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    creds = tmp_path / "credentials.json"
    creds.write_text("{}")

    resultado = realizar_backup_xlsx_local(creds, "planilha-id", backup_dir)

    assert resultado is None


def test_main_levanta_runtime_error_sem_credenciais(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.gsheets.caminho_json_credenciais.unlink()

    with pytest.raises(RuntimeError, match="credenciais"):
        main(config)


def test_main_levanta_runtime_error_sem_id_planilha(tmp_path):
    config = _make_config(tmp_path, id_planilha="")

    with pytest.raises(RuntimeError, match="id_planilha"):
        main(config)


def test_main_cria_diretorio_de_backup_automaticamente(tmp_path, mocker):
    _setup_drive_mock(mocker)
    config = _make_config(tmp_path)
    assert not config.gsheets.caminho_backup_local.exists()

    main(config)

    assert config.gsheets.caminho_backup_local.exists()
