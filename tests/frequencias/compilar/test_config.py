import pytest
import tomli_w

import scripthub.scripts.frequencias.compilar.config as cfg_module
from scripthub.scripts.frequencias.compilar.config import Config
from scripthub.services.erros import ErroConfiguracao


@pytest.fixture
def settings_valido(tmp_path):
    return {
        "moodle": {
            "usuario": "user",
            "urlLogin": "https://example.com/login",
            "urlsFrequencias": {
                "Turma A": "https://example.com/freq?id=1",
                "Turma B": "https://example.com/freq?id=2",
            },
        },
        "atas": {
            "caminhoSaida": str(tmp_path / "atas"),
        },
    }


def _preparar(tmp_path, monkeypatch, mocker, settings_valido, senha="pass"):
    (tmp_path / "settings.toml").write_bytes(tomli_w.dumps(settings_valido).encode())
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path)
    monkeypatch.setattr(cfg_module, "_diretorio_cache", lambda: tmp_path / "cache")
    mocker.patch("scripthub.scripts.frequencias.compilar.config.keyring_moodle.obter_senha_moodle", return_value=senha)


def test_load_valido(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()

    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url_login == "https://example.com/login"
    assert config.moodle.urls_frequencias == {
        "Turma A": "https://example.com/freq?id=1",
        "Turma B": "https://example.com/freq?id=2",
    }
    assert config.atas.caminho_saida == tmp_path / "atas"
    assert config.atas.caminho_logo is None
    assert config.atas.caminho_assinatura is None
    assert config.diretorio_download == tmp_path / "cache" / "frequencias"


def test_load_com_logo_e_assinatura_opcionais(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["atas"]["caminhoLogo"] = str(tmp_path / "logo.png")
    settings_valido["atas"]["caminhoAssinatura"] = str(tmp_path / "assinatura.png")
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()

    assert config.atas.caminho_logo == tmp_path / "logo.png"
    assert config.atas.caminho_assinatura == tmp_path / "assinatura.png"


def test_load_sem_caminho_saida_levanta_key_error(tmp_path, monkeypatch, mocker, settings_valido):
    del settings_valido["atas"]["caminhoSaida"]
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(KeyError):
        Config.load()


def test_load_caminho_saida_relativo_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["atas"]["caminhoSaida"] = "atas"
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="caminhoSaida"):
        Config.load()


def test_load_caminho_logo_relativo_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["atas"]["caminhoLogo"] = "logo.png"
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="caminhoLogo"):
        Config.load()


def test_load_caminho_assinatura_relativo_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["atas"]["caminhoAssinatura"] = "assinatura.png"
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="caminhoAssinatura"):
        Config.load()


def test_load_sem_senha_no_keyring_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido, senha=None)

    with pytest.raises(ErroConfiguracao, match="usuario"):
        Config.load()


def test_load_sem_settings_levanta_erro_configuracao(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path)

    with pytest.raises(ErroConfiguracao):
        Config.load()
