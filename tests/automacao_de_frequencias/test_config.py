import json

import pytest

import automacao_de_frequencias.config as cfg_module
from automacao_de_frequencias.config import Config


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
        }
    }


def test_load_valido(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(
        json.dumps(settings_valido), encoding="utf-8"
    )
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


def test_load_sem_credenciais_levanta_excecao(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("")
    (tmp_path / "settings.json").write_text(
        json.dumps(settings_valido), encoding="utf-8"
    )
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.delenv("MOODLE_USUARIO", raising=False)
    monkeypatch.delenv("MOODLE_SENHA", raising=False)

    with pytest.raises(ValueError, match="MOODLE_USUARIO"):
        Config.load()


def test_load_sem_settings_levanta_excecao(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(FileNotFoundError):
        Config.load()
