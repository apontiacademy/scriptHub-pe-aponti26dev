import pytest
import tomli_w

import scripthub.scripts.frequencias.auditar.config as cfg_module
from scripthub.scripts.frequencias.auditar.config import Config
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
            "caminhoExportacao": str(tmp_path / "output"),
        },
        "gsheets": {
            "idPlanilha": "planilha-id-123",
            "caminhoJsonCredenciais": str(tmp_path / "credentials.json"),
        },
    }


def _preparar(tmp_path, monkeypatch, mocker, settings_valido, senha="pass"):
    (tmp_path / "settings.toml").write_bytes(tomli_w.dumps(settings_valido).encode())
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path)
    mocker.patch("scripthub.scripts.frequencias.auditar.config.keyring_moodle.obter_senha_moodle", return_value=senha)


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
    assert config.moodle.caminho_exportacao == tmp_path / "output"
    assert config.gsheets.caminho_json_credenciais == tmp_path / "credentials.json"


def test_load_sem_caminho_json_credenciais_levanta_key_error(tmp_path, monkeypatch, mocker, settings_valido):
    del settings_valido["gsheets"]["caminhoJsonCredenciais"]
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(KeyError):
        Config.load()


def test_load_caminho_json_credenciais_relativo_levanta_erro_configuracao(
    tmp_path, monkeypatch, mocker, settings_valido
):
    settings_valido["gsheets"]["caminhoJsonCredenciais"] = "credentials.json"
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="caminhoJsonCredenciais"):
        Config.load()


def test_load_caminho_exportacao_relativo_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["moodle"]["caminhoExportacao"] = "output"
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="caminhoExportacao"):
        Config.load()


def test_load_sem_senha_no_keyring_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido, senha=None)

    with pytest.raises(ErroConfiguracao, match="usuario"):
        Config.load()


def test_load_sem_usuario_em_settings_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    del settings_valido["moodle"]["usuario"]
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="usuario"):
        Config.load()


def test_load_sem_settings_levanta_excecao(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path)

    with pytest.raises(ErroConfiguracao):
        Config.load()
