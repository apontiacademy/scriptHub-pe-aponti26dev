import json

import pytest

import automacao_de_notas.config as cfg_module
from automacao_de_notas.config import Config


@pytest.fixture
def settings_valido(tmp_path):
    return {
        "moodle": {
            "url": "https://moodle.test",
            "urlLogin": "https://moodle.test/login/index.php",
            "urlTurmas": "https://moodle.test/course/index.php",
            "headless": True,
        },
        "drive": {
            "folderId": "folder-id-123",
            "credentialsPath": "credentials.json",
        },
        "outputDir": "dados",
    }


def test_load_valido(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()
    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url == "https://moodle.test"
    assert config.moodle.url_login == "https://moodle.test/login/index.php"
    assert config.moodle.url_turmas == "https://moodle.test/course/index.php"
    assert config.moodle.headless is True
    assert config.drive.folder_id == "folder-id-123"
    assert config.output_dir == tmp_path / "dados"


def test_load_sem_usuario_levanta_excecao(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.delenv("MOODLE_USUARIO", raising=False)

    with pytest.raises(ValueError, match="MOODLE_USUARIO"):
        Config.load()


def test_load_sem_senha_levanta_excecao(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.delenv("MOODLE_SENHA", raising=False)

    with pytest.raises(ValueError, match="MOODLE_SENHA"):
        Config.load()


def test_load_sem_settings_levanta_excecao(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(FileNotFoundError):
        Config.load()


def test_credentials_path_relativo_resolve_para_parent(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()
    assert config.drive.credentials_path == (tmp_path.parent / "credentials.json").resolve()


def test_headless_padrao_true(tmp_path, monkeypatch, settings_valido):
    del settings_valido["moodle"]["headless"]
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()
    assert config.moodle.headless is True
