import json

import pytest

import scripthub.scripts.relatorios.extrair.config as cfg_module
from scripthub.scripts.relatorios.extrair.config import Config
from scripthub.services.erros import ErroConfiguracao


@pytest.fixture
def settings_valido(tmp_path):
    return {
        "moodle": {
            "urlLogin": "https://example.com/login",
            "urlsRelatorios": [
                "https://example.com/relatorio1",
                "https://example.com/relatorio2",
            ],
        },
    }


def test_load_retorna_config_completa(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.setattr(cfg_module, "DIRETORIO_DOMINIO", tmp_path)

    config = Config.load()

    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url_login == "https://example.com/login"
    assert config.moodle.urls_relatorios == [
        "https://example.com/relatorio1",
        "https://example.com/relatorio2",
    ]
    assert config.moodle.caminho_download_relatorio == tmp_path / "dados" / "relatorios"


def test_load_sem_usuario_levanta_erro_configuracao(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.setattr(cfg_module, "DIRETORIO_DOMINIO", tmp_path)
    monkeypatch.delenv("MOODLE_USUARIO", raising=False)

    with pytest.raises(ErroConfiguracao, match="MOODLE_USUARIO"):
        Config.load()


def test_load_sem_senha_levanta_erro_configuracao(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.setattr(cfg_module, "DIRETORIO_DOMINIO", tmp_path)
    monkeypatch.delenv("MOODLE_SENHA", raising=False)

    with pytest.raises(ErroConfiguracao, match="MOODLE_SENHA"):
        Config.load()


def test_load_sem_settings_levanta_erro_configuracao(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.setattr(cfg_module, "DIRETORIO_DOMINIO", tmp_path)

    with pytest.raises(ErroConfiguracao):
        Config.load()


def test_load_sem_urls_relatorios_levanta_key_error(tmp_path, monkeypatch, settings_valido):
    del settings_valido["moodle"]["urlsRelatorios"]
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.setattr(cfg_module, "DIRETORIO_DOMINIO", tmp_path)

    with pytest.raises(KeyError):
        Config.load()
