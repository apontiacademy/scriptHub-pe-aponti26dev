import pytest


@pytest.fixture
def moodle_env(tmp_path):
    """Escreve .env com credenciais Moodle válidas em tmp_path."""
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    return tmp_path


@pytest.fixture(autouse=True)
def _sem_handler_de_log_real():
    """Garante que nenhum teste crie um FileHandler real fora de tmp_path: pré-popula
    `_logger.handlers` com um NullHandler antes de cada teste, o que faz o handler
    lazy de `services/log.py` (`_garantir_handler`) fazer early-return. Testes que
    precisam exercitar a criação real do handler (tests/services/test_log.py) limpam
    `_logger.handlers` explicitamente no próprio corpo do teste."""
    import logging

    from scripthub.services import log as log_module

    handlers_originais = list(log_module._logger.handlers)
    if not handlers_originais:
        log_module._logger.addHandler(logging.NullHandler())
    yield
    log_module._logger.handlers = handlers_originais
