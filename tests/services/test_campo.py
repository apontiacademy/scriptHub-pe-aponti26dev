from scripthub.services.config.campo import Campo, resolver_dependencias


def _campo(chave, obrigatorio, depende_de=None):
    return Campo(
        chave=chave,
        rotulo="r",
        tipo="texto",
        origem="settings",
        obrigatorio=obrigatorio,
        json_chaves=[chave],
        depende_de=depende_de,
    )


def test_resolver_dependencias_sem_depende_de_mantem_campo_inalterado():
    campo = _campo("a", obrigatorio=False)

    resolvidos = resolver_dependencias([campo], {})

    assert resolvidos[0] == campo


def test_resolver_dependencias_com_dependencia_verdadeira_torna_obrigatorio():
    campo = _campo("b", obrigatorio=False, depende_de="a")

    resolvidos = resolver_dependencias([campo], {"a": True})

    assert resolvidos[0].obrigatorio is True


def test_resolver_dependencias_com_dependencia_falsa_torna_opcional():
    campo = _campo("b", obrigatorio=True, depende_de="a")

    resolvidos = resolver_dependencias([campo], {"a": False})

    assert resolvidos[0].obrigatorio is False


def test_resolver_dependencias_com_dependencia_ausente_torna_opcional():
    campo = _campo("b", obrigatorio=True, depende_de="a")

    resolvidos = resolver_dependencias([campo], {})

    assert resolvidos[0].obrigatorio is False
