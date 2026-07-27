import json

import pytest

import scripthub.scripts.frequencias.extrair.config as cfg_module
from scripthub.scripts.frequencias.extrair.config import Config
from scripthub.services.erros import ErroConfiguracao


@pytest.fixture
def settings_valido(tmp_path):
    return {
        "moodle": {
            "urlLogin": "https://example.com/login",
            "urlsFrequencias": {
                "Turma A": "https://example.com/freq?id=1",
                "Turma B": "https://example.com/freq?id=2",
            },
            "caminhoExportacao": str(tmp_path / "output"),
        },
    }


def test_load_valido(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.setattr(cfg_module, "DIRETORIO_DOMINIO", tmp_path)

    config = Config.load()

    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url_login == "https://example.com/login"
    assert config.moodle.urls_frequencias == {
        "Turma A": "https://example.com/freq?id=1",
        "Turma B": "https://example.com/freq?id=2",
    }
    assert config.moodle.caminho_exportacao == tmp_path / "output"


def test_load_sem_credenciais_levanta_erro_configuracao(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.setattr(cfg_module, "DIRETORIO_DOMINIO", tmp_path)
    monkeypatch.delenv("MOODLE_USUARIO", raising=False)
    monkeypatch.delenv("MOODLE_SENHA", raising=False)

    with pytest.raises(ErroConfiguracao, match="MOODLE_USUARIO"):
        Config.load()


def test_load_sem_settings_levanta_erro_configuracao(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.setattr(cfg_module, "DIRETORIO_DOMINIO", tmp_path)

    with pytest.raises(ErroConfiguracao):
        Config.load()


def test_load_sem_urls_frequencias_levanta_key_error(tmp_path, monkeypatch, settings_valido):
    del settings_valido["moodle"]["urlsFrequencias"]
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.setattr(cfg_module, "DIRETORIO_DOMINIO", tmp_path)

    with pytest.raises(KeyError):
        Config.load()
