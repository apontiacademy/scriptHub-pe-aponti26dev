from scripthub.scripts.frequencias.auditar.config import Config, GsheetsConfig, MoodleConfig
from scripthub.scripts.frequencias.auditar.extrair_frequencias import main

_PATCH = "scripthub.scripts.frequencias.auditar.extrair_frequencias"


def _make_config(tmp_path):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            url_login="https://moodle.example.com/login/index.php",
            urls_frequencias={"Turma A": "https://moodle.example.com/freq?id=1"},
        ),
        gsheets=GsheetsConfig(
            id_planilha="planilha-id",
            caminho_json_credenciais=tmp_path / "creds.json",
        ),
        diretorio_download=tmp_path / "cache" / "frequencias",
    )


def test_main_delega_para_extrair_todas_frequencias_com_diretorio_download(tmp_path, mocker):
    config = _make_config(tmp_path)
    mock_extrair_todas = mocker.patch(f"{_PATCH}.extrair_todas_frequencias")

    main(config)

    mock_extrair_todas.assert_called_once_with(
        url_login=config.moodle.url_login,
        usuario=config.moodle.usuario,
        senha=config.moodle.senha,
        urls_frequencias=config.moodle.urls_frequencias,
        diretorio_saida=config.diretorio_download,
    )
