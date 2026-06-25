import json

import pytest

import scripthub.services.config.persistencia as persistencia_module
from scripthub.services.config.campo import Campo
from scripthub.services.config.persistencia import carregar_valores, persistir


@pytest.fixture(autouse=True)
def scripts_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(persistencia_module, "_SCRIPTS_FOLDER", tmp_path)
    return tmp_path


def _campo_env(chave, env_var):
    return Campo(chave=chave, rotulo="r", tipo="texto", origem="env", env_var=env_var, json_chaves=[])


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


# ── carregar_valores ──────────────────────────────────────────────────────────


def test_carregar_valores_le_variavel_de_env(tmp_path):
    d = _script_dir(tmp_path, "meu_script")
    (d / ".env").write_text("MOODLE_USUARIO=testuser\n")
    campo = _campo_env("usuario", "MOODLE_USUARIO")

    resultado = carregar_valores("meu_script", [campo])

    assert resultado["usuario"] == "testuser"


def test_carregar_valores_le_valor_settings_aninhado(tmp_path):
    d = _script_dir(tmp_path, "meu_script")
    (d / "settings.json").write_text(json.dumps({"moodle": {"urlLogin": "https://x.com"}}), encoding="utf-8")
    campo = _campo_settings("url_login", "moodle", "urlLogin")

    resultado = carregar_valores("meu_script", [campo])

    assert resultado["url_login"] == "https://x.com"


def test_carregar_valores_campo_ausente_retorna_none(tmp_path):
    d = _script_dir(tmp_path, "meu_script")
    (d / "settings.json").write_text(json.dumps({}), encoding="utf-8")
    campo = _campo_settings("url_login", "moodle", "urlLogin")

    resultado = carregar_valores("meu_script", [campo])

    assert resultado["url_login"] is None


def test_carregar_valores_sem_arquivos_retorna_nones(tmp_path):
    _script_dir(tmp_path, "meu_script")
    campos = [_campo_env("usuario", "MOODLE_USUARIO"), _campo_settings("url", "moodle", "url")]

    resultado = carregar_valores("meu_script", campos)

    assert resultado["usuario"] is None
    assert resultado["url"] is None


def test_carregar_valores_env_vazio_retorna_none(tmp_path):
    d = _script_dir(tmp_path, "meu_script")
    (d / ".env").write_text("MOODLE_USUARIO=\n")
    campo = _campo_env("usuario", "MOODLE_USUARIO")

    resultado = carregar_valores("meu_script", [campo])

    assert resultado["usuario"] is None


# ── persistir ─────────────────────────────────────────────────────────────────


def test_persistir_campo_env_cria_arquivo_env(tmp_path):
    _script_dir(tmp_path, "meu_script")
    campo = _campo_env("usuario", "MOODLE_USUARIO")

    persistir("meu_script", [campo], {"usuario": "novo_user"})

    env_path = tmp_path / "meu_script" / ".env"
    assert env_path.exists()
    assert "MOODLE_USUARIO" in env_path.read_text()
    assert "novo_user" in env_path.read_text()


def test_persistir_campo_settings_cria_json_correto(tmp_path):
    _script_dir(tmp_path, "meu_script")
    campo = _campo_settings("url", "moodle", "urlLogin")

    persistir("meu_script", [campo], {"url": "https://novo.com"})

    settings_path = tmp_path / "meu_script" / "settings.json"
    dados = json.loads(settings_path.read_text(encoding="utf-8"))
    assert dados["moodle"]["urlLogin"] == "https://novo.com"


def test_persistir_settings_faz_merge_com_json_existente(tmp_path):
    d = _script_dir(tmp_path, "meu_script")
    (d / "settings.json").write_text(json.dumps({"outros": "dados", "moodle": {"url": "antiga"}}), encoding="utf-8")
    campo = _campo_settings("nome_aba", "gsheets", "nomeAba")

    persistir("meu_script", [campo], {"nome_aba": "Nova Aba"})

    dados = json.loads((d / "settings.json").read_text(encoding="utf-8"))
    assert dados["outros"] == "dados"
    assert dados["gsheets"]["nomeAba"] == "Nova Aba"


def test_persistir_settings_aninhado_dois_niveis(tmp_path):
    _script_dir(tmp_path, "meu_script")
    campo = _campo_settings("headless", "moodle", "headless")
    campo.tipo = "bool"

    persistir("meu_script", [campo], {"headless": True})

    dados = json.loads((tmp_path / "meu_script" / "settings.json").read_text(encoding="utf-8"))
    assert dados["moodle"]["headless"] is True


def test_persistir_valor_none_nao_escreve_campo_opcional(tmp_path):
    _script_dir(tmp_path, "meu_script")
    campo = _campo_settings("url", "moodle", "url", obrigatorio=False)

    persistir("meu_script", [campo], {"url": None})

    settings_path = tmp_path / "meu_script" / "settings.json"
    if settings_path.exists():
        dados = json.loads(settings_path.read_text(encoding="utf-8"))
        assert dados.get("moodle", {}).get("url") is None
