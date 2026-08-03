import pytest

from scripthub.services.config.campo import Campo
from scripthub.services.config.main import (
    _escopar_por_script,
    _priorizar_por_script,
    config,
    limpar,
    visualizar,
)
from scripthub.services.erros import ErroUsoCLI

_PATCH = "scripthub.services.config.main"


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


@pytest.fixture
def keyring_fake_main(mocker):
    armazem: dict[str, str] = {}
    mocker.patch(f"{_PATCH}.perfil.resolver_perfil", return_value="default")
    mocker.patch(f"{_PATCH}.keyring_moodle.obter_senha_moodle", side_effect=lambda d, p: armazem.get(d))
    mocker.patch(f"{_PATCH}.keyring_moodle.remover_senha_moodle", side_effect=lambda d, p: armazem.pop(d, None))
    return armazem


def test_limpar_sem_nada_para_remover_loga_aviso(tmp_path, mocker, keyring_fake_main):
    mocker.patch(f"{_PATCH}._script_dir", lambda nome: tmp_path / nome)
    mock_log = mocker.patch(f"{_PATCH}.log")

    limpar("torpedo")

    mock_log.aviso.assert_called_once()


def test_priorizar_por_script_none_mantem_ordem_original():
    campos = [
        Campo(chave="a", rotulo="A", tipo="texto", origem="settings", scripts=("compilar",)),
        Campo(chave="b", rotulo="B", tipo="texto", origem="settings"),
    ]

    assert _priorizar_por_script(campos, None) == campos


def test_priorizar_por_script_coloca_campos_do_script_primeiro():
    comum = Campo(chave="comum", rotulo="Comum", tipo="texto", origem="settings")
    so_compilar = Campo(chave="c", rotulo="C", tipo="texto", origem="settings", scripts=("compilar",))
    so_auditar = Campo(chave="a", rotulo="A", tipo="texto", origem="settings", scripts=("auditar",))

    resultado = _priorizar_por_script([so_compilar, comum, so_auditar], "auditar")

    assert [c.chave for c in resultado] == ["a", "comum", "c"]


def test_config_com_script_prioriza_campos_na_selecao(mocker):
    campos = [
        Campo(chave="c", rotulo="C", tipo="texto", origem="settings", scripts=("compilar",)),
        Campo(chave="a", rotulo="A", tipo="texto", origem="settings", scripts=("auditar",)),
    ]
    mocker.patch(f"{_PATCH}.ESQUEMAS", {"relatorios": campos})
    mocker.patch(f"{_PATCH}.carregar_valores", return_value={})
    mocker.patch(f"{_PATCH}.persistir")
    selecionar_campos_mock = mocker.patch(f"{_PATCH}.selecionar_campos", return_value=[])
    mocker.patch(f"{_PATCH}.log")

    config("relatorios", script="auditar")

    campos_passados = selecionar_campos_mock.call_args[0][0]
    assert [c.chave for c in campos_passados] == ["a", "c"]


def test_escopar_por_script_none_mantem_obrigatorio_original():
    campos = [
        Campo(chave="a", rotulo="A", tipo="texto", origem="settings", obrigatorio=True, scripts=("auditar",)),
        Campo(chave="b", rotulo="B", tipo="texto", origem="settings", obrigatorio=True),
    ]

    assert _escopar_por_script(campos, None) == campos


def test_escopar_por_script_torna_nao_obrigatorio_campo_de_outro_script():
    so_auditar = Campo(chave="a", rotulo="A", tipo="texto", origem="settings", obrigatorio=True, scripts=("auditar",))
    so_compilar = Campo(chave="c", rotulo="C", tipo="texto", origem="settings", obrigatorio=True, scripts=("compilar",))
    comum = Campo(chave="comum", rotulo="Comum", tipo="texto", origem="settings", obrigatorio=True)

    resultado = _escopar_por_script([so_auditar, so_compilar, comum], "auditar")

    por_chave = {c.chave: c.obrigatorio for c in resultado}
    assert por_chave == {"a": True, "c": False, "comum": True}


