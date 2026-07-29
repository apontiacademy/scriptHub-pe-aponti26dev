import pytest
import tomli_w

import scripthub.scripts.frequencias.extrair.config as cfg_module
from scripthub.scripts.frequencias.extrair.config import Config
from scripthub.services.erros import ErroConfiguracao


def _settings_valido(tmp_path, usuario="user"):
    return {
        "moodle": {
            "usuario": usuario,
            "urlLogin": "https://example.com/login",
            "urlsFrequencias": {
                "Turma A": "https://example.com/freq?id=1",
                "Turma B": "https://example.com/freq?id=2",
            },
            "caminhoExportacao": str(tmp_path / "output"),
        },
    }


def test_load_valido(tmp_path, monkeypatch, mocker):
    (tmp_path / "settings.toml").write_bytes(tomli_w.dumps(_settings_valido(tmp_path)).encode())
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path)
    mocker.patch("scripthub.scripts.frequencias.extrair.config.keyring_moodle.obter_senha_moodle", return_value="pass")

    config = Config.load()

    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url_login == "https://example.com/login"
    assert config.moodle.urls_frequencias == {
        "Turma A": "https://example.com/freq?id=1",
        "Turma B": "https://example.com/freq?id=2",
    }
    assert config.moodle.caminho_exportacao == tmp_path / "output"


def test_load_sem_senha_no_keyring_levanta_erro_configuracao(tmp_path, monkeypatch, mocker):
    (tmp_path / "settings.toml").write_bytes(tomli_w.dumps(_settings_valido(tmp_path)).encode())
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path)
    mocker.patch("scripthub.scripts.frequencias.extrair.config.keyring_moodle.obter_senha_moodle", return_value=None)

    with pytest.raises(ErroConfiguracao, match="usuario"):
        Config.load()


def test_load_sem_usuario_em_settings_levanta_erro_configuracao(tmp_path, monkeypatch, mocker):
    dados = _settings_valido(tmp_path)
    del dados["moodle"]["usuario"]
    (tmp_path / "settings.toml").write_bytes(tomli_w.dumps(dados).encode())
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path)
    mocker.patch("scripthub.scripts.frequencias.extrair.config.keyring_moodle.obter_senha_moodle", return_value="pass")

    with pytest.raises(ErroConfiguracao, match="usuario"):
        Config.load()


def test_load_sem_settings_levanta_erro_configuracao(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path)

    with pytest.raises(ErroConfiguracao):
        Config.load()


def test_load_sem_urls_frequencias_levanta_key_error(tmp_path, monkeypatch, mocker):
    dados = _settings_valido(tmp_path)
    del dados["moodle"]["urlsFrequencias"]
    (tmp_path / "settings.toml").write_bytes(tomli_w.dumps(dados).encode())
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path)
    mocker.patch("scripthub.scripts.frequencias.extrair.config.keyring_moodle.obter_senha_moodle", return_value="pass")

    with pytest.raises(KeyError):
        Config.load()
