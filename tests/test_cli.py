from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

import scripthub.cli as cli_module
from scripthub.cli import (
    _carregar_config,
    _executar_com_tratamento_global,
    _executar_pipeline_simples,
    app,
    config,
    executar_script,
)
from scripthub.services.erros import ErroConfiguracao, ErroIntegracao, ErroUsoCLI, FalhaParcial
from scripthub.services.escopo import Escopo


def _escopo(slug="baixar", nome="Baixar", func=None, aliases=()):
    return Escopo(slug, nome, func or (lambda config: None), aliases)


runner = CliRunner()


def test_aliases_nao_lista_menu_interativo():
    result = runner.invoke(app, ["--aliases"])

    assert result.exit_code == 0
    assert "scripthub menu" not in result.output
    assert "[depreciado]" not in result.output


def test_menu_interativo_nao_e_um_comando_registrado():
    nomes = {comando.name for comando in app.registered_commands}

    assert nomes.isdisjoint({"menu", "m"})


# --- executar_script / _executar_pipeline_simples: só executam e propagam, sem logar/converter ---


def test_executar_script_sucesso_loga_mensagem_padronizada_com_codigo_0(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    executar_script(None, [_escopo()], None, "TÍTULO")

    mock_log.sucesso.assert_any_call("Script finalizado com sucesso. Código de saída: 0")


def test_executar_script_excecao_generica_propaga_sem_logar(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha(config):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        executar_script(None, [_escopo(func=falha)], None, "TÍTULO")

    mock_log.erro.assert_not_called()


def test_executar_script_passo_invalido_levanta_erro_uso_cli_sem_logar(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    with pytest.raises(ErroUsoCLI) as exc_info:
        executar_script(None, [_escopo()], "passo-inexistente", "TÍTULO")

    assert exc_info.value.codigo_saida == 3
    assert "Passo 'passo-inexistente' inválido. Disponíveis: baixar" in str(exc_info.value)
    mock_log.erro.assert_not_called()


def test_executar_pipeline_simples_sucesso_loga_mensagem_padronizada_com_codigo_0(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    _executar_pipeline_simples(lambda: None)

    mock_log.sucesso.assert_any_call("Script finalizado com sucesso. Código de saída: 0")


def test_executar_pipeline_simples_excecao_generica_propaga_sem_logar(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        _executar_pipeline_simples(falha)

    mock_log.erro.assert_not_called()


@pytest.mark.parametrize(
    "excecao,codigo",
    [
        (ErroConfiguracao, 2),
        (FalhaParcial, 4),
        (ErroIntegracao, 5),
    ],
)
def test_executar_script_erro_scripthub_propaga_sem_logar(mocker, excecao, codigo):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha(config):
        raise excecao("mensagem específica")

    with pytest.raises(excecao) as exc_info:
        executar_script(None, [_escopo(func=falha)], None, "TÍTULO")

    assert exc_info.value.codigo_saida == codigo
    mock_log.erro.assert_not_called()


@pytest.mark.parametrize(
    "excecao,codigo",
    [
        (ErroConfiguracao, 2),
        (FalhaParcial, 4),
        (ErroIntegracao, 5),
    ],
)
def test_executar_pipeline_simples_erro_scripthub_propaga_sem_logar(mocker, excecao, codigo):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha():
        raise excecao("mensagem específica")

    with pytest.raises(excecao) as exc_info:
        _executar_pipeline_simples(falha)

    assert exc_info.value.codigo_saida == codigo
    mock_log.erro.assert_not_called()


# --- _carregar_config: converte KeyError, enriquece ErroConfiguracao com dica, propaga o resto ---


def test_carregar_config_sucesso_retorna_valor():
    assert _carregar_config(lambda: {"ok": True}, "meu_script") == {"ok": True}


def test_carregar_config_key_error_vira_erro_configuracao_com_dica():
    def carregar():
        raise KeyError("moodle_usuario")

    with pytest.raises(ErroConfiguracao) as exc_info:
        _carregar_config(carregar, "meu_script")

    assert "meu_script" in str(exc_info.value)
    assert exc_info.value.dica == "Execute: scripthub config meu_script"


def test_carregar_config_erro_configuracao_sem_dica_recebe_dica_padrao():
    def carregar():
        raise ErroConfiguracao("settings.json ausente")

    with pytest.raises(ErroConfiguracao) as exc_info:
        _carregar_config(carregar, "meu_script")

    assert exc_info.value.dica == "Execute: scripthub config meu_script"


def test_carregar_config_erro_configuracao_com_dica_propria_nao_e_sobrescrita():
    def carregar():
        raise ErroConfiguracao("settings.json ausente", dica="dica customizada")

    with pytest.raises(ErroConfiguracao) as exc_info:
        _carregar_config(carregar, "meu_script")

    assert exc_info.value.dica == "dica customizada"


def test_carregar_config_excecao_generica_propaga_sem_conversao():
    def carregar():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        _carregar_config(carregar, "meu_script")


# --- _executar_com_tratamento_global: handler global único ---


def test_tratamento_global_erro_scripthub_loga_mensagem_mesclada_e_levanta_system_exit(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha():
        raise ErroConfiguracao("settings.json ausente")

    with pytest.raises(SystemExit) as exc_info:
        _executar_com_tratamento_global(falha)

    assert exc_info.value.code == 2
    mock_log.erro.assert_called_once_with("settings.json ausente. Código de saída: 2")
    mock_log.passo.assert_not_called()


def test_tratamento_global_erro_scripthub_nao_duplica_ponto_final(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha():
        raise ErroConfiguracao("settings.json ausente.")

    with pytest.raises(SystemExit):
        _executar_com_tratamento_global(falha)

    mock_log.erro.assert_called_once_with("settings.json ausente. Código de saída: 2")


def test_tratamento_global_excecao_generica_nao_duplica_ponto_final(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha():
        raise RuntimeError("boom.")

    with pytest.raises(SystemExit):
        _executar_com_tratamento_global(falha)

    mock_log.erro.assert_called_once_with("Erro inesperado: boom. Código de saída: 1")


def test_tratamento_global_com_dica_loga_dica_apos_erro(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha():
        raise ErroConfiguracao("settings.json ausente", dica="Execute: scripthub config -s x")

    with pytest.raises(SystemExit):
        _executar_com_tratamento_global(falha)

    mock_log.passo.assert_called_once_with("Execute: scripthub config -s x")


def test_tratamento_global_excecao_generica_loga_e_levanta_system_exit_1(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    def falha():
        raise RuntimeError("boom")

    with pytest.raises(SystemExit) as exc_info:
        _executar_com_tratamento_global(falha)

    assert exc_info.value.code == 1
    mock_log.erro.assert_called_once_with("Erro inesperado: boom. Código de saída: 1")


def test_tratamento_global_debug_ativo_chama_traceback(mocker):
    mock_log = mocker.patch("scripthub.cli.log")
    mocker.patch.object(cli_module, "_DEBUG", True)

    def falha():
        raise RuntimeError("boom")

    with pytest.raises(SystemExit):
        _executar_com_tratamento_global(falha)

    mock_log.traceback.assert_called_once()


def test_tratamento_global_debug_inativo_nao_chama_traceback(mocker):
    mock_log = mocker.patch("scripthub.cli.log")
    mocker.patch.object(cli_module, "_DEBUG", False)

    def falha():
        raise RuntimeError("boom")

    with pytest.raises(SystemExit):
        _executar_com_tratamento_global(falha)

    mock_log.traceback.assert_not_called()


def test_tratamento_global_debug_nao_afeta_erro_scripthub(mocker):
    mock_log = mocker.patch("scripthub.cli.log")
    mocker.patch.object(cli_module, "_DEBUG", True)

    def falha():
        raise ErroConfiguracao("settings.json ausente")

    with pytest.raises(SystemExit):
        _executar_com_tratamento_global(falha)

    mock_log.traceback.assert_not_called()


def test_tratamento_global_sucesso_nao_levanta_e_nao_loga(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    _executar_com_tratamento_global(lambda: None)

    mock_log.erro.assert_not_called()


# --- flag --debug: seta o global do módulo a partir do callback ---


def test_callback_debug_flag_seta_modulo_global():
    ctx = SimpleNamespace(invoked_subcommand="frequencias")

    cli_module._callback(ctx, versao=False, aliases=False, debug=True)
    assert cli_module._DEBUG is True

    cli_module._callback(ctx, versao=False, aliases=False, debug=False)
    assert cli_module._DEBUG is False


# --- validações de uso da CLI viram ErroUsoCLI, sem log/typer.Exit direto ---


def test_config_opcoes_e_limpar_juntos_levanta_erro_uso_cli(mocker):
    mock_log = mocker.patch("scripthub.cli.log")

    with pytest.raises(ErroUsoCLI) as exc_info:
        config(dominio=None, apenas_visualizar=True, limpar=True)

    assert exc_info.value.codigo_saida == 3
    mock_log.erro.assert_not_called()


# --- subapps: registro duplo (nome cheio + alias) resolve para o mesmo comando ---


def test_relatorios_subapp_registrado_com_nome_cheio_e_alias():
    nomes = {t.name for t in app.registered_groups}

    assert {"relatorios", "r"}.issubset(nomes)


def test_frequencias_subapp_registrado_com_nome_cheio_e_alias():
    nomes = {t.name for t in app.registered_groups}

    assert {"frequencias", "f"}.issubset(nomes)


def test_relatorios_help_lista_subcomandos_auditar_e_compilar():
    result = runner.invoke(app, ["relatorios", "--help"])

    assert result.exit_code == 0
    assert "auditar" in result.output
    assert "compilar" in result.output


def test_relatorios_a_e_alias_de_auditar(mocker):
    mocker.patch("scripthub.cli._carregar_config", return_value=None)
    mock_executar = mocker.patch("scripthub.cli.executar_script")

    result = runner.invoke(app, ["relatorios", "a"])

    assert result.exit_code == 0
    mock_executar.assert_called_once()


def test_r_a_encadeia_alias_de_dominio_e_de_script(mocker):
    mocker.patch("scripthub.cli._carregar_config", return_value=None)
    mock_executar = mocker.patch("scripthub.cli.executar_script")

    result = runner.invoke(app, ["r", "a"])

    assert result.exit_code == 0
    mock_executar.assert_called_once()


def test_relatorios_compilar_chama_pipeline_simples(mocker):
    mock_pipeline = mocker.patch("scripthub.cli._executar_pipeline_simples")

    result = runner.invoke(app, ["relatorios", "compilar"])

    assert result.exit_code == 0
    mock_pipeline.assert_called_once()


def test_relatorios_extrair_chama_executar_script_com_passo_fixo(mocker):
    mocker.patch("scripthub.cli._carregar_config", return_value=None)
    mock_executar = mocker.patch("scripthub.cli.executar_script")

    result = runner.invoke(app, ["relatorios", "extrair"])

    assert result.exit_code == 0
    mock_executar.assert_called_once_with(None, mocker.ANY, "extrair", "AUDITORIA DE RELATÓRIOS")


def test_relatorios_e_e_alias_de_extrair(mocker):
    mocker.patch("scripthub.cli._carregar_config", return_value=None)
    mock_executar = mocker.patch("scripthub.cli.executar_script")

    result = runner.invoke(app, ["r", "e"])

    assert result.exit_code == 0
    mock_executar.assert_called_once_with(None, mocker.ANY, "extrair", "AUDITORIA DE RELATÓRIOS")


def test_frequencias_sem_subcomando_executa_callback(mocker):
    mocker.patch("scripthub.cli._carregar_config", return_value=None)
    mock_executar = mocker.patch("scripthub.cli.executar_script")

    result = runner.invoke(app, ["frequencias"])

    assert result.exit_code == 0
    mock_executar.assert_called_once()
