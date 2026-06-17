import json
from pathlib import Path

import pytest

import automacao_de_forum.config as cfg_module
from automacao_de_forum.config import Config


@pytest.fixture
def settings_valido(tmp_path):
    """Fixture com settings válidos para automacao_de_forum."""
    return {
        "moodle": {
            "urlLogin": "https://example.com/login",
            "urlsForuns": ["https://example.com/forum1", "https://example.com/forum2"],
            "headless": True,
            "postDelay": 3,
            "caminhoPostFile": "post.md",
            "caminhoImagem": None,
        }
    }


def test_caminho_imagem_relativo(tmp_path, monkeypatch, settings_valido):
    """Testa que caminhos relativos de imagem são resolvidos corretamente para DIRETORIO_BASE."""
    # Configura settings com caminho relativo
    settings_valido["moodle"]["caminhoImagem"] = "teste.png"
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    # Verifica se o caminho foi resolvido corretamente para DIRETORIO_BASE/teste.png
    expected_path = tmp_path / "teste.png"
    assert config.moodle.caminho_imagem == expected_path
    assert str(config.moodle.caminho_imagem).endswith("teste.png")


def test_caminho_imagem_absoluto(tmp_path, monkeypatch, settings_valido):
    """Testa que caminhos absolutos de imagem são mantidos corretamente."""
    # Configura settings com caminho absoluto
    absolute_image_path = str(tmp_path / "imagens" / "teste.png")
    settings_valido["moodle"]["caminhoImagem"] = absolute_image_path
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    # Verifica se o caminho absoluto foi mantido corretamente
    assert config.moodle.caminho_imagem == Path(absolute_image_path)


def test_sem_caminho_imagem(tmp_path, monkeypatch, settings_valido):
    """Testa que a ausência de caminho de imagem resulta em None."""
    # Configura settings sem caminho de imagem
    settings_valido["moodle"]["caminhoImagem"] = None
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    # Verifica se caminho_imagem é None
    assert config.moodle.caminho_imagem is None


def test_load_valido_completo(tmp_path, monkeypatch, settings_valido):
    """Testa o carregamento completo de configurações válidas."""
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    # Verifica todos os campos básicos
    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url_login == "https://example.com/login"
    assert len(config.moodle.urls_foruns) == 2
    assert config.moodle.headless is True
    assert config.moodle.post_delay == 3
    assert config.moodle.caminho_post_file == tmp_path / "post.md"


def test_load_sem_credenciais_levanta_excecao(tmp_path, monkeypatch, settings_valido):
    """Testa que a falta de credenciais levanta ValueError."""
    (tmp_path / ".env").write_text("")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.delenv("MOODLE_USUARIO", raising=False)
    monkeypatch.delenv("MOODLE_SENHA", raising=False)

    with pytest.raises(ValueError, match="MOODLE_USUARIO"):
        Config.load()


def test_load_sem_settings_levanta_excecao(tmp_path, monkeypatch):
    """Testa que a falta de settings.json levanta FileNotFoundError."""
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(FileNotFoundError):
        Config.load()
