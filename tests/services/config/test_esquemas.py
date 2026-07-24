from scripthub.services.config.esquemas import ESQUEMAS


def _campo(chave_modulo, chave_campo):
    campos = ESQUEMAS[chave_modulo]
    return next(c for c in campos if c.chave == chave_campo)


def test_esquema_moodle_url_usa_chave_urlbase():
    campo = _campo("softskills", "moodle_url")

    assert campo.json_chaves == ["moodle", "urlBase"]


def test_esquema_frequencias_caminho_json_credenciais_exige_absoluto():
    campo = _campo("frequencias", "gsheets_caminho_json_credenciais")

    assert campo.caminho_absoluto is True


def test_esquema_relatorios_caminho_json_credenciais_exige_absoluto():
    campo = _campo("relatorios", "gsheets_caminho_json_credenciais")

    assert campo.caminho_absoluto is True


def test_esquema_relatorios_tem_um_unico_campo_moodle_usuario():
    campos = [c for c in ESQUEMAS["relatorios"] if c.chave == "moodle_usuario"]

    assert len(campos) == 1


def test_esquema_relatorios_campo_so_de_auditar_tem_scripts_auditar():
    campo = _campo("relatorios", "moodle_urls_relatorios")

    assert campo.scripts == ("auditar",)


def test_esquema_relatorios_campo_so_de_compilar_tem_scripts_compilar():
    campo = _campo("relatorios", "moodle_meses")

    assert campo.scripts == ("compilar",)


def test_esquema_relatorios_campo_comum_tem_scripts_vazio():
    campo = _campo("relatorios", "moodle_usuario")

    assert campo.scripts == ()
