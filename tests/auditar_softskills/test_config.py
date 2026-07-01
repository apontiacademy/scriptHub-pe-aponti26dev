import json

import pytest

import scripthub.scripts.auditar_softskills.config as cfg_module
from scripthub.scripts.auditar_softskills.config import Config


@pytest.fixture
def settings_valido(tmp_path):
    return {
        "moodle": {
            "url": "https://moodle.test",
            "bootcampCatId": "136",
            "aprovadosCatId": "140",
        },
        "drive": {
            "folderId": "folder-id-123",
            "credentialsPath": "credentials.json",
        },
        "outputDir": "bootcamps",
        "aprovadosDir": "aprovados",
    }


def test_load_valido(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()
    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url == "https://moodle.test"
    assert config.moodle.bootcamp_cat_id == "136"
    assert config.moodle.aprovados_cat_id == "140"
    assert config.drive.folder_id == "folder-id-123"
    assert config.output_dir == tmp_path / "bootcamps"
    assert config.aprovados_dir == tmp_path / "aprovados"


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


def test_credentials_path_relativo_resolve_para_diretorio_base(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()
    assert config.drive.credentials_path == (tmp_path / "credentials.json").resolve()


def test_load_com_urlbase_nova_chave(tmp_path, monkeypatch, settings_valido):
    settings_valido["moodle"].pop("url")
    settings_valido["moodle"]["urlBase"] = "https://moodle-novo.test"
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    assert config.moodle.url == "https://moodle-novo.test"


def test_load_com_urlbase_e_url_prioriza_urlbase(tmp_path, monkeypatch, settings_valido):
    settings_valido["moodle"]["url"] = "https://moodle-antigo.test"
    settings_valido["moodle"]["urlBase"] = "https://moodle-novo.test"
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    assert config.moodle.url == "https://moodle-novo.test"


def test_load_url_com_trailing_slash_removido(tmp_path, monkeypatch, settings_valido):
    settings_valido["moodle"].pop("url")
    settings_valido["moodle"]["urlBase"] = "https://moodle.test/"
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    assert config.moodle.url == "https://moodle.test"


def test_load_sem_urlbase_nem_url_levanta_erro_claro(tmp_path, monkeypatch, settings_valido):
    settings_valido["moodle"].pop("url")
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(RuntimeError, match="urlBase"):
        Config.load()


def test_load_sem_bootcamp_cat_id_levanta_erro_claro(tmp_path, monkeypatch, settings_valido):
    settings_valido["moodle"].pop("bootcampCatId")
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(RuntimeError, match="bootcampCatId"):
        Config.load()


def test_load_sem_aprovados_cat_id_levanta_erro_claro(tmp_path, monkeypatch, settings_valido):
    settings_valido["moodle"].pop("aprovadosCatId")
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(RuntimeError, match="aprovadosCatId"):
        Config.load()


def test_load_sem_folder_id_levanta_erro_claro(tmp_path, monkeypatch, settings_valido):
    settings_valido["drive"].pop("folderId")
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(RuntimeError, match="folderId"):
        Config.load()
