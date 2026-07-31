import pytest

from scripthub.scripts.frequencias.extrair_frequencias import extrair_todas_frequencias
from scripthub.services.erros import ErroConfiguracao

_PATCH = "scripthub.scripts.frequencias.extrair_frequencias"


def test_cria_diretorio_de_saida(tmp_path, mocker):
    mocker.patch(f"{_PATCH}.MoodleSessao")
    mocker.patch(f"{_PATCH}.extrair_frequencia")

    extrair_todas_frequencias(
        url_login="https://moodle.example.com/login/index.php",
        usuario="user",
        senha="pass",
        urls_frequencias={"Turma A": "https://moodle.example.com/freq?id=1"},
        diretorio_saida=tmp_path / "saida",
    )

    assert (tmp_path / "saida").exists()


def test_levanta_erro_configuracao_sem_urls(tmp_path, mocker):
    mocker.patch(f"{_PATCH}.MoodleSessao")

    with pytest.raises(ErroConfiguracao, match="[Uu][Rr][Ll]"):
        extrair_todas_frequencias(
            url_login="https://moodle.example.com/login/index.php",
            usuario="user",
            senha="pass",
            urls_frequencias={},
            diretorio_saida=tmp_path / "saida",
        )


def test_chama_login_e_extrair_para_cada_turma(tmp_path, mocker):
    mock_sessao_cls = mocker.patch(f"{_PATCH}.MoodleSessao")
    mock_sessao = mock_sessao_cls.return_value
    mock_extrair = mocker.patch(f"{_PATCH}.extrair_frequencia")

    extrair_todas_frequencias(
        url_login="https://moodle.example.com/login/index.php",
        usuario="user",
        senha="pass",
        urls_frequencias={
            "Turma A": "https://moodle.example.com/f1",
            "Turma B": "https://moodle.example.com/f2",
        },
        diretorio_saida=tmp_path / "saida",
    )

    mock_sessao_cls.assert_called_once_with(
        url_login="https://moodle.example.com/login/index.php", usuario="user", senha="pass"
    )
    mock_sessao.login.assert_called_once()
    assert mock_extrair.call_count == 2
