import pytest
import tomli_w

import scripthub.scripts.relatorios.compilar.config as cfg_module
from scripthub.scripts.relatorios.compilar.config import Config
from scripthub.services.erros import ErroConfiguracao


@pytest.fixture
def settings_valido(tmp_path):
    return {
        "moodle": {
            "usuario": "user",
            "urlLogin": "https://example.com/login",
            "meses": {
                "Janeiro": ["https://example.com/semana1", "https://example.com/semana2"],
                "Fevereiro": ["https://example.com/semana3"],
            },
        },
        "pdf": {
            "caminhoSaida": str(tmp_path / "pdfs"),
        },
    }


def _preparar(tmp_path, monkeypatch, mocker, settings_valido, senha="pass"):
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config" / "settings.toml").write_bytes(tomli_w.dumps(settings_valido).encode())
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path / "config")
    monkeypatch.setattr(cfg_module, "_diretorio_cache", lambda: tmp_path / "cache" / "compilar")
    mocker.patch("scripthub.scripts.relatorios.compilar.config.keyring_moodle.obter_senha_moodle", return_value=senha)


def test_load_retorna_config_completa(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()

    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url_login == "https://example.com/login"
    assert "Janeiro" in config.moodle.meses
    assert len(config.moodle.meses["Janeiro"]) == 2
    assert config.pdf.caminho_saida == tmp_path / "pdfs"


def test_load_caminho_download_e_relativo_ao_diretorio_de_cache(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()

    assert config.moodle.caminho_download == tmp_path / "cache" / "compilar"


def test_load_sem_senha_no_keyring_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido, senha=None)

    with pytest.raises(ErroConfiguracao, match="usuario"):
        Config.load()


def test_load_caminho_saida_relativo_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["pdf"]["caminhoSaida"] = "pdfs"
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="caminhoSaida"):
        Config.load()


def test_load_sem_settings_levanta_erro_configuracao(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path / "config")

    with pytest.raises(ErroConfiguracao):
        Config.load()


def test_meses_normaliza_urls_com_strip(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["moodle"]["meses"] = {"Jan": ["  https://example.com/s1  ", "https://example.com/s2"]}
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()

    assert config.moodle.meses["Jan"][0] == "https://example.com/s1"
