from scripthub.services.config.campo import Campo


def test_campo_scripts_default_e_tupla_vazia():
    campo = Campo(chave="x", rotulo="X", tipo="texto", origem="env")

    assert campo.scripts == ()


def test_campo_scripts_aceita_tupla_de_slugs():
    campo = Campo(chave="x", rotulo="X", tipo="texto", origem="env", scripts=("auditar",))

    assert campo.scripts == ("auditar",)
