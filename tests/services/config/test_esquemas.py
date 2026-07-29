import pytest

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


def test_esquema_relatorios_tem_um_unico_campo_moodle_usuario():
    campos = [c for c in ESQUEMAS["relatorios"] if c.chave == "moodle_usuario"]

    assert len(campos) == 1


def test_esquema_relatorios_campo_de_extracao_tem_scripts_so_extrair():
    campo = _campo("relatorios", "moodle_urls_relatorios")

    assert campo.scripts == ("extrair",)


def test_esquema_relatorios_campo_so_de_compilar_tem_scripts_compilar():
    campo = _campo("relatorios", "moodle_meses")

    assert campo.scripts == ("compilar",)


def test_esquema_relatorios_campo_comum_tem_scripts_vazio():
    campo = _campo("relatorios", "moodle_usuario")

    assert campo.scripts == ()


def test_esquema_frequencias_campo_de_extracao_tem_scripts_auditar_e_extrair():
    campo = _campo("frequencias", "moodle_caminho_exportacao")

    assert campo.scripts == ("auditar", "extrair")


def test_esquema_relatorios_nao_tem_mais_campos_de_auditar():
    chaves_removidas = {
        "gsheets_id_planilha",
        "gsheets_nome_aba",
        "gsheets_caminho_backup",
        "gsheets_caminho_json_credenciais",
        "moodle_exportar_analise",
        "moodle_caminho_exportacao_analise",
        "moodle_csv_residentes",
    }
    chaves_atuais = {c.chave for c in ESQUEMAS["relatorios"]}

    assert chaves_removidas.isdisjoint(chaves_atuais)


@pytest.mark.parametrize("dominio", ["frequencias", "relatorios", "softskills", "torpedo"])
def test_moodle_usuario_vem_de_settings_toml(dominio):
    campo = _campo(dominio, "moodle_usuario")

    assert campo.origem == "settings"
    assert campo.json_chaves == ["moodle", "usuario"]


@pytest.mark.parametrize("dominio", ["frequencias", "relatorios", "softskills", "torpedo"])
def test_moodle_senha_vem_do_keyring(dominio):
    campo = _campo(dominio, "moodle_senha")

    assert campo.origem == "keyring"
