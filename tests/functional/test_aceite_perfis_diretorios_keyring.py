"""Step definitions dos critérios de aceite da issue #78 (ver o .feature
correspondente em tests/features/aceite_perfis_diretorios_keyring.feature).

Cross-cutting a vários serviços (`diretorios`, `perfil`, `keyring_moodle`,
`migracao`) e à CLI — por isso o .feature/step-defs ficam na raiz de
tests/features // tests/functional, sem subpasta de domínio/script, mesmo
padrão já usado por test_cli.py/test_i18n.py em tests/unit.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import tomllib
from pytest_bdd import given, parsers, scenarios, then, when
from typer.testing import CliRunner

import scripthub.cli as cli_module
from scripthub.cli import app
from scripthub.services import log as log_module
from scripthub.services import perfil
from scripthub.services.config.campo import Campo

scenarios("aceite_perfis_diretorios_keyring.feature")

runner = CliRunner()


def _fake_platformdirs(tmp_path, mocker):
    """Troca `platformdirs.PlatformDirs` por um objeto com os 3 diretórios raiz
    apontando para dentro de `tmp_path`, isolando os testes do SO real."""
    from scripthub.services import diretorios

    fake = SimpleNamespace(
        user_config_dir=str(tmp_path / "config"),
        user_data_dir=str(tmp_path / "data"),
        user_state_dir=str(tmp_path / "state"),
    )
    mocker.patch.object(diretorios.platformdirs, "PlatformDirs", return_value=fake)
    return fake


def _fake_keyring(mocker):
    """Substitui o keyring do SO por um dict em memória, chaveado por (serviço, usuário)."""
    from scripthub.services import keyring_moodle

    armazem: dict[tuple[str, str], str] = {}

    def _get(servico, usuario):
        return armazem.get((servico, usuario))

    def _set(servico, usuario, senha):
        armazem[(servico, usuario)] = senha

    def _delete(servico, usuario):
        armazem.pop((servico, usuario), None)

    mock_keyring = mocker.patch.object(keyring_moodle, "keyring")
    mock_keyring.get_password.side_effect = _get
    mock_keyring.set_password.side_effect = _set
    mock_keyring.delete_password.side_effect = _delete
    return armazem


@pytest.fixture(autouse=True)
def _estado_limpo():
    """Evita que override de profile ou handler de log vazem de um teste para o outro."""

    def reset():
        perfil.definir_override(None)
        log_module._logger.handlers.clear()

    reset()
    yield
    reset()


# ── set-profile persiste e é usado nas execuções seguintes ────────────────────


@given("que nenhum profile está persistido", target_fixture="contexto")
def dado_nenhum_profile_persistido(tmp_path, mocker):
    _fake_platformdirs(tmp_path, mocker)
    assert perfil.perfil_persistido() == "default"
    return {"tmp_path": tmp_path}


@when(parsers.parse('o usuário roda "scripthub {comando}"'))
def quando_usuario_roda_comando(contexto, comando):
    contexto["resultado"] = runner.invoke(app, comando.split())


@then(parsers.parse('o profile ativo passa a ser "{nome}"'))
def entao_profile_ativo_passa_a_ser(contexto, nome):
    assert contexto["resultado"].exit_code == 0
    assert perfil.perfil_persistido() == nome


@then(parsers.parse('o profile "{nome}" permanece ativo nas execuções seguintes'))
def entao_profile_permanece_ativo(contexto, nome):
    # "execução seguinte" simulada por uma nova leitura do arquivo persistido, sem override
    assert perfil.resolver_perfil() == nome
    assert (contexto["tmp_path"] / "config" / "Profile").read_text(encoding="utf-8").strip() == nome


# ── unset-profile volta para default quando o profile ativo não é default ─────


@given(parsers.parse('que o profile "{nome}" está persistido'), target_fixture="contexto")
def dado_profile_persistido(tmp_path, mocker, nome):
    _fake_platformdirs(tmp_path, mocker)
    runner.invoke(app, ["set-profile", nome])
    return {"tmp_path": tmp_path}


# (o Then "o profile ativo passa a ser <default>" reaproveita entao_profile_ativo_passa_a_ser acima)


# ── unset-profile é no-op quando o profile ativo já é default ─────────────────


@given('que o profile ativo já é "default"', target_fixture="contexto")
def dado_profile_ativo_ja_e_default(tmp_path, mocker):
    _fake_platformdirs(tmp_path, mocker)
    assert perfil.perfil_persistido() == "default"
    return {"tmp_path": tmp_path}


@then("nada muda no profile persistido")
def entao_nada_muda_no_profile_persistido(contexto):
    assert contexto["resultado"].exit_code == 0
    assert perfil.perfil_persistido() == "default"
    assert not (contexto["tmp_path"] / "config" / "Profile").exists()


# ── --profile é um override pontual que não altera o profile persistido ───────


@when(parsers.parse('o usuário roda um comando com a flag "--profile {novo}"'))
def quando_roda_comando_com_flag_profile(contexto, novo):
    ctx = SimpleNamespace(invoked_subcommand="config")
    cli_module._callback(ctx, versao=False, aliases=False, debug=False, profile=novo)
    contexto["profile_override"] = novo


@then(parsers.parse('a execução usa o profile "{nome}"'))
def entao_execucao_usa_profile(nome):
    assert perfil.resolver_perfil() == nome, "a execução com --profile deve usar o profile informado"


@then(parsers.parse('o profile persistido continua sendo "{nome}"'))
def entao_profile_persistido_continua_sendo(nome):
    assert perfil.perfil_persistido() == nome, "--profile não deve alterar o persistido"


@then(parsers.parse('a próxima execução sem a flag usa o profile "{nome}"'))
def entao_proxima_execucao_sem_flag_usa_profile(nome):
    # "próxima execução sem a flag": novo processo simulado por limpar o override
    perfil.definir_override(None)
    assert perfil.resolver_perfil() == nome


# ── dois profiles não vazam config/dados entre si ──────────────────────────────


@given("dois profiles diferentes com config própria para o mesmo script", target_fixture="contexto")
def dado_dois_profiles_com_config_propria(tmp_path, mocker):
    _fake_platformdirs(tmp_path, mocker)
    from scripthub.services.config import persistencia

    campo = Campo(chave="url", rotulo="r", tipo="texto", origem="settings", settings_chaves=["moodle", "urlLogin"])

    perfil.definir_perfil("equipe-diurna")
    persistencia.persistir("frequencias", [campo], {"url": "https://diurna.example.com"})

    perfil.definir_perfil("equipe-noturna")
    persistencia.persistir("frequencias", [campo], {"url": "https://noturna.example.com"})

    return {"campo": campo}


@when("o usuário alterna entre os dois profiles")
def quando_usuario_alterna_entre_profiles(contexto):
    from scripthub.services.config import persistencia

    perfil.definir_perfil("equipe-noturna")
    contexto["valores_noturna"] = persistencia.carregar_valores("frequencias", [contexto["campo"]])

    perfil.definir_perfil("equipe-diurna")
    contexto["valores_diurna"] = persistencia.carregar_valores("frequencias", [contexto["campo"]])


@then("cada execução só enxerga a config do profile ativo")
def entao_cada_execucao_so_enxerga_config_do_profile_ativo(contexto):
    assert contexto["valores_noturna"]["url"] == "https://noturna.example.com"
    assert contexto["valores_diurna"]["url"] == "https://diurna.example.com"


# ── log é compartilhado só por profile, entre scripts diferentes ──────────────


@given("múltiplos scripts rodando sob o mesmo profile", target_fixture="contexto")
def dado_multiplos_scripts_sob_mesmo_profile(tmp_path, mocker):
    _fake_platformdirs(tmp_path, mocker)
    perfil.definir_perfil("equipe-noturna")
    return {"tmp_path": tmp_path}


@when("eles geram log")
def quando_eles_geram_log(contexto):
    log_module.passo("evento do script A")  # ex.: scripthub frequencias auditar
    contexto["caminho_a"] = Path(log_module._logger.handlers[0].baseFilename)

    log_module._logger.handlers.clear()  # simula um novo processo `scripthub <outro comando>`
    log_module.passo("evento do script B")  # ex.: scripthub torpedo
    contexto["caminho_b"] = Path(log_module._logger.handlers[0].baseFilename)


@then("todos escrevem no mesmo arquivo de log daquele profile")
def entao_todos_escrevem_no_mesmo_arquivo_de_log(contexto):
    assert contexto["caminho_a"] == contexto["caminho_b"]
    assert contexto["caminho_a"] == contexto["tmp_path"] / "state" / "equipe-noturna" / "scripthub.log"


# ── configuração não lê mais .env ──────────────────────────────────────────────


@given("a versão nova instalada", target_fixture="contexto")
def dado_versao_nova_instalada(tmp_path, mocker):
    _fake_platformdirs(tmp_path, mocker)
    _fake_keyring(mocker)
    return {"tmp_path": tmp_path}


@when("qualquer script carrega configuração")
def quando_script_carrega_configuracao(contexto):
    from scripthub.services import keyring_moodle
    from scripthub.services.config import persistencia

    campo_usuario = Campo(
        chave="moodle_usuario", rotulo="r", tipo="texto", origem="settings", settings_chaves=["moodle", "usuario"]
    )
    campo_senha = Campo(chave="moodle_senha", rotulo="r", tipo="senha", origem="keyring")

    persistencia.persistir("frequencias", [campo_usuario], {"moodle_usuario": "user-freq"})
    persistencia.persistir("torpedo", [campo_usuario], {"moodle_usuario": "user-torpedo"})
    keyring_moodle.definir_senha_moodle("frequencias", "default", "senha-frequencias")
    keyring_moodle.definir_senha_moodle("torpedo", "default", "senha-torpedo")

    contexto["valores_freq"] = persistencia.carregar_valores("frequencias", [campo_usuario, campo_senha])
    contexto["valores_torpedo"] = persistencia.carregar_valores("torpedo", [campo_usuario, campo_senha])


@then(parsers.parse('o usuário do Moodle vem de "{arquivo}"'))
def entao_usuario_moodle_vem_de_settings(contexto, arquivo):
    assert arquivo == "settings.toml"
    assert contexto["valores_freq"]["moodle_usuario"] == "user-freq"
    assert contexto["valores_torpedo"]["moodle_usuario"] == "user-torpedo"


@then("a senha do Moodle vem do keyring do sistema operacional")
def entao_senha_moodle_vem_do_keyring(contexto):
    assert contexto["valores_freq"]["moodle_senha"] == "senha-frequencias"
    assert contexto["valores_torpedo"]["moodle_senha"] == "senha-torpedo"
    # nenhum .env em lugar nenhum — se algum código ainda dependesse dele, o carregamento acima
    # teria levantado ErroConfiguracao por falta de credenciais
    assert not (contexto["tmp_path"] / "config" / "default" / "frequencias" / ".env").exists()


@then("cada script tem sua própria entrada de keyring, sem colisão entre scripts")
def entao_cada_script_tem_propria_entrada_de_keyring(contexto):
    assert contexto["valores_freq"]["moodle_senha"] != contexto["valores_torpedo"]["moodle_senha"]


# ── senha do Moodle no keyring também é isolada por profile ───────────────────


@given("dois profiles diferentes usando o mesmo script", target_fixture="contexto")
def dado_dois_profiles_usando_mesmo_script(tmp_path, mocker):
    _fake_platformdirs(tmp_path, mocker)
    _fake_keyring(mocker)
    return {}


@when("cada profile define sua própria senha do Moodle para esse script")
def quando_cada_profile_define_propria_senha(contexto):
    from scripthub.services import keyring_moodle

    perfil.definir_perfil("equipe-diurna")
    keyring_moodle.definir_senha_moodle("frequencias", perfil.resolver_perfil(), "senha-diurna")

    perfil.definir_perfil("equipe-noturna")
    keyring_moodle.definir_senha_moodle("frequencias", perfil.resolver_perfil(), "senha-noturna")
    contexto["senha_noturna"] = keyring_moodle.obter_senha_moodle("frequencias", perfil.resolver_perfil())

    perfil.definir_perfil("equipe-diurna")
    contexto["senha_diurna"] = keyring_moodle.obter_senha_moodle("frequencias", perfil.resolver_perfil())


@then("cada profile lê de volta só a própria senha, sem vazamento entre profiles")
def entao_cada_profile_le_so_a_propria_senha(contexto):
    assert contexto["senha_diurna"] == "senha-diurna"
    assert contexto["senha_noturna"] == "senha-noturna"


# ── migrate-legacy-config migra sem perda de dados ─────────────────────────────


@given("uma instalação existente no layout antigo, com settings.json, dados/ e .env", target_fixture="contexto")
def dado_instalacao_layout_antigo(tmp_path, mocker):
    _fake_platformdirs(tmp_path, mocker)
    _fake_keyring(mocker)
    from scripthub.services import migracao

    legado_frequencias = tmp_path / "legado" / "frequencias"
    legado_frequencias.mkdir(parents=True)
    caminho_credentials = tmp_path / "em_algum_lugar" / "credentials.json"
    caminho_credentials.parent.mkdir(parents=True)
    caminho_credentials.write_text('{"tipo": "service_account"}', encoding="utf-8")

    (legado_frequencias / "settings.json").write_text(
        json.dumps(
            {
                "moodle": {"urlLogin": "https://x.com/login"},
                "gsheets": {"caminhoJsonCredenciais": str(caminho_credentials)},
            }
        ),
        encoding="utf-8",
    )
    (legado_frequencias / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=segredo\n", encoding="utf-8")

    pasta_dados_legada = tmp_path / "legado" / "relatorios" / "compilar" / "dados"
    pasta_dados_legada.mkdir(parents=True)
    (pasta_dados_legada / "turma1.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    mocker.patch.object(
        migracao,
        "_DOMINIO_RAIZ",
        {
            "frequencias": legado_frequencias,
            "relatorios": tmp_path / "legado" / "relatorios",
            "softskills": tmp_path / "legado" / "softskills",
            "torpedo": tmp_path / "legado" / "torpedo",
        },
    )
    for pasta in migracao._DOMINIO_RAIZ.values():
        pasta.mkdir(parents=True, exist_ok=True)
    mocker.patch.object(
        migracao,
        "_DADOS_LEGADOS",
        {
            "frequencias": [],
            "relatorios": [tmp_path / "legado" / "relatorios" / "compilar" / "dados"],
            "softskills": [],
            "torpedo": [],
        },
    )

    return {"tmp_path": tmp_path, "caminho_credentials": caminho_credentials, "legado_frequencias": legado_frequencias}


@then(parsers.parse('"{origem}" vira "{destino}" válido no novo layout por profile e script'))
def entao_settings_vira_settings_toml(contexto, origem, destino):
    assert contexto["resultado"].exit_code == 0
    assert origem == "settings.json"
    assert destino == "settings.toml"

    novo_settings = contexto["tmp_path"] / "config" / "default" / "frequencias" / "settings.toml"
    dados_migrados = tomllib.loads(novo_settings.read_text(encoding="utf-8"))
    assert dados_migrados["moodle"]["urlLogin"] == "https://x.com/login"
    contexto["dados_migrados"] = dados_migrados

    # nada foi apagado da origem
    assert (contexto["legado_frequencias"] / "settings.json").exists()
    assert (contexto["legado_frequencias"] / ".env").exists()


@then('a pasta "dados/" migra junto')
def entao_pasta_dados_migra_junto(contexto):
    novo_dado = contexto["tmp_path"] / "data" / "default" / "relatorios" / "dados" / "turma1.csv"
    assert novo_dado.read_text(encoding="utf-8") == "a,b\n1,2\n"


@then(parsers.parse('"{variavel}" vai para "{destino}"'))
def entao_variavel_vai_para(contexto, variavel, destino):
    if variavel == "MOODLE_USUARIO":
        assert destino == "settings.toml"
        assert contexto["dados_migrados"]["moodle"]["usuario"] == "user"
    elif variavel == "MOODLE_SENHA":
        assert destino == "keyring"
        from scripthub.services import keyring_moodle

        assert keyring_moodle.obter_senha_moodle("frequencias", "default") == "segredo"
    else:
        raise AssertionError(f"variável não esperada: {variavel!r}")


@then('"credentials.json" permanece no caminho já configurado, sem ser movido')
def entao_credentials_json_permanece_no_caminho(contexto):
    # credentials.json não se move: o caminho salvo continua apontando pro lugar original
    assert contexto["dados_migrados"]["gsheets"]["caminhoJsonCredenciais"] == str(contexto["caminho_credentials"])
    assert contexto["caminho_credentials"].exists()  # o arquivo em si nunca foi tocado


# ── migrate-legacy-config é no-op amigável sem arquivos legados ───────────────


@given("uma instalação já no layout novo, sem arquivos legados", target_fixture="contexto")
def dado_instalacao_layout_novo_sem_arquivos_legados(tmp_path, mocker):
    _fake_platformdirs(tmp_path, mocker)
    from scripthub.services import migracao

    raiz_vazia = {
        "frequencias": tmp_path / "legado" / "frequencias",
        "relatorios": tmp_path / "legado" / "relatorios",
        "softskills": tmp_path / "legado" / "softskills",
        "torpedo": tmp_path / "legado" / "torpedo",
    }
    for pasta in raiz_vazia.values():
        pasta.mkdir(parents=True)
    mocker.patch.object(migracao, "_DOMINIO_RAIZ", raiz_vazia)
    mocker.patch.object(
        migracao, "_DADOS_LEGADOS", {"frequencias": [], "relatorios": [], "softskills": [], "torpedo": []}
    )
    return {"tmp_path": tmp_path}


@then("o comando não faz nada destrutivo")
def entao_comando_nao_faz_nada_destrutivo(contexto):
    assert contexto["resultado"].exit_code == 0
    # nada foi criado no novo layout
    pasta_config = contexto["tmp_path"] / "config"
    assert not pasta_config.exists() or not any(pasta_config.iterdir())
