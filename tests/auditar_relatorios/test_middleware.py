from pathlib import Path

import pytest

from scripthub.scripts.auditar_relatorios.config import Config, GsheetsConfig, MoodleConfig
from scripthub.scripts.auditar_relatorios.middleware_analise_de_relatorios import main

_PATCH_CORE = "scripthub.scripts.auditar_relatorios.middleware_analise_de_relatorios.executar_analise_core"


@pytest.fixture
def config(tmp_path):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            caminho_download_relatorio=tmp_path / "relatorios",
            csv_residentes=tmp_path / "residentes.csv",
            csv_saida_analise=tmp_path / "dados" / "resultado.csv",
            url_login="https://example.com/login",
            urls_relatorios=["https://example.com/r1"],
            exportar_analise_relatorio=False,
            caminho_exportacao_analise=None,
        ),
        gsheets=GsheetsConfig(
            id_planilha="planilha-id",
            nome_aba="Aba",
            caminho_backup_local=tmp_path / "backups",
            caminho_json_credenciais=tmp_path / "credentials.json",
        ),
    )


def test_main_injeta_flag_diretorio_relatorios(config, mocker):
    mock_core = mocker.patch(_PATCH_CORE)

    main(config)

    args = mock_core.call_args[0][0]
    assert "-d" in args
    assert str(config.moodle.caminho_download_relatorio) in args


def test_main_injeta_flag_csv_residentes(config, mocker):
    mock_core = mocker.patch(_PATCH_CORE)

    main(config)

    args = mock_core.call_args[0][0]
    assert "-p" in args
    assert str(config.moodle.csv_residentes) in args


def test_main_injeta_modo_feitos(config, mocker):
    mock_core = mocker.patch(_PATCH_CORE)

    main(config)

    args = mock_core.call_args[0][0]
    assert "-m" in args
    assert "feitos" in args


def test_main_injeta_flag_csv_saida(config, mocker):
    mock_core = mocker.patch(_PATCH_CORE)

    main(config)

    args = mock_core.call_args[0][0]
    assert "-o" in args
    assert str(config.moodle.csv_saida_analise) in args


def test_main_cria_diretorio_pai_do_csv_saida(config, mocker):
    mocker.patch(_PATCH_CORE)
    assert not config.moodle.csv_saida_analise.parent.exists()

    main(config)

    assert config.moodle.csv_saida_analise.parent.exists()


def test_main_nao_propaga_excecao_do_core(config, mocker):
    mocker.patch(_PATCH_CORE, side_effect=RuntimeError("falha no core"))

    # O código atual captura a exceção e faz log.erro — não deve propagar
    main(config)
