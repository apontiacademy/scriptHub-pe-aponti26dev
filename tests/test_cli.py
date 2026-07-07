import pytest
import typer

from scripthub.cli import _executar_pipeline_simples, executar_script, relatorios
from scripthub.services.erros import ErroConfiguracao, ErroIntegracao, FalhaParcial
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


def test_executar_script_passo_invalido_loga_erro_unico_e_levanta_exit_3(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    with pytest.raises(typer.Exit) as exc_info:
        executar_script(None, [_escopo()], "passo-inexistente", "TÍTULO")

    assert exc_info.value.exit_code == 3
    mock_log.erro.assert_called_once_with("Passo 'passo-inexistente' inválido. Disponíveis: baixar")


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

    mock_log.erro.assert_any_call("Script finalizado com erro. Código de saída: 2")


def test_executar_script_typer_exit_nao_zero_loga_erro_com_codigo_correto_e_propaga(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def sai_com_erro(config):
        raise typer.Exit(2)

    with pytest.raises(typer.Exit):
        executar_script(None, [_escopo(func=sai_com_erro)], None, "TÍTULO")

    mock_log.erro.assert_any_call("Script finalizado com erro. Código de saída: 2")


@pytest.mark.parametrize(
    "excecao,codigo",
    [
        (ErroConfiguracao, 2),
        (FalhaParcial, 4),
        (ErroIntegracao, 5),
    ],
)
def test_executar_script_erro_scripthub_loga_mensagem_especifica_e_levanta_exit_com_codigo(mocker, excecao, codigo):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha(config):
        raise excecao("mensagem específica")

    with pytest.raises(typer.Exit) as exc_info:
        executar_script(None, [_escopo(func=falha)], None, "TÍTULO")

    assert exc_info.value.exit_code == codigo
    mock_log.erro.assert_any_call("mensagem específica")
    mock_log.erro.assert_any_call(f"Script finalizado com erro. Código de saída: {codigo}")


@pytest.mark.parametrize(
    "excecao,codigo",
    [
        (ErroConfiguracao, 2),
        (FalhaParcial, 4),
        (ErroIntegracao, 5),
    ],
)
def test_executar_pipeline_simples_erro_scripthub_loga_mensagem_especifica_e_levanta_exit_com_codigo(
    mocker, excecao, codigo
):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha():
        raise excecao("mensagem específica")

    with pytest.raises(typer.Exit) as exc_info:
        _executar_pipeline_simples(falha)

    assert exc_info.value.exit_code == codigo
    mock_log.erro.assert_any_call("mensagem específica")
    mock_log.erro.assert_any_call(f"Script finalizado com erro. Código de saída: {codigo}")


def test_relatorios_modo_invalido_levanta_exit_3(mocker):
    mocker.patch("scripthub.cli.log")

    with pytest.raises(typer.Exit) as exc_info:
        relatorios(modo="invalido", passo=None)

    assert exc_info.value.exit_code == 3


def test_relatorios_compilar_com_passo_levanta_exit_3(mocker):
    mocker.patch("scripthub.cli.log")

    with pytest.raises(typer.Exit) as exc_info:
        relatorios(modo="compilar", passo="baixar")

    assert exc_info.value.exit_code == 3
