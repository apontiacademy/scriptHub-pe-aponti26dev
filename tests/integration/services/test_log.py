from scripthub.services import log


def test_garantir_handler_usa_caminho_do_profile_ativo(tmp_path, mocker):
    log._logger.handlers.clear()
    mocker.patch("scripthub.services.log.diretorios.caminho_log", return_value=tmp_path / "state" / "equipe-x")
    mocker.patch("scripthub.services.log.perfil.resolver_perfil", return_value="equipe-x")

    log.passo("teste")

    assert (tmp_path / "state" / "equipe-x" / "scripthub.log").exists()
    log._logger.handlers.clear()


def test_garantir_handler_e_idempotente(tmp_path, mocker):
    log._logger.handlers.clear()
    mocker.patch("scripthub.services.log.diretorios.caminho_log", return_value=tmp_path / "state" / "default")
    mocker.patch("scripthub.services.log.perfil.resolver_perfil", return_value="default")

    log.passo("primeira")
    log.passo("segunda")

    assert len(log._logger.handlers) == 1
    log._logger.handlers.clear()
