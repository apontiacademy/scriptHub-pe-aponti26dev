from scripthub.services import log


def test_erro_imprime_painel_rich_no_stderr(capsys):
    log.erro("algo deu errado")

    saida = capsys.readouterr().err

    assert "╭" in saida
    assert "╰" in saida
    assert "Erro" in saida
    assert "algo deu errado" in saida


def test_erro_grava_texto_plano_no_logger(mocker):
    mock_logger = mocker.patch("scripthub.services.log._logger")

    log.erro("algo deu errado")

    mock_logger.error.assert_called_once_with("  ❌ %s", "algo deu errado")


def test_traceback_imprime_excecao_no_stderr(capsys):
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        log.traceback()

    saida = capsys.readouterr().err

    assert "RuntimeError" in saida
    assert "boom" in saida


def test_traceback_grava_texto_completo_no_logger(mocker):
    mock_logger = mocker.patch("scripthub.services.log._logger")

    try:
        raise RuntimeError("boom")
    except RuntimeError:
        log.traceback()

    mock_logger.error.assert_called_once()
    texto_logado = mock_logger.error.call_args[0][0]
    assert "RuntimeError" in texto_logado
    assert "boom" in texto_logado
