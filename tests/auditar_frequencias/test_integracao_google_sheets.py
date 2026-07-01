import pytest

from scripthub.scripts.auditar_frequencias.config import Config, GsheetsConfig, MoodleConfig
from scripthub.scripts.auditar_frequencias.integracao_google_sheets import main

_PATCH = "scripthub.scripts.auditar_frequencias.integracao_google_sheets"


@pytest.fixture
def config(tmp_path):
    export_dir = tmp_path / "exportacao"
    export_dir.mkdir()
    creds = tmp_path / "credentials.json"
    creds.write_text("{}")
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            url_login="https://example.com/login",
            urls_frequencias={"Turma A": "https://example.com/freq"},
            caminho_exportacao=export_dir,
        ),
        gsheets=GsheetsConfig(
            id_planilha="planilha-id-123",
            caminho_json_credenciais=creds,
        ),
    )


def _add_xlsx(config, nome="Turma A"):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Nome", "Nota"])
    ws.append(["Joao", 8.5])
    path = config.moodle.caminho_exportacao / f"{nome}.xlsx"
    wb.save(path)
    return path


def _setup_mock(mocker, config):
    mock_ws = mocker.MagicMock()
    mock_planilha = mocker.MagicMock()
    mock_client = mocker.patch(f"{_PATCH}.GoogleSheetsClient").return_value
    mock_client.planilha.return_value = mock_planilha
    mock_client.obter_ou_criar_aba.return_value = mock_ws
    return mock_client, mock_planilha, mock_ws


def test_main_levanta_runtime_sem_diretorio_exportacao(config):
    config.moodle.caminho_exportacao.rmdir()

    with pytest.raises(RuntimeError, match="exportação"):
        main(config)


def test_main_levanta_runtime_sem_credenciais(config):
    config.gsheets.caminho_json_credenciais.unlink()

    with pytest.raises(RuntimeError, match="credenciais"):
        main(config)


def test_main_levanta_runtime_sem_id_planilha(config):
    config.gsheets.id_planilha = ""

    with pytest.raises(RuntimeError, match="id_planilha"):
        main(config)


def test_main_levanta_runtime_sem_arquivos_xlsx(config, mocker):
    mocker.patch(f"{_PATCH}.GoogleSheetsClient")

    with pytest.raises(RuntimeError, match="XLSX"):
        main(config)


def test_main_atualiza_planilha_com_xlsx(config, mocker):
    _add_xlsx(config)
    _, _, mock_ws = _setup_mock(mocker, config)

    main(config)

    mock_ws.clear.assert_called_once()
    mock_ws.update.assert_called_once()


def test_main_cria_aba_se_nao_existir(config, mocker):
    _add_xlsx(config)
    mock_client, mock_planilha, mock_ws = _setup_mock(mocker, config)

    main(config)

    mock_client.obter_ou_criar_aba.assert_called_once()
    mock_ws.update.assert_called_once()


def test_main_abre_planilha_pelo_id(config, mocker):
    _add_xlsx(config)
    mock_client, _, _ = _setup_mock(mocker, config)

    main(config)

    mock_client.planilha.assert_called_once_with("planilha-id-123")
