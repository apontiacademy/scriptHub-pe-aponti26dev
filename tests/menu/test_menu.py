import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripthub.scripts.menu.main import discover_modules, read_docstring


def test_read_docstring_uma_linha(tmp_path):
    f = tmp_path / "__main__.py"
    f.write_text('"""Pipeline completo."""\nfrom .executar import main\n', encoding="utf-8")
    assert read_docstring(f) == "Pipeline completo."


def test_read_docstring_multiline_retorna_primeira_linha(tmp_path):
    f = tmp_path / "__main__.py"
    f.write_text('"""Primeira linha.\nSegunda linha.\n"""\n', encoding="utf-8")
    assert read_docstring(f) == "Primeira linha."


def test_read_docstring_sem_docstring_retorna_vazio(tmp_path):
    f = tmp_path / "__main__.py"
    f.write_text("from .executar import main\n", encoding="utf-8")
    assert read_docstring(f) == ""


def test_discover_modules_encontra_modulo_valido(tmp_path):
    mod = tmp_path / "meu_modulo"
    mod.mkdir()
    (mod / "__init__.py").write_text("", encoding="utf-8")
    (mod / "__main__.py").write_text('"""Faz algo útil."""\n', encoding="utf-8")

    result = discover_modules(tmp_path)
    assert result == [("meu_modulo", "Faz algo útil.")]


def test_discover_modules_ignora_dir_sem_init(tmp_path):
    mod = tmp_path / "sem_init"
    mod.mkdir()
    (mod / "__main__.py").write_text('"""Teste."""\n', encoding="utf-8")

    result = discover_modules(tmp_path)
    assert result == []


def test_discover_modules_ignora_dir_sem_main(tmp_path):
    mod = tmp_path / "sem_main"
    mod.mkdir()
    (mod / "__init__.py").write_text("", encoding="utf-8")

    result = discover_modules(tmp_path)
    assert result == []


def test_discover_modules_ordem_alfabetica(tmp_path):
    for name, desc in [("zzz", '"""Z."""\n'), ("aaa", '"""A."""\n'), ("mmm", '"""M."""\n')]:
        d = tmp_path / name
        d.mkdir()
        (d / "__init__.py").write_text("", encoding="utf-8")
        (d / "__main__.py").write_text(desc, encoding="utf-8")

    result = discover_modules(tmp_path)
    assert [r[0] for r in result] == ["aaa", "mmm", "zzz"]


def test_discover_modules_sem_descricao_retorna_string_vazia(tmp_path):
    mod = tmp_path / "sem_doc"
    mod.mkdir()
    (mod / "__init__.py").write_text("", encoding="utf-8")
    (mod / "__main__.py").write_text("from .executar import main\n", encoding="utf-8")

    result = discover_modules(tmp_path)
    assert result == [("sem_doc", "")]


def test_read_docstring_docstring_vazio_retorna_vazio(tmp_path):
    f = tmp_path / "__main__.py"
    f.write_text('""""""', encoding="utf-8")
    assert read_docstring(f) == ""
