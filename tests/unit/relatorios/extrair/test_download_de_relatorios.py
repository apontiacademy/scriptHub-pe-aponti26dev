import pytest

from scripthub.scripts.relatorios.extrair.config import Config, MoodleConfig
from scripthub.scripts.relatorios.extrair.download_de_relatorios import main
from scripthub.services.erros import ErroConfiguracao

_PATCH = "scripthub.scripts.relatorios.extrair.download_de_relatorios"


def _make_config(tmp_path):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            caminho_download_relatorio=tmp_path / "relatorios",
            url_login="https://moodle.example.com/login/index.php",
            urls_relatorios=["https://moodle.example.com/report?id=1"],
        ),
    )


def test_main_levanta_erro_configuracao_sem_urls(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.moodle.urls_relatorios = []
    mocker.patch(f"{_PATCH}.MoodleSessao")

    with pytest.raises(ErroConfiguracao, match="[Uu][Rr][Ll]"):
        main(config)
