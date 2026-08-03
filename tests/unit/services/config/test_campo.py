from scripthub.services.config.campo import Campo


def test_campo_scripts_default_e_tupla_vazia():
    campo = Campo(chave="x", rotulo="X", tipo="texto", origem="settings")

    assert campo.scripts == ()


def test_campo_scripts_aceita_tupla_de_slugs():
    campo = Campo(chave="x", rotulo="X", tipo="senha", origem="keyring", scripts=("auditar",))

    assert campo.scripts == ("auditar",)


def test_campo_nao_tem_mais_atributo_env_var():
    campo = Campo(chave="x", rotulo="X", tipo="texto", origem="settings")

    assert not hasattr(campo, "env_var")
