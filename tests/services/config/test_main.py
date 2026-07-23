import pytest

from scripthub.services.config.main import config, discover_modules, limpar, read_docstring, visualizar
from scripthub.services.erros import ErroUsoCLI

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
    (modulo / "__init__.py").write_text('MENU_CMD = ("meu_modulo",)\n', encoding="utf-8")
    (modulo / "main.py").write_text('"""Faz algo útil."""\n', encoding="utf-8")

    assert discover_modules(tmp_path) == [("meu_modulo", ("meu_modulo",), "Faz algo útil.")]


def test_discover_modules_ignora_dir_sem_init(tmp_path):
    modulo = tmp_path / "sem_init"
    modulo.mkdir()
    (modulo / "main.py").write_text('"""Teste."""\n', encoding="utf-8")

    assert discover_modules(tmp_path) == []


def test_discover_modules_ignora_dir_sem_menu_cmd(tmp_path):
    modulo = tmp_path / "sem_menu_cmd"
    modulo.mkdir()
    (modulo / "__init__.py").write_text("from .main import main\n", encoding="utf-8")

    assert discover_modules(tmp_path) == []


def test_discover_modules_ordem_alfabetica(tmp_path):
    for nome in ["zzz", "aaa", "mmm"]:
        modulo = tmp_path / nome
        modulo.mkdir()
        (modulo / "__init__.py").write_text(f'MENU_CMD = ("{nome}",)\n', encoding="utf-8")

    assert [modulo[0] for modulo in discover_modules(tmp_path)] == ["aaa", "mmm", "zzz"]


def test_config_sem_scripts_com_esquema_loga_aviso_nao_erro(mocker):
    mocker.patch(f"{_PATCH}.discover_modules", return_value=[])
    mock_log = mocker.patch(f"{_PATCH}.log")

    config()

    mock_log.aviso.assert_any_call("Nenhum script com configuração disponível foi encontrado.")
    mock_log.erro.assert_not_called()


def test_config_nome_invalido_levanta_erro_uso_cli_sem_logar(mocker):
    mock_log = mocker.patch(f"{_PATCH}.log")

    with pytest.raises(ErroUsoCLI) as exc_info:
        config("script-que-nao-existe")

    assert exc_info.value.codigo_saida == 3
    mock_log.erro.assert_not_called()
    mock_log.aviso.assert_not_called()


def test_visualizar_sem_scripts_com_esquema_loga_aviso_nao_erro(mocker):
    mocker.patch(f"{_PATCH}.discover_modules", return_value=[])
    mock_log = mocker.patch(f"{_PATCH}.log")

    visualizar()

    mock_log.aviso.assert_any_call("Nenhum script com configuração disponível foi encontrado.")
    mock_log.erro.assert_not_called()


def test_visualizar_nome_invalido_levanta_erro_uso_cli_sem_logar(mocker):
    mock_log = mocker.patch(f"{_PATCH}.log")

    with pytest.raises(ErroUsoCLI) as exc_info:
        visualizar("script-que-nao-existe")

    assert exc_info.value.codigo_saida == 3
    mock_log.erro.assert_not_called()


def test_limpar_nome_invalido_levanta_erro_uso_cli_sem_logar(mocker):
    mock_log = mocker.patch(f"{_PATCH}.log")

    with pytest.raises(ErroUsoCLI) as exc_info:
        limpar("script-que-nao-existe")

    assert exc_info.value.codigo_saida == 3
    mock_log.erro.assert_not_called()
    mock_log.aviso.assert_not_called()


def test_limpar_sem_scripts_com_esquema_loga_aviso_nao_erro(mocker):
    mocker.patch(f"{_PATCH}.discover_modules", return_value=[])
    mock_log = mocker.patch(f"{_PATCH}.log")

    limpar()

    mock_log.aviso.assert_any_call("Nenhum script com configuração disponível foi encontrado.")
    mock_log.erro.assert_not_called()
