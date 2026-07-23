from scripthub.services.config.esquemas import ESQUEMAS


def _campo(chave_modulo, chave_campo):
    campos = ESQUEMAS[chave_modulo]
    return next(c for c in campos if c.chave == chave_campo)


def test_esquema_moodle_url_usa_chave_urlbase():
    campo = _campo("softskills", "moodle_url")

    assert campo.json_chaves == ["moodle", "urlBase"]


def test_esquema_frequencias_caminho_json_credenciais_exige_absoluto():
    campo = _campo("auditar_frequencias", "gsheets_caminho_json_credenciais")

    assert campo.caminho_absoluto is True


def test_esquema_relatorios_caminho_json_credenciais_exige_absoluto():
    campo = _campo("auditar_relatorios", "gsheets_caminho_json_credenciais")

    assert campo.caminho_absoluto is True