def test_config_com_script_nao_marca_campo_de_outro_script_como_obrigatorio(mocker):
    campos = [
        Campo(chave="c", rotulo="C", tipo="texto", origem="settings", obrigatorio=True, scripts=("compilar",)),
        Campo(chave="a", rotulo="A", tipo="texto", origem="settings", obrigatorio=True, scripts=("auditar",)),
    ]
    mocker.patch(f"{_PATCH}.ESQUEMAS", {"relatorios": campos})
    mocker.patch(f"{_PATCH}.carregar_valores", return_value={})
    mocker.patch(f"{_PATCH}.persistir")
    selecionar_campos_mock = mocker.patch(f"{_PATCH}.selecionar_campos", return_value=[])
    mocker.patch(f"{_PATCH}.log")

    config("relatorios", script="auditar")

    campos_passados = selecionar_campos_mock.call_args[0][0]
    por_chave = {c.chave: c.obrigatorio for c in campos_passados}
    assert por_chave == {"a": True, "c": False}


def test_visualizar_com_script_nao_marca_campo_de_outro_script_como_obrigatorio(mocker):
    campos = [
        Campo(chave="c", rotulo="C", tipo="texto", origem="settings", obrigatorio=True, scripts=("compilar",)),
        Campo(chave="a", rotulo="A", tipo="texto", origem="settings", obrigatorio=True, scripts=("auditar",)),
    ]
    mocker.patch(f"{_PATCH}.ESQUEMAS", {"relatorios": campos})
    mocker.patch(f"{_PATCH}.carregar_valores", return_value={})
    exibir_campos_mock = mocker.patch(f"{_PATCH}.exibir_campos")
    mocker.patch(f"{_PATCH}.log")

    visualizar("relatorios", script="auditar")

    campos_passados = exibir_campos_mock.call_args[0][0]
    por_chave = {c.chave: c.obrigatorio for c in campos_passados}
    assert por_chave == {"a": True, "c": False}


def test_config_script_invalido_levanta_erro_uso_cli(mocker):
    campos = [
        Campo(chave="c", rotulo="C", tipo="texto", origem="settings", scripts=("compilar",)),
        Campo(chave="a", rotulo="A", tipo="texto", origem="settings", scripts=("auditar",)),
    ]
    mocker.patch(f"{_PATCH}.ESQUEMAS", {"relatorios": campos})
    mock_log = mocker.patch(f"{_PATCH}.log")

    with pytest.raises(ErroUsoCLI) as exc_info:
        config("relatorios", script="auditra")

    assert exc_info.value.codigo_saida == 3
    mock_log.erro.assert_not_called()


def test_visualizar_script_invalido_levanta_erro_uso_cli(mocker):
    campos = [
        Campo(chave="c", rotulo="C", tipo="texto", origem="settings", scripts=("compilar",)),
        Campo(chave="a", rotulo="A", tipo="texto", origem="settings", scripts=("auditar",)),
    ]
    mocker.patch(f"{_PATCH}.ESQUEMAS", {"relatorios": campos})
    mock_log = mocker.patch(f"{_PATCH}.log")

    with pytest.raises(ErroUsoCLI) as exc_info:
        visualizar("relatorios", script="auditra")

    assert exc_info.value.codigo_saida == 3
    mock_log.erro.assert_not_called()


def test_config_script_valido_nao_levanta_erro(mocker):
    campos = [
        Campo(chave="c", rotulo="C", tipo="texto", origem="settings", scripts=("compilar",)),
        Campo(chave="a", rotulo="A", tipo="texto", origem="settings", scripts=("auditar",)),
    ]
    mocker.patch(f"{_PATCH}.ESQUEMAS", {"relatorios": campos})
    mocker.patch(f"{_PATCH}.carregar_valores", return_value={})
    mocker.patch(f"{_PATCH}.persistir")
    mocker.patch(f"{_PATCH}.selecionar_campos", return_value=[])
    mocker.patch(f"{_PATCH}.log")

    config("relatorios", script="auditar")


def test_config_script_em_dominio_sem_scripts_internos_levanta_erro(mocker):
    campos = [Campo(chave="x", rotulo="X", tipo="texto", origem="settings")]
    mocker.patch(f"{_PATCH}.ESQUEMAS", {"frequencias": campos})
    mock_log = mocker.patch(f"{_PATCH}.log")

    with pytest.raises(ErroUsoCLI) as exc_info:
        config("frequencias", script="qualquer")

    assert exc_info.value.codigo_saida == 3
    mock_log.erro.assert_not_called()
