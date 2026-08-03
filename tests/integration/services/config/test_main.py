import pytest

from scripthub.services.config.main import discover_modules, limpar, read_docstring

_PATCH = "scripthub.services.config.main"


def test_read_docstring_uma_linha(tmp_path):
    arquivo = tmp_path / "main.py"
    arquivo.write_text('"""Pipeline completo."""\nfrom .executar import main\n', encoding="utf-8")

    assert read_docstring(arquivo) == "Pipeline completo."


def test_read_docstring_multiline_retorna_primeira_linha(tmp_path):
    arquivo = tmp_path / "main.py"
    arquivo.write_text('"""Primeira linha.\nSegunda linha.\n"""\n', encoding="utf-8")

    assert read_docstring(arquivo) == "Primeira linha."


def test_read_docstring_sem_docstring_retorna_vazio(tmp_path):
    arquivo = tmp_path / "main.py"
    arquivo.write_text("from .executar import main\n", encoding="utf-8")

    assert read_docstring(arquivo) == ""


def test_discover_modules_encontra_modulo_valido(tmp_path):
    modulo = tmp_path / "meu_modulo"
    modulo.mkdir()
    (modulo / "__init__.py").write_text('CLI_CMD = ("meu_modulo",)\n', encoding="utf-8")
    (modulo / "main.py").write_text('"""Faz algo útil."""\n', encoding="utf-8")

    assert discover_modules(tmp_path) == [("meu_modulo", ("meu_modulo",), "Faz algo útil.")]


def test_discover_modules_ignora_dir_sem_init(tmp_path):
    modulo = tmp_path / "sem_init"
    modulo.mkdir()
    (modulo / "main.py").write_text('"""Teste."""\n', encoding="utf-8")

    assert discover_modules(tmp_path) == []


def test_discover_modules_ignora_dir_sem_cli_cmd(tmp_path):
    modulo = tmp_path / "sem_cli_cmd"
    modulo.mkdir()
    (modulo / "__init__.py").write_text("from .main import main\n", encoding="utf-8")

    assert discover_modules(tmp_path) == []


def test_discover_modules_ordem_alfabetica(tmp_path):
    for nome in ["zzz", "aaa", "mmm"]:
        modulo = tmp_path / nome
        modulo.mkdir()
        (modulo / "__init__.py").write_text(f'CLI_CMD = ("{nome}",)\n', encoding="utf-8")

    assert [modulo[0] for modulo in discover_modules(tmp_path)] == ["aaa", "mmm", "zzz"]


@pytest.fixture
def keyring_fake_main(mocker):
    armazem: dict[str, str] = {}
    mocker.patch(f"{_PATCH}.perfil.resolver_perfil", return_value="default")
    mocker.patch(f"{_PATCH}.keyring_moodle.obter_senha_moodle", side_effect=lambda d, p: armazem.get(d))
    mocker.patch(f"{_PATCH}.keyring_moodle.remover_senha_moodle", side_effect=lambda d, p: armazem.pop(d, None))
    return armazem


def test_limpar_remove_settings_toml_e_senha_do_keyring(tmp_path, mocker, keyring_fake_main):
    mocker.patch(f"{_PATCH}._script_dir", lambda nome: tmp_path / nome)
    (tmp_path / "torpedo").mkdir()
    (tmp_path / "torpedo" / "settings.toml").write_text("", encoding="utf-8")
    keyring_fake_main["torpedo"] = "senha"
    mocker.patch(f"{_PATCH}.questionary.confirm").return_value.ask.return_value = True

    limpar("torpedo")

    assert not (tmp_path / "torpedo" / "settings.toml").exists()
    assert "torpedo" not in keyring_fake_main


def test_limpar_operacao_cancelada_nao_remove_nada(tmp_path, mocker, keyring_fake_main):
    mocker.patch(f"{_PATCH}._script_dir", lambda nome: tmp_path / nome)
    (tmp_path / "torpedo").mkdir()
    (tmp_path / "torpedo" / "settings.toml").write_text("", encoding="utf-8")
    mocker.patch(f"{_PATCH}.questionary.confirm").return_value.ask.return_value = False

    limpar("torpedo")

    assert (tmp_path / "torpedo" / "settings.toml").exists()
