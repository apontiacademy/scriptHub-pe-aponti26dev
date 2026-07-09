import pytest

from scripthub.services.config.main import config, limpar, visualizar
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
