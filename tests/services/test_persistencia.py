import tomllib

import pytest
import tomli_w

import scripthub.services.config.persistencia as persistencia_module
from scripthub.services.config.campo import Campo
from scripthub.services.config.persistencia import carregar_valores, persistir


def _campo_keyring(chave):
    return Campo(chave=chave, rotulo="r", tipo="senha", origem="keyring")


def _campo_settings(chave, *json_chaves, obrigatorio=True):
    return Campo(
        chave=chave,
        rotulo="r",
        tipo="texto",
        origem="settings",
        json_chaves=list(json_chaves),
        obrigatorio=obrigatorio,
    )


def _script_dir(tmp_path, nome):
    d = tmp_path / nome
    d.mkdir(exist_ok=True)
    return d


@pytest.fixture(autouse=True)
def scripts_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia_module, "_script_dir", lambda nome_script: _script_dir(tmp_path, nome_script))
    return tmp_path


@pytest.fixture(autouse=True)
def keyring_fake(mocker):
    armazem: dict[str, str] = {}

    def _get(nome_dominio):
        return armazem.get(nome_dominio)

    def _set(nome_dominio, senha):
        armazem[nome_dominio] = senha

    mocker.patch("scripthub.services.config.persistencia.keyring_moodle.obter_senha_moodle", side_effect=_get)
    mocker.patch("scripthub.services.config.persistencia.keyring_moodle.definir_senha_moodle", side_effect=_set)
    return armazem


# ── carregar_valores ──────────────────────────────────────────────────────────


def test_carregar_valores_le_senha_do_keyring(tmp_path, keyring_fake):
    keyring_fake["meu_script"] = "minhasenha"
    campo = _campo_keyring("senha")

    resultado = carregar_valores("meu_script", [campo])

    assert resultado["senha"] == "minhasenha"


def test_carregar_valores_le_valor_settings_aninhado(tmp_path):
    d = _script_dir(tmp_path, "meu_script")
    (d / "settings.toml").write_bytes(tomli_w.dumps({"moodle": {"urlLogin": "https://x.com"}}).encode())
    campo = _campo_settings("url_login", "moodle", "urlLogin")

    resultado = carregar_valores("meu_script", [campo])

    assert resultado["url_login"] == "https://x.com"


def test_carregar_valores_campo_ausente_retorna_none(tmp_path):
    d = _script_dir(tmp_path, "meu_script")
    (d / "settings.toml").write_bytes(tomli_w.dumps({}).encode())
    campo = _campo_settings("url_login", "moodle", "urlLogin")

    resultado = carregar_valores("meu_script", [campo])

    assert resultado["url_login"] is None


def test_carregar_valores_sem_arquivos_retorna_nones(tmp_path):
    _script_dir(tmp_path, "meu_script")
    campos = [_campo_keyring("senha"), _campo_settings("url", "moodle", "url")]

    resultado = carregar_valores("meu_script", campos)

    assert resultado["senha"] is None
    assert resultado["url"] is None


# ── persistir ─────────────────────────────────────────────────────────────────


def test_persistir_campo_keyring_grava_no_keyring(tmp_path, keyring_fake):
    campo = _campo_keyring("senha")

    persistir("meu_script", [campo], {"senha": "novasenha"})

    assert keyring_fake["meu_script"] == "novasenha"
    assert not (tmp_path / "meu_script" / "settings.toml").exists()


def test_persistir_campo_settings_cria_toml_correto(tmp_path):
    _script_dir(tmp_path, "meu_script")
    campo = _campo_settings("url", "moodle", "urlLogin")

    persistir("meu_script", [campo], {"url": "https://novo.com"})

    settings_path = tmp_path / "meu_script" / "settings.toml"
    dados = tomllib.loads(settings_path.read_text(encoding="utf-8"))
    assert dados["moodle"]["urlLogin"] == "https://novo.com"


def test_persistir_settings_faz_merge_com_toml_existente(tmp_path):
    d = _script_dir(tmp_path, "meu_script")
    (d / "settings.toml").write_bytes(tomli_w.dumps({"outros": "dados", "moodle": {"url": "antiga"}}).encode())
    campo = _campo_settings("nome_aba", "gsheets", "nomeAba")

    persistir("meu_script", [campo], {"nome_aba": "Nova Aba"})

    dados = tomllib.loads((d / "settings.toml").read_text(encoding="utf-8"))
    assert dados["outros"] == "dados"
    assert dados["gsheets"]["nomeAba"] == "Nova Aba"


def test_persistir_settings_aninhado_dois_niveis(tmp_path):
    _script_dir(tmp_path, "meu_script")
    campo = _campo_settings("headless", "moodle", "headless")
    campo.tipo = "bool"

    persistir("meu_script", [campo], {"headless": True})

    dados = tomllib.loads((tmp_path / "meu_script" / "settings.toml").read_text(encoding="utf-8"))
    assert dados["moodle"]["headless"] is True


def test_persistir_valor_none_nao_escreve_campo_opcional(tmp_path):
    _script_dir(tmp_path, "meu_script")
    campo = _campo_settings("url", "moodle", "url", obrigatorio=False)

    persistir("meu_script", [campo], {"url": None})

    settings_path = tmp_path / "meu_script" / "settings.toml"
    if settings_path.exists():
        dados = tomllib.loads(settings_path.read_text(encoding="utf-8"))
        assert dados.get("moodle", {}).get("url") is None


def test_persistir_valor_none_remove_chave_opcional_existente(tmp_path):
    d = _script_dir(tmp_path, "meu_script")
    (d / "settings.toml").write_bytes(
        tomli_w.dumps({"moodle": {"url": "https://antiga.com", "outraChave": "mantida"}}).encode()
    )
    campo = _campo_settings("url", "moodle", "url", obrigatorio=False)

    persistir("meu_script", [campo], {"url": None})

    dados = tomllib.loads((d / "settings.toml").read_text(encoding="utf-8"))
    assert "url" not in dados["moodle"]
    assert dados["moodle"]["outraChave"] == "mantida"


def test_persistir_valor_none_com_json_chaves_vazio_nao_gera_indexerror(tmp_path):
    _script_dir(tmp_path, "meu_script")
    campo = _campo_settings("campo_sem_caminho", obrigatorio=False)

    persistir("meu_script", [campo], {"campo_sem_caminho": None})


def test_persistir_ignora_valor_none_de_campo_keyring(tmp_path, keyring_fake):
    campo = _campo_keyring("senha")

    persistir("meu_script", [campo], {"senha": None})

    assert "meu_script" not in keyring_fake
