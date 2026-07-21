import json

import pytest

import scripthub.scripts.auditar_frequencias.config as cfg_module
from scripthub.scripts.auditar_frequencias.config import Config
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
        "gsheets": {
            "idPlanilha": "planilha-id-123",
            "caminhoJsonCredenciais": str(tmp_path / "credentials.json"),
        },
    }


def test_load_valido(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url_login == "https://example.com/login"
    assert config.moodle.urls_frequencias == {
        "Turma A": "https://example.com/freq?id=1",
        "Turma B": "https://example.com/freq?id=2",
    }
    assert config.moodle.caminho_exportacao == tmp_path / "output"
    assert config.gsheets.caminho_json_credenciais == tmp_path / "credentials.json"


def test_load_sem_caminho_json_credenciais_levanta_key_error(tmp_path, monkeypatch, settings_valido):
    del settings_valido["gsheets"]["caminhoJsonCredenciais"]
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(KeyError):
        Config.load()


def test_load_caminho_json_credenciais_relativo_levanta_erro_configuracao(tmp_path, monkeypatch, settings_valido):
    settings_valido["gsheets"]["caminhoJsonCredenciais"] = "credentials.json"
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(ErroConfiguracao, match="caminhoJsonCredenciais"):
        Config.load()


def test_load_sem_credenciais_levanta_excecao(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.delenv("MOODLE_USUARIO", raising=False)
    monkeypatch.delenv("MOODLE_SENHA", raising=False)

    with pytest.raises(ErroConfiguracao, match="MOODLE_USUARIO"):
        Config.load()


def test_load_sem_settings_levanta_excecao(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(ErroConfiguracao):
        Config.load()
