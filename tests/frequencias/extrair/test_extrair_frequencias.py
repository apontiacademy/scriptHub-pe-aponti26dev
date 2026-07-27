import pytest

from scripthub.scripts.frequencias.extrair.config import Config, MoodleConfig
from scripthub.scripts.frequencias.extrair.extrair_frequencias import main
from scripthub.services.erros import ErroConfiguracao

_PATCH = "scripthub.scripts.frequencias.extrair.extrair_frequencias"


def _make_config(tmp_path):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            url_login="https://moodle.example.com/login/index.php",
            urls_frequencias={"Turma A": "https://moodle.example.com/freq?id=1"},
            caminho_exportacao=tmp_path / "exportacao",
        ),
    )


def test_main_cria_diretorio_de_exportacao(tmp_path, mocker):
    config = _make_config(tmp_path)
    mocker.patch(f"{_PATCH}.MoodleSessao")
    mocker.patch(f"{_PATCH}.extrair_frequencia")

    main(config)

    assert config.moodle.caminho_exportacao.exists()


def test_main_levanta_erro_configuracao_sem_urls(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.moodle.urls_frequencias = {}
    mocker.patch(f"{_PATCH}.MoodleSessao")

    with pytest.raises(ErroConfiguracao, match="[Uu][Rr][Ll]"):
        main(config)


def test_main_chama_login_e_extrair_para_cada_turma(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.moodle.urls_frequencias = {
        "Turma A": "https://moodle.example.com/f1",
        "Turma B": "https://moodle.example.com/f2",
    }
    mock_sessao_cls = mocker.patch(f"{_PATCH}.MoodleSessao")
    mock_sessao = mock_sessao_cls.return_value
    mock_extrair = mocker.patch(f"{_PATCH}.extrair_frequencia")

    main(config)

    mock_sessao.login.assert_called_once()
    assert mock_extrair.call_count == 2
