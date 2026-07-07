import pytest
import typer

from scripthub.cli import _executar_pipeline_simples, executar_script
from scripthub.services.escopo import Escopo


def _escopo(slug="baixar", nome="Baixar", func=None, aliases=()):
    return Escopo(slug, nome, func or (lambda config: None), aliases)


def test_executar_script_sucesso_loga_mensagem_padronizada_com_codigo_0(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    executar_script(None, [_escopo()], None, "TÍTULO")

    mock_log.sucesso.assert_any_call("Script finalizado com sucesso. Código de saída: 0")


def test_executar_script_excecao_em_escopo_loga_erro_com_codigo_1_e_levanta_exit(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha(config):
        raise RuntimeError("boom")

    with pytest.raises(typer.Exit):
        executar_script(None, [_escopo(func=falha)], None, "TÍTULO")

    mock_log.erro.assert_any_call("Script finalizado com erro. Código de saída: 1")


def test_executar_script_passo_invalido_loga_erro_com_codigo_1_e_levanta_exit(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    with pytest.raises(typer.Exit):
        executar_script(None, [_escopo()], "passo-inexistente", "TÍTULO")

    mock_log.erro.assert_any_call("Script finalizado com erro. Código de saída: 1")


def test_executar_pipeline_simples_sucesso_loga_mensagem_padronizada_com_codigo_0(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    _executar_pipeline_simples(lambda: None)

    mock_log.sucesso.assert_any_call("Script finalizado com sucesso. Código de saída: 0")


def test_executar_pipeline_simples_excecao_loga_erro_com_codigo_1_e_levanta_exit(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha():
        raise RuntimeError("boom")

    with pytest.raises(typer.Exit):
        _executar_pipeline_simples(falha)

    mock_log.erro.assert_any_call("Script finalizado com erro. Código de saída: 1")


def test_executar_script_typer_exit_zero_nao_loga_erro_e_propaga(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def sai_com_zero(config):
        raise typer.Exit(0)

    with pytest.raises(typer.Exit):
        executar_script(None, [_escopo(func=sai_com_zero)], None, "TÍTULO")

    mock_log.erro.assert_not_called()


def test_executar_script_system_exit_zero_nao_loga_erro_e_propaga(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def sai_com_zero(config):
        raise SystemExit(0)

    with pytest.raises(SystemExit):
        executar_script(None, [_escopo(func=sai_com_zero)], None, "TÍTULO")

    mock_log.erro.assert_not_called()


def test_executar_pipeline_simples_typer_exit_zero_nao_loga_erro_e_propaga(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def sai_com_zero():
        raise typer.Exit(0)

    with pytest.raises(typer.Exit):
        _executar_pipeline_simples(sai_com_zero)

    mock_log.erro.assert_not_called()


def test_executar_pipeline_simples_system_exit_zero_nao_loga_erro_e_propaga(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def sai_com_zero():
        raise SystemExit(0)

    with pytest.raises(SystemExit):
        _executar_pipeline_simples(sai_com_zero)

    mock_log.erro.assert_not_called()


def test_executar_pipeline_simples_system_exit_nao_zero_loga_erro_e_propaga(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def sai_com_erro():
        raise SystemExit(2)

    with pytest.raises(SystemExit):
        _executar_pipeline_simples(sai_com_erro)

    mock_log.erro.assert_any_call("Script finalizado com erro. Código de saída: 1")
