from scripthub.services.menu.main import discover_modules, read_docstring


# ── read_docstring ────────────────────────────────────────────────────────────


def test_read_docstring_uma_linha(tmp_path):
    f = tmp_path / "main.py"
    f.write_text('"""Pipeline completo."""\nfrom .executar import main\n', encoding="utf-8")

    assert read_docstring(f) == "Pipeline completo."


def test_read_docstring_multiline_retorna_primeira_linha(tmp_path):
    f = tmp_path / "main.py"
    f.write_text('"""Primeira linha.\nSegunda linha.\n"""\n', encoding="utf-8")

    assert read_docstring(f) == "Primeira linha."


def test_read_docstring_sem_docstring_retorna_vazio(tmp_path):
    f = tmp_path / "main.py"
    f.write_text("from .executar import main\n", encoding="utf-8")

    assert read_docstring(f) == ""


def test_read_docstring_docstring_vazio_retorna_vazio(tmp_path):
    f = tmp_path / "main.py"
    f.write_text('""""""', encoding="utf-8")

    assert read_docstring(f) == ""


# ── discover_modules ──────────────────────────────────────────────────────────


def test_discover_modules_encontra_modulo_valido(tmp_path):
    mod = tmp_path / "meu_modulo"
    mod.mkdir()
    (mod / "__init__.py").write_text('MENU_CMD = ("meu_modulo",)\n', encoding="utf-8")
    (mod / "main.py").write_text('"""Faz algo util."""\n', encoding="utf-8")

    result = discover_modules(tmp_path)

    assert len(result) == 1
    name, cmd, desc = result[0]
    assert name == "meu_modulo"
    assert cmd == ("meu_modulo",)
    assert desc == "Faz algo util."


def test_discover_modules_ignora_dir_sem_init(tmp_path):
    mod = tmp_path / "sem_init"
    mod.mkdir()
    (mod / "main.py").write_text('"""Teste."""\n', encoding="utf-8")

    result = discover_modules(tmp_path)

    assert result == []


def test_discover_modules_ignora_dir_sem_menu_cmd(tmp_path):
    mod = tmp_path / "sem_menu_cmd"
    mod.mkdir()
    (mod / "__init__.py").write_text("from .main import main\n", encoding="utf-8")
    (mod / "main.py").write_text('"""Descricao."""\n', encoding="utf-8")

    result = discover_modules(tmp_path)

    assert result == []


def test_discover_modules_ordem_alfabetica(tmp_path):
    for name in ["zzz", "aaa", "mmm"]:
        d = tmp_path / name
        d.mkdir()
        (d / "__init__.py").write_text(f'MENU_CMD = ("{name}",)\n', encoding="utf-8")
        (d / "main.py").write_text(f'"""{name} desc."""\n', encoding="utf-8")

    result = discover_modules(tmp_path)

    assert [r[0] for r in result] == ["aaa", "mmm", "zzz"]


def test_discover_modules_sem_main_py_retorna_desc_vazia(tmp_path):
    mod = tmp_path / "sem_main"
    mod.mkdir()
    (mod / "__init__.py").write_text('MENU_CMD = ("sem_main",)\n', encoding="utf-8")

    result = discover_modules(tmp_path)

    assert len(result) == 1
    assert result[0][2] == ""


def test_discover_modules_retorna_cmd_como_tupla(tmp_path):
    mod = tmp_path / "meu_mod"
    mod.mkdir()
    (mod / "__init__.py").write_text('MENU_CMD = ("meu_mod", "alias")\n', encoding="utf-8")
    (mod / "main.py").write_text('"""Desc."""\n', encoding="utf-8")

    result = discover_modules(tmp_path)

    _, cmd, _ = result[0]
    assert cmd == ("meu_mod", "alias")
