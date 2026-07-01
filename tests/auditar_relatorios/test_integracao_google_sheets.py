import pytest

from scripthub.scripts.auditar_relatorios.config import Config, GsheetsConfig, MoodleConfig
from scripthub.scripts.auditar_relatorios.integracao_google_sheets import main

_PATCH_BASE = "scripthub.scripts.auditar_relatorios.integracao_google_sheets"


@pytest.fixture
def config(tmp_path):
    csv_saida = tmp_path / "dados" / "resultado.csv"
    creds = tmp_path / "credentials.json"
    creds.write_text("{}")
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            caminho_download_relatorio=tmp_path / "relatorios",
            headless=True,
            csv_residentes=tmp_path / "residentes.csv",
            csv_saida_analise=csv_saida,
            url_login="https://example.com/login",
            urls_relatorios=["https://example.com/r1"],
            exportar_analise_relatorio=False,
            caminho_exportacao_analise=None,
        ),
        gsheets=GsheetsConfig(
            id_planilha="planilha-id-123",
            nome_aba="Resultados",
            caminho_backup_local=tmp_path / "backups",
            caminho_json_credenciais=creds,
        ),
    )


def _write_csv(config, conteudo="Col A,Col B,Col C,Situacao\nJoao,x,y,Aprovado\n"):
    csv = config.moodle.csv_saida_analise
    csv.parent.mkdir(parents=True, exist_ok=True)
    csv.write_text(conteudo, encoding="utf-8")


def test_main_levanta_runtime_sem_csv(config):
    with pytest.raises(RuntimeError, match="não encontrado"):
        main(config)


def test_main_levanta_runtime_sem_credenciais(config):
    _write_csv(config)
    config.gsheets.caminho_json_credenciais.unlink()

    with pytest.raises(RuntimeError, match="credenciais"):
        main(config)


def test_main_levanta_runtime_sem_id_planilha(config):
    _write_csv(config)
    config.gsheets.id_planilha = ""

    with pytest.raises(RuntimeError, match="id_planilha"):
        main(config)


def test_main_levanta_runtime_com_csv_de_menos_colunas(config):
    _write_csv(config, conteudo="Col A,Col B,Col C\nJoao,x,y\n")

    with pytest.raises(RuntimeError, match="menos de 4 colunas"):
        main(config)


def test_main_atualiza_coluna_d_na_planilha(config, mocker):
    _write_csv(config)
    mock_gc = mocker.MagicMock()
    mock_aba = mocker.MagicMock()
    mock_planilha = mocker.MagicMock()
    mock_planilha.worksheet.return_value = mock_aba
    mock_gc.open_by_key.return_value = mock_planilha
    mocker.patch(f"{_PATCH_BASE}.gspread.service_account", return_value=mock_gc)

    main(config)

    mock_planilha.worksheet.assert_called_once_with("Resultados")
    mock_aba.batch_clear.assert_called_once_with(["D:D"])
    mock_aba.update.assert_called_once()


def test_main_levanta_runtime_se_aba_nao_existir(config, mocker):
    import gspread

    _write_csv(config)
    mock_gc = mocker.MagicMock()
    mock_planilha = mocker.MagicMock()
    mock_planilha.worksheet.side_effect = gspread.exceptions.WorksheetNotFound
    mock_gc.open_by_key.return_value = mock_planilha
    mocker.patch(f"{_PATCH_BASE}.gspread.service_account", return_value=mock_gc)

    with pytest.raises(RuntimeError, match="aba"):
        main(config)
