import json

import pytest

import scripthub.scripts.compilacao_de_relatorios.config as cfg_module
from scripthub.scripts.compilacao_de_relatorios.config import Config


@pytest.fixture
def settings_valido(tmp_path):
    return {
        "moodle": {
            "urlLogin": "https://example.com/login",
            "meses": {
                "Janeiro": ["https://example.com/semana1", "https://example.com/semana2"],
                "Fevereiro": ["https://example.com/semana3"],
            },
        },
        "pdf": {
            "caminhoSaida": str(tmp_path / "pdfs"),
            "csvResidentes": str(tmp_path / "residentes.csv"),
        },
    }


def test_load_retorna_config_completa(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url_login == "https://example.com/login"
    assert "Janeiro" in config.moodle.meses
    assert len(config.moodle.meses["Janeiro"]) == 2
    assert config.pdf.caminho_saida == tmp_path / "pdfs"
    assert config.pdf.csv_residentes == tmp_path / "residentes.csv"


def test_load_sem_credenciais_levanta_value_error(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.delenv("MOODLE_USUARIO", raising=False)
    monkeypatch.delenv("MOODLE_SENHA", raising=False)

    with pytest.raises(ValueError, match="MOODLE_USUARIO"):
        Config.load()


def test_load_sem_settings_levanta_file_not_found(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(FileNotFoundError):
        Config.load()


def test_meses_normaliza_urls_com_strip(tmp_path, monkeypatch, settings_valido):
    settings_valido["moodle"]["meses"] = {"Jan": ["  https://example.com/s1  ", "https://example.com/s2"]}
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    assert config.moodle.meses["Jan"][0] == "https://example.com/s1"
