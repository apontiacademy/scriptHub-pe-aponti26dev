from pathlib import Path

import pytest


def pytest_collection_modifyitems(config, items):
    """Aplica automaticamente os marcadores `unit`/`integration` com base no
    diretório de topo do teste dentro de `tests/` (`tests/unit/...` ou
    `tests/integration/...`), evitando decorar ~400 funções manualmente.
    Itens fora dessas duas árvores (ex.: `tests/features/`, `tests/functional/`,
    cenários pytest-bdd) não recebem nenhum dos dois marcadores."""
    rootdir = Path(config.rootpath) / "tests"
    for item in items:
        try:
            relativo = item.path.relative_to(rootdir)
        except ValueError:
            continue
        topo = relativo.parts[0] if relativo.parts else ""
        if topo == "unit":
            item.add_marker(pytest.mark.unit)
        elif topo == "integration":
            item.add_marker(pytest.mark.integration)


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
