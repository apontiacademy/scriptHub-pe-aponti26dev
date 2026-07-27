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


def test_main_chama_login_e_baixar_para_cada_url(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.moodle.urls_relatorios = [
        "https://moodle.example.com/r1",
        "https://moodle.example.com/r2",
    ]
    mock_sessao_cls = mocker.patch(f"{_PATCH}.MoodleSessao")
    mock_sessao = mock_sessao_cls.return_value
    mock_baixar = mocker.patch(f"{_PATCH}.baixar_relatorio")

    main(config)

    mock_sessao.login.assert_called_once()
    assert mock_baixar.call_count == 2


def test_main_cria_diretorio_de_download(tmp_path, mocker):
    config = _make_config(tmp_path)
    mocker.patch(f"{_PATCH}.MoodleSessao")
    mocker.patch(f"{_PATCH}.baixar_relatorio")

    main(config)

    assert config.moodle.caminho_download_relatorio.exists()
