from pathlib import Path

import pytest
import tomli_w

import scripthub.scripts.torpedo.config as cfg_module
from scripthub.scripts.torpedo.config import Config
from scripthub.services.erros import ErroConfiguracao


@pytest.fixture
def settings_valido(tmp_path):
    return {
        "moodle": {
            "usuario": "user",
            "urlLogin": "https://example.com/login",
            "urlsForuns": ["https://example.com/forum1", "https://example.com/forum2"],
            "headless": True,
            "postDelay": 3,
            "caminhoPostFile": str(tmp_path / "post.md"),
        }
    }


def _preparar(tmp_path, monkeypatch, mocker, settings_valido, senha="pass"):
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config" / "settings.toml").write_bytes(tomli_w.dumps(settings_valido).encode())
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path / "config")
    mocker.patch("scripthub.scripts.torpedo.config.keyring_moodle.obter_senha_moodle", return_value=senha)


def test_caminho_post_file_relativo_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["moodle"]["caminhoPostFile"] = "post.md"
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="caminhoPostFile"):
        Config.load()


def test_caminho_imagem_relativo_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["moodle"]["caminhoImagem"] = "teste.png"
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="caminhoImagem"):
        Config.load()


def test_caminho_imagem_absoluto_e_mantido(tmp_path, monkeypatch, mocker, settings_valido):
    absolute_image_path = str(tmp_path / "imagens" / "teste.png")
    settings_valido["moodle"]["caminhoImagem"] = absolute_image_path
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()

    assert config.moodle.caminho_imagem == Path(absolute_image_path)


def test_sem_caminho_imagem_e_none(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()

    assert config.moodle.caminho_imagem is None


def test_load_valido_completo(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()

    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url_login == "https://example.com/login"
    assert len(config.moodle.urls_foruns) == 2
    assert config.moodle.headless is True
    assert config.moodle.post_delay == 3
    assert config.moodle.caminho_post_file == tmp_path / "post.md"


def test_sem_caminho_post_file_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    del settings_valido["moodle"]["caminhoPostFile"]
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="caminhoPostFile"):
        Config.load()


def test_load_sem_credenciais_levanta_excecao(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido, senha=None)

    with pytest.raises(ErroConfiguracao, match="usuario|senha|Moodle"):
        Config.load()


def test_load_sem_settings_levanta_excecao(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path / "config")

    with pytest.raises(ErroConfiguracao):
        Config.load()
