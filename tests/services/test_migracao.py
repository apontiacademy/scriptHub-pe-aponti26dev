import json

import tomllib

from scripthub.services import migracao


def _preparar_scripts_folder(tmp_path, monkeypatch):
    raiz = {
        "frequencias": tmp_path / "legado" / "frequencias",
        "relatorios": tmp_path / "legado" / "relatorios",
        "softskills": tmp_path / "legado" / "softskills",
        "torpedo": tmp_path / "legado" / "torpedo",
    }
    for pasta in raiz.values():
        pasta.mkdir(parents=True)
    monkeypatch.setattr(migracao, "_DOMINIO_RAIZ", raiz)
    monkeypatch.setattr(
        migracao,
        "_DADOS_LEGADOS",
        {
            "frequencias": [],
            "relatorios": [raiz["relatorios"] / "compilar" / "dados"],
            "softskills": [raiz["softskills"] / "bootcamps", raiz["softskills"] / "aprovados"],
            "torpedo": [],
        },
    )
    return raiz


def _mock_destinos(tmp_path, mocker):
    mocker.patch(
        "scripthub.services.migracao.diretorios.caminho_config",
        side_effect=lambda perfil, dominio: tmp_path / "novo_config" / perfil / dominio,
    )
    mocker.patch(
        "scripthub.services.migracao.diretorios.caminho_dados",
        side_effect=lambda perfil, dominio: tmp_path / "novo_dados" / perfil / dominio,
    )
    mocker.patch("scripthub.services.migracao.perfil.resolver_perfil", return_value="default")


def test_migra_settings_json_para_settings_toml(tmp_path, monkeypatch, mocker):
    raiz = _preparar_scripts_folder(tmp_path, monkeypatch)
    _mock_destinos(tmp_path, mocker)
    (raiz["torpedo"] / "settings.json").write_text(json.dumps({"moodle": {"urlLogin": "https://x.com"}}))

    migracao.migrar_configuracao_legada()

    novo = tmp_path / "novo_config" / "default" / "torpedo" / "settings.toml"
    assert novo.exists()
    assert tomllib.loads(novo.read_text(encoding="utf-8"))["moodle"]["urlLogin"] == "https://x.com"


def test_migra_env_usuario_para_settings_toml_e_senha_para_keyring(tmp_path, monkeypatch, mocker):
    raiz = _preparar_scripts_folder(tmp_path, monkeypatch)
    _mock_destinos(tmp_path, mocker)
    (raiz["softskills"] / ".env").write_text("MOODLE_USUARIO=user1\nMOODLE_SENHA=segredo\n")
    mocker.patch("scripthub.services.migracao.keyring_moodle.obter_senha_moodle", return_value=None)
    mock_definir_senha = mocker.patch("scripthub.services.migracao.keyring_moodle.definir_senha_moodle")

    migracao.migrar_configuracao_legada()

    novo = tmp_path / "novo_config" / "default" / "softskills" / "settings.toml"
    assert tomllib.loads(novo.read_text(encoding="utf-8"))["moodle"]["usuario"] == "user1"
    mock_definir_senha.assert_called_once_with("softskills", "segredo")


def test_migra_pasta_de_dados_legada(tmp_path, monkeypatch, mocker):
    raiz = _preparar_scripts_folder(tmp_path, monkeypatch)
    _mock_destinos(tmp_path, mocker)
    pasta_dados = raiz["relatorios"] / "compilar" / "dados"
    pasta_dados.mkdir(parents=True)
    (pasta_dados / "arquivo.csv").write_text("a,b\n1,2\n")

    migracao.migrar_configuracao_legada()

    novo = tmp_path / "novo_dados" / "default" / "relatorios" / "arquivo.csv"
    assert novo.exists()
    assert novo.read_text() == "a,b\n1,2\n"


def test_migra_pasta_de_dados_legada_preserva_arquivo_original(tmp_path, monkeypatch, mocker):
    raiz = _preparar_scripts_folder(tmp_path, monkeypatch)
    _mock_destinos(tmp_path, mocker)
    pasta_dados = raiz["relatorios"] / "compilar" / "dados"
    pasta_dados.mkdir(parents=True)
    original = pasta_dados / "arquivo.csv"
    original.write_text("a,b\n1,2\n")

    migracao.migrar_configuracao_legada()

    assert original.exists()


