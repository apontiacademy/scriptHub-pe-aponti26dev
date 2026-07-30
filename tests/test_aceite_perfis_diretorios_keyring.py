"""Testes de aceite da issue #78 — um teste por critério "Given/When/Then" do
corpo da issue (exceto o critério de documentação/README, que não é um
comportamento executável e é conferido manualmente na Task 25 do plano de
implementação). Cada teste é anotado com o Given/When/Then correspondente no
docstring, citado quase literalmente da issue.

Estado esperado nesta fase (RED): todos os testes deste arquivo devem FALHAR,
já que nenhum dos serviços novos (`diretorios`, `perfil`, `keyring_moodle`,
`migracao`) nem os comandos novos da CLI (`set-profile`/`unset-profile`/
`migrate-legacy-config`/`--profile`) existem ainda. A implementação de
`docs/superpowers/plans/2026-07-29-diretorios-perfis-keyring.md` deve fazê-los
passar, um a um, ao longo das Tasks 1-19.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import tomllib
from typer.testing import CliRunner

import scripthub.cli as cli_module
from scripthub.cli import app
from scripthub.services import log as log_module
from scripthub.services import perfil
from scripthub.services.config.campo import Campo

runner = CliRunner()


def _fake_platformdirs(tmp_path, mocker):
    """Troca `platformdirs.PlatformDirs` por um objeto com os 3 diretórios raiz
    apontando para dentro de `tmp_path`, isolando os testes do SO real — o mesmo
    padrão usado em `tests/services/test_diretorios.py` (Task 1 do plano)."""
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


# ── 1. set-profile persiste e é usado nas execuções seguintes ─────────────────


def test_set_profile_persiste_e_execucoes_seguintes_usam_o_novo_profile(tmp_path, mocker):
    """Given nenhum profile persistido (ou um profile diferente já persistido),
    when o usuário roda `scripthub set-profile <nome>`,
    then o profile ativo passa a ser `<nome>` e permanece assim nas execuções
    seguintes (persistido em `<config>/Profile`)."""
    _fake_platformdirs(tmp_path, mocker)
    assert perfil.perfil_persistido() == "default"

    resultado = runner.invoke(app, ["set-profile", "equipe-noturna"])

    assert resultado.exit_code == 0
    assert perfil.perfil_persistido() == "equipe-noturna"
    # "execução seguinte" simulada por uma nova leitura do arquivo persistido, sem override
    assert perfil.resolver_perfil() == "equipe-noturna"
    assert (tmp_path / "config" / "Profile").read_text(encoding="utf-8").strip() == "equipe-noturna"


# ── 2. unset-profile volta para default quando não é default ──────────────────


def test_unset_profile_volta_para_default_quando_profile_ativo_nao_e_default(tmp_path, mocker):
    """Given um profile diferente de `default` está persistido,
    when o usuário roda `scripthub unset-profile`,
    then o profile ativo volta a ser `default`."""
    _fake_platformdirs(tmp_path, mocker)
    runner.invoke(app, ["set-profile", "equipe-noturna"])

    resultado = runner.invoke(app, ["unset-profile"])

    assert resultado.exit_code == 0
    assert perfil.perfil_persistido() == "default"


# ── 3. unset-profile é no-op quando já é default ───────────────────────────────


def test_unset_profile_e_no_op_quando_profile_ativo_ja_e_default(tmp_path, mocker):
    """Given o profile ativo já é `default`,
    when o usuário roda `scripthub unset-profile`,
    then nada muda (no-op)."""
    _fake_platformdirs(tmp_path, mocker)
    assert perfil.perfil_persistido() == "default"

    resultado = runner.invoke(app, ["unset-profile"])

    assert resultado.exit_code == 0
    assert perfil.perfil_persistido() == "default"
    assert not (tmp_path / "config" / "Profile").exists()


# ── 4. --profile é um override pontual, não persiste ───────────────────────────


def test_profile_flag_override_nao_altera_o_persistido(tmp_path, mocker):
    """Given um profile `X` está persistido,
    when o usuário roda qualquer comando com `--profile Y`,
    then a execução usa o profile `Y` sem alterar o valor persistido — a próxima
    execução sem a flag continua usando `X`."""
    _fake_platformdirs(tmp_path, mocker)
    perfil.definir_perfil("equipe-diurna")

    ctx = SimpleNamespace(invoked_subcommand="config")
    cli_module._callback(ctx, versao=False, aliases=False, debug=False, profile="equipe-noturna")
    assert perfil.resolver_perfil() == "equipe-noturna", "a execução com --profile deve usar Y"
    assert perfil.perfil_persistido() == "equipe-diurna", "--profile não deve alterar o persistido"

    # "próxima execução sem a flag": novo processo simulado por limpar o override
    perfil.definir_override(None)
    assert perfil.resolver_perfil() == "equipe-diurna"


# ── 5. dois profiles não vazam config/dados entre si ───────────────────────────


def test_dois_profiles_com_config_propria_nao_vazam_um_para_o_outro(tmp_path, mocker):
    """Given dois profiles diferentes com config/dados próprios para o mesmo
    script, when o usuário alterna entre eles (via `set-profile` ou `--profile`),
    then cada execução só enxerga a config/dados do profile ativo, sem vazamento
    entre profiles."""
    _fake_platformdirs(tmp_path, mocker)
    from scripthub.services.config import persistencia

    campo = Campo(chave="url", rotulo="r", tipo="texto", origem="settings", settings_chaves=["moodle", "urlLogin"])

    perfil.definir_perfil("equipe-diurna")
    persistencia.persistir("frequencias", [campo], {"url": "https://diurna.example.com"})

    perfil.definir_perfil("equipe-noturna")
    persistencia.persistir("frequencias", [campo], {"url": "https://noturna.example.com"})
    valores_noturna = persistencia.carregar_valores("frequencias", [campo])

    perfil.definir_perfil("equipe-diurna")
    valores_diurna = persistencia.carregar_valores("frequencias", [campo])

    assert valores_noturna["url"] == "https://noturna.example.com"
    assert valores_diurna["url"] == "https://diurna.example.com"


# ── 6. log é compartilhado só por profile, entre scripts diferentes ────────────


def test_scripts_diferentes_sob_mesmo_profile_escrevem_no_mesmo_arquivo_de_log(tmp_path, mocker):
    """Given múltiplos scripts rodando sob o mesmo profile,
    when eles geram log,
    then todos escrevem no mesmo arquivo de log daquele profile (state dividido
    só por profile, não por script)."""
    _fake_platformdirs(tmp_path, mocker)
    perfil.definir_perfil("equipe-noturna")

    log_module.passo("evento do script A")  # ex.: scripthub frequencias auditar
    caminho_a = Path(log_module._logger.handlers[0].baseFilename)

    log_module._logger.handlers.clear()  # simula um novo processo `scripthub <outro comando>`
    log_module.passo("evento do script B")  # ex.: scripthub torpedo
    caminho_b = Path(log_module._logger.handlers[0].baseFilename)

    assert caminho_a == caminho_b
    assert caminho_a == tmp_path / "state" / "equipe-noturna" / "scripthub.log"


# ── 7. .env não é mais lido; usuário em settings.toml, senha no keyring por script ──


def test_config_nao_le_mais_dot_env_usuario_em_settings_senha_no_keyring_por_script(tmp_path, mocker):
    """Given a versão nova instalada,
    when qualquer script carrega configuração,
    then `.env` não é mais lido — usuário do Moodle vem de `settings.toml` e a
    senha vem do keyring do SO, com uma entrada de keyring própria por script
    (sem colisão de senha entre scripts diferentes)."""
    _fake_platformdirs(tmp_path, mocker)
    _fake_keyring(mocker)
    from scripthub.services import keyring_moodle
    from scripthub.services.config import persistencia

    campo_usuario = Campo(
        chave="moodle_usuario", rotulo="r", tipo="texto", origem="settings", settings_chaves=["moodle", "usuario"]
    )
    campo_senha = Campo(chave="moodle_senha", rotulo="r", tipo="senha", origem="keyring")

    persistencia.persistir("frequencias", [campo_usuario], {"moodle_usuario": "user-freq"})
    persistencia.persistir("torpedo", [campo_usuario], {"moodle_usuario": "user-torpedo"})
    keyring_moodle.definir_senha_moodle("frequencias", "senha-frequencias")
    keyring_moodle.definir_senha_moodle("torpedo", "senha-torpedo")

    # nenhum .env em lugar nenhum — se algum código ainda dependesse dele, estas
    # duas chamadas levantariam ErroConfiguracao por falta de credenciais
    valores_freq = persistencia.carregar_valores("frequencias", [campo_usuario, campo_senha])
    valores_torpedo = persistencia.carregar_valores("torpedo", [campo_usuario, campo_senha])

    assert valores_freq == {"moodle_usuario": "user-freq", "moodle_senha": "senha-frequencias"}
    assert valores_torpedo == {"moodle_usuario": "user-torpedo", "moodle_senha": "senha-torpedo"}
    assert not (tmp_path / "config" / "default" / "frequencias" / ".env").exists()


# ── 8. migrate-legacy-config migra sem perda de dados; credentials.json não se move ──


def test_migrate_legacy_config_migra_sem_perda_e_nao_move_credentials_json(tmp_path, mocker):
    """Given uma instalação existente no layout antigo (`settings.json`, `dados/`
    e `.env` dentro do diretório do pacote),
    when o usuário roda `scripthub migrate-legacy-config`,
    then a migração ocorre sem perda de dados: `settings.json` vira
    `settings.toml` válido no novo layout por profile/script, `dados/` migra
    junto, `MOODLE_USUARIO` vai para `settings.toml`, `MOODLE_SENHA` vai para o
    keyring, e `credentials.json` permanece no caminho já configurado pelo
    usuário, sem ser movido."""
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

    resultado = runner.invoke(app, ["migrate-legacy-config"])

    assert resultado.exit_code == 0

    novo_settings = tmp_path / "config" / "default" / "frequencias" / "settings.toml"
    dados_migrados = tomllib.loads(novo_settings.read_text(encoding="utf-8"))
    assert dados_migrados["moodle"]["urlLogin"] == "https://x.com/login"
    assert dados_migrados["moodle"]["usuario"] == "user"
    # credentials.json não se move: o caminho salvo continua apontando pro lugar original
    assert dados_migrados["gsheets"]["caminhoJsonCredenciais"] == str(caminho_credentials)
    assert caminho_credentials.exists()  # o arquivo em si nunca foi tocado

    from scripthub.services import keyring_moodle

    assert keyring_moodle.obter_senha_moodle("frequencias") == "segredo"

    novo_dado = tmp_path / "data" / "default" / "relatorios" / "dados" / "turma1.csv"
    assert novo_dado.read_text(encoding="utf-8") == "a,b\n1,2\n"

    # nada foi apagado da origem
    assert (legado_frequencias / "settings.json").exists()
    assert (legado_frequencias / ".env").exists()


# ── 9. migrate-legacy-config é no-op amigável em instalação já no layout novo ──


def test_migrate_legacy_config_e_no_op_amigavel_sem_arquivos_legados(tmp_path, mocker):
    """Given uma instalação já no layout novo (sem arquivos legados),
    when o usuário roda `scripthub migrate-legacy-config`,
    then o comando não faz nada destrutivo (idempotente / no-op amigável)."""
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

    resultado = runner.invoke(app, ["migrate-legacy-config"])

    assert resultado.exit_code == 0
    # nada foi criado no novo layout
    assert not (tmp_path / "config").exists() or not any((tmp_path / "config").iterdir())
