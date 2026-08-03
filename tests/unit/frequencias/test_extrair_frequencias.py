import pytest

from scripthub.scripts.frequencias.extrair_frequencias import extrair_todas_frequencias
from scripthub.services.erros import ErroConfiguracao

_PATCH = "scripthub.scripts.frequencias.extrair_frequencias"


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
