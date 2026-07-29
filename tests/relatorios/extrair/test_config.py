import pytest
import tomli_w

import scripthub.scripts.relatorios.extrair.config as cfg_module
from scripthub.scripts.relatorios.extrair.config import Config
from scripthub.services.erros import ErroConfiguracao


@pytest.fixture
def settings_valido(tmp_path):
    return {
        "moodle": {
            "usuario": "user",
            "urlLogin": "https://example.com/login",
            "urlsRelatorios": [
                "https://example.com/relatorio1",
                "https://example.com/relatorio2",
            ],
            "caminhoDownloadRelatorio": str(tmp_path / "downloads"),
        },
    }


def _preparar(tmp_path, monkeypatch, mocker, settings_valido, senha="pass"):
    (tmp_path / "settings.toml").write_bytes(tomli_w.dumps(settings_valido).encode())
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path)
    mocker.patch("scripthub.scripts.relatorios.extrair.config.keyring_moodle.obter_senha_moodle", return_value=senha)


def test_load_retorna_config_completa(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()

    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url_login == "https://example.com/login"
    assert config.moodle.urls_relatorios == [
        "https://example.com/relatorio1",
        "https://example.com/relatorio2",
    ]
    assert config.moodle.caminho_download_relatorio == tmp_path / "downloads"


def test_load_sem_usuario_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    del settings_valido["moodle"]["usuario"]
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="usuario"):
        Config.load()


def test_load_sem_senha_no_keyring_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido, senha=None)

    with pytest.raises(ErroConfiguracao, match="usuario"):
        Config.load()


def test_load_sem_settings_levanta_erro_configuracao(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path)

    with pytest.raises(ErroConfiguracao):
        Config.load()


def test_load_sem_urls_relatorios_levanta_key_error(tmp_path, monkeypatch, mocker, settings_valido):
    del settings_valido["moodle"]["urlsRelatorios"]
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(KeyError):
        Config.load()


def test_load_sem_caminho_download_relatorio_levanta_key_error(tmp_path, monkeypatch, mocker, settings_valido):
    del settings_valido["moodle"]["caminhoDownloadRelatorio"]
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(KeyError):
        Config.load()
