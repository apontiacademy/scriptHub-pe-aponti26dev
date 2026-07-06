from scripthub.services.config.esquemas import ESQUEMAS


def _campo(chave_modulo, chave_campo):
    campos = ESQUEMAS[chave_modulo]
    return next(c for c in campos if c.chave == chave_campo)


def test_esquema_moodle_url_usa_chave_urlbase():
    campo = _campo("auditar_softskills", "moodle_url")

    assert campo.json_chaves == ["moodle", "urlBase"]
