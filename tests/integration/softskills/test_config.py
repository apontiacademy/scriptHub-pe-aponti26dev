import pytest
import tomli_w

import scripthub.scripts.softskills.config as cfg_module
from scripthub.scripts.softskills.config import Config
from scripthub.services.erros import ErroConfiguracao


@pytest.fixture
def settings_valido(tmp_path):
    return {
        "moodle": {
            "usuario": "user",
            "url": "https://moodle.test",
            "bootcampCatId": "136",
            "aprovadosCatId": "140",
        },
        "drive": {
            "folderId": "folder-id-123",
            "credentialsPath": str(tmp_path / "credentials.json"),
        },
        "outputDir": "bootcamps",
        "aprovadosDir": "aprovados",
    }


def _preparar(tmp_path, monkeypatch, mocker, settings_valido, senha="pass"):
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config" / "settings.toml").write_bytes(tomli_w.dumps(settings_valido).encode())
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path / "config")
    monkeypatch.setattr(cfg_module, "_diretorio_dados", lambda: tmp_path / "dados")
    mocker.patch("scripthub.scripts.softskills.config.keyring_moodle.obter_senha_moodle", return_value=senha)


def test_load_valido(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()
    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url == "https://moodle.test"
    assert config.moodle.bootcamp_cat_id == "136"
    assert config.moodle.aprovados_cat_id == "140"
    assert config.drive.folder_id == "folder-id-123"
    assert config.drive.credentials_path == tmp_path / "credentials.json"
    assert config.output_dir == tmp_path / "dados" / "bootcamps"
    assert config.aprovados_dir == tmp_path / "dados" / "aprovados"


def test_load_sem_usuario_levanta_excecao(tmp_path, monkeypatch, mocker, settings_valido):
    del settings_valido["moodle"]["usuario"]
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="usuario"):
        Config.load()


def test_load_sem_senha_no_keyring_levanta_excecao(tmp_path, monkeypatch, mocker, settings_valido):
    _preparar(tmp_path, monkeypatch, mocker, settings_valido, senha=None)

    with pytest.raises(ErroConfiguracao, match="keyring"):
        Config.load()


def test_load_sem_settings_levanta_excecao(tmp_path, monkeypatch):
    monkeypatch.setattr(cfg_module, "_diretorio_config", lambda: tmp_path / "config")

    with pytest.raises(ErroConfiguracao):
        Config.load()


def test_credentials_path_relativo_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["drive"]["credentialsPath"] = "credentials.json"
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="credentialsPath"):
        Config.load()


def test_credentials_path_ausente_levanta_erro_configuracao(tmp_path, monkeypatch, mocker, settings_valido):
    del settings_valido["drive"]["credentialsPath"]
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="credentialsPath"):
        Config.load()


def test_load_com_urlbase_nova_chave(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["moodle"].pop("url")
    settings_valido["moodle"]["urlBase"] = "https://moodle-novo.test"
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()

    assert config.moodle.url == "https://moodle-novo.test"


def test_load_com_urlbase_e_url_prioriza_urlbase(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["moodle"]["url"] = "https://moodle-antigo.test"
    settings_valido["moodle"]["urlBase"] = "https://moodle-novo.test"
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()

    assert config.moodle.url == "https://moodle-novo.test"


def test_load_url_com_trailing_slash_removido(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["moodle"].pop("url")
    settings_valido["moodle"]["urlBase"] = "https://moodle.test/"
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    config = Config.load()

    assert config.moodle.url == "https://moodle.test"


def test_load_sem_urlbase_nem_url_levanta_erro_claro(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["moodle"].pop("url")
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="urlBase"):
        Config.load()


def test_load_sem_bootcamp_cat_id_levanta_erro_claro(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["moodle"].pop("bootcampCatId")
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="bootcampCatId"):
        Config.load()


def test_load_sem_aprovados_cat_id_levanta_erro_claro(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["moodle"].pop("aprovadosCatId")
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="aprovadosCatId"):
        Config.load()


def test_load_sem_folder_id_levanta_erro_claro(tmp_path, monkeypatch, mocker, settings_valido):
    settings_valido["drive"].pop("folderId")
    _preparar(tmp_path, monkeypatch, mocker, settings_valido)

    with pytest.raises(ErroConfiguracao, match="folderId"):
        Config.load()