def test_layout_novo_sem_arquivos_legados_e_no_op(tmp_path, monkeypatch, mocker):
    _preparar_scripts_folder(tmp_path, monkeypatch)
    _mock_destinos(tmp_path, mocker)
    mock_log = mocker.patch("scripthub.services.migracao.log")

    migracao.migrar_configuracao_legada()

    mock_log.aviso.assert_called_once()
    mock_log.ok.assert_not_called()


def test_migracao_e_idempotente(tmp_path, monkeypatch, mocker):
    raiz = _preparar_scripts_folder(tmp_path, monkeypatch)
    _mock_destinos(tmp_path, mocker)
    (raiz["torpedo"] / "settings.json").write_text(json.dumps({"moodle": {"urlLogin": "https://x.com"}}))

    migracao.migrar_configuracao_legada()
    migracao.migrar_configuracao_legada()  # segunda execução não deve levantar nem duplicar

    novo = tmp_path / "novo_config" / "default" / "torpedo" / "settings.toml"
    assert tomllib.loads(novo.read_text(encoding="utf-8"))["moodle"]["urlLogin"] == "https://x.com"


def test_todos_dominios_sao_migrados_mesmo_quando_um_ja_migrou(tmp_path, monkeypatch, mocker):
    """Regressão: any() com short-circuit pararia de migrar os domínios seguintes
    assim que o primeiro retornasse True — cada domínio precisa ser migrado
    independentemente do resultado dos anteriores."""
    raiz = _preparar_scripts_folder(tmp_path, monkeypatch)
    _mock_destinos(tmp_path, mocker)
    (raiz["frequencias"] / "settings.json").write_text(json.dumps({"moodle": {"urlLogin": "https://a.com"}}))
    (raiz["torpedo"] / "settings.json").write_text(json.dumps({"moodle": {"urlLogin": "https://b.com"}}))

    migracao.migrar_configuracao_legada()

    novo_torpedo = tmp_path / "novo_config" / "default" / "torpedo" / "settings.toml"
    assert novo_torpedo.exists()


def test_migracao_nao_sobrescreve_settings_toml_editado_apos_primeira_migracao(tmp_path, monkeypatch, mocker):
    raiz = _preparar_scripts_folder(tmp_path, monkeypatch)
    _mock_destinos(tmp_path, mocker)
    (raiz["torpedo"] / "settings.json").write_text(json.dumps({"moodle": {"urlLogin": "https://legado.com"}}))
    migracao.migrar_configuracao_legada()

    novo = tmp_path / "novo_config" / "default" / "torpedo" / "settings.toml"
    novo.write_bytes(b'[moodle]\nurlLogin = "https://editado-manualmente.com"\n')

    migracao.migrar_configuracao_legada()

    assert tomllib.loads(novo.read_text(encoding="utf-8"))["moodle"]["urlLogin"] == "https://editado-manualmente.com"


def test_migracao_nao_sobrescreve_usuario_ja_presente_no_settings_toml(tmp_path, monkeypatch, mocker):
    raiz = _preparar_scripts_folder(tmp_path, monkeypatch)
    _mock_destinos(tmp_path, mocker)
    mocker.patch("scripthub.services.migracao.keyring_moodle.obter_senha_moodle", return_value=None)
    mocker.patch("scripthub.services.migracao.keyring_moodle.definir_senha_moodle")
    (raiz["softskills"] / ".env").write_text("MOODLE_USUARIO=legado\n")
    migracao.migrar_configuracao_legada()

    novo = tmp_path / "novo_config" / "default" / "softskills" / "settings.toml"
    settings = tomllib.loads(novo.read_text(encoding="utf-8"))
    settings["moodle"]["usuario"] = "editado-manualmente"
    with open(novo, "wb") as f:
        import tomli_w

        tomli_w.dump(settings, f)

    migracao.migrar_configuracao_legada()

    assert tomllib.loads(novo.read_text(encoding="utf-8"))["moodle"]["usuario"] == "editado-manualmente"


def test_migracao_nao_sobrescreve_senha_ja_presente_no_keyring(tmp_path, monkeypatch, mocker):
    raiz = _preparar_scripts_folder(tmp_path, monkeypatch)
    _mock_destinos(tmp_path, mocker)
    mocker.patch("scripthub.services.migracao.keyring_moodle.obter_senha_moodle", return_value="ja-rotacionada")
    mock_definir_senha = mocker.patch("scripthub.services.migracao.keyring_moodle.definir_senha_moodle")
    (raiz["softskills"] / ".env").write_text("MOODLE_USUARIO=user1\nMOODLE_SENHA=legado\n")

    migracao.migrar_configuracao_legada()

    mock_definir_senha.assert_not_called()
