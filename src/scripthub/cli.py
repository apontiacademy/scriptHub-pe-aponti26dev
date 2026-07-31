from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import Annotated

import typer

from ._i18n import instalar as _instalar_i18n
from .services import log, migracao, perfil
from .services.erros import ErroConfiguracao, ErroScriptHub, ErroUsoCLI

_instalar_i18n()

try:
    _VERSAO = _pkg_version("scriptHub-pe-aponti26dev")
except PackageNotFoundError:
    _VERSAO = "(versão desconhecida)"

from .scripts import softskills, torpedo
from .scripts.frequencias import auditar as frequencias_auditar_script
from .scripts.frequencias import compilar as frequencias_compilar_script
from .scripts.frequencias import extrair as frequencias_extrair_script
from .scripts.relatorios import compilar as relatorios_compilar_script
from .scripts.relatorios import extrair as relatorios_extrair_script
from .services.config import config as config_service
from .services.config import limpar as limpar_config
from .services.config import visualizar as visualizar_config

app = typer.Typer(
    help="Hub de automações para operações do bootcamp Aponti PE.",
    context_settings={"help_option_names": ["-h", "--help"]},
)

_DEBUG = False


@app.callback(invoke_without_command=True)
def _callback(
    ctx: typer.Context,
    versao: Annotated[
        bool,
        typer.Option("--version", "-V", help="Exibir a versão instalada.", is_eager=True),
    ] = False,
    aliases: Annotated[
        bool,
        typer.Option("--aliases", "-a", help="Exibir aliases de cada comando."),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Exibir traceback completo em erros inesperados (código de saída 1)."),
    ] = False,
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="Usar este profile só nesta execução, sem persistir."),
    ] = None,
):
    global _DEBUG
    _DEBUG = debug
    perfil.definir_override(profile)
    if versao:
        typer.echo(f"scripthub {_VERSAO}")
        raise typer.Exit()
    elif aliases:
        _ALIASES = [
            ("scripthub relatorios compilar", "r compilar, relatorios c, r c"),
            ("scripthub relatorios extrair", "r extrair, relatorios e, r e"),
            ("scripthub frequencias auditar", "f auditar, frequencias a, f a"),
            ("scripthub frequencias compilar", "f compilar, frequencias c, f c"),
            ("scripthub frequencias extrair", "f extrair, frequencias e, f e"),
            ("scripthub softskills", "s"),
            ("scripthub torpedo", "t"),
            ("scripthub config", "c"),
        ]
        typer.echo("Aliases disponíveis:\n")
        for cmd, alias in _ALIASES:
            typer.echo(f"  {cmd:<34}→  {alias}")
        raise typer.Exit()
    elif ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def _executar_com_tratamento_global(fn) -> None:
    try:
        fn()
    except ErroScriptHub as exc:
        log.erro(f"{str(exc).rstrip('.')}. Código de saída: {exc.codigo_saida}")
        if exc.dica:
            log.passo(exc.dica)
        raise SystemExit(exc.codigo_saida) from exc
    except Exception as exc:
        log.erro(f"Erro inesperado: {str(exc).rstrip('.')}. Código de saída: 1")
        if _DEBUG:
            log.traceback()
        raise SystemExit(1) from exc


def run():
    _executar_com_tratamento_global(app)


def _carregar_config(fn, nome_dominio: str):
    try:
        return fn()
    except ErroConfiguracao as e:
        if e.dica is None:
            e.dica = f"Execute: scripthub config {nome_dominio}"
        raise
    except KeyError as e:
        raise ErroConfiguracao(
            f"Configuração inválida para {nome_dominio}: {e}",
            dica=f"Execute: scripthub config {nome_dominio}",
        ) from e


def _help_passo(escopos) -> str:
    partes = " | ".join(f"{e.slug} ({', '.join(e.aliases)})" if e.aliases else e.slug for e in escopos)
    return f"Executar somente um passo do pipeline. Passos: {partes}"


def executar_script(config, escopos, passo: str | None, titulo: str):
    log.secao(titulo)
    total = len(escopos)

    match = None
    if passo is not None:
        match = next(
            ((i + 1, e) for i, e in enumerate(escopos) if passo in (e.slug, *e.aliases)),
            None,
        )
        if match is None:
            disponiveis = " | ".join(f"{e.slug} ({', '.join(e.aliases)})" if e.aliases else e.slug for e in escopos)
            raise ErroUsoCLI(f"Passo '{passo}' inválido. Disponíveis: {disponiveis}")

    if passo is None:
        for i, e in enumerate(escopos, 1):
            log.secao(f"PASSO {i}/{total} — {e.nome}")
            e.func(config)
    else:
        i, e = match
        log.secao(f"PASSO {i}/{total} — {e.nome}")
        e.func(config)

    log.sucesso("Script finalizado com sucesso. Código de saída: 0")


def _executar_pipeline_simples(fn) -> None:
    fn()
    log.sucesso("Script finalizado com sucesso. Código de saída: 0")


# --- relatorios: subapp com 2 scripts internos (compilar/extrair) ---

relatorios_app = typer.Typer(help="Processa relatórios do Moodle: extração ou compilação de PDFs.")
app.add_typer(relatorios_app, name="relatorios")
app.add_typer(relatorios_app, name="r", hidden=True)


@relatorios_app.command("compilar")
@relatorios_app.command("c", hidden=True)
def relatorios_compilar():
    """Baixa os relatórios mensais e compila um PDF por aluno."""
    _executar_pipeline_simples(relatorios_compilar_script.main)


@relatorios_app.command("extrair")
@relatorios_app.command("e", hidden=True)
def relatorios_extrair():
    """Baixa os relatórios do Moodle."""
    config = _carregar_config(relatorios_extrair_script.get_config, "relatorios")
    executar_script(config, relatorios_extrair_script.ESCOPOS, "extrair", "EXTRAÇÃO DE RELATÓRIOS")


# --- frequencias: subapp com 3 comandos (auditar/extrair/compilar), mesmo padrão de relatorios ---

frequencias_app = typer.Typer(help="Processa frequências do Moodle: auditoria completa ou compilação de atas em PDF.")
app.add_typer(frequencias_app, name="frequencias")
app.add_typer(frequencias_app, name="f", hidden=True)


@frequencias_app.command("auditar")
@frequencias_app.command("a", hidden=True)
def frequencias_auditar(
    passo: Annotated[
        str | None,
        typer.Option("--passo", "-p", help=_help_passo(frequencias_auditar_script.ESCOPOS)),
    ] = None,
):
    """Pipeline completo de auditoria de frequências (extração, integração)."""
    config = _carregar_config(frequencias_auditar_script.get_config, "frequencias")
    executar_script(config, frequencias_auditar_script.ESCOPOS, passo, "AUDITORIA DE FREQUÊNCIAS")


@frequencias_app.command("extrair")
@frequencias_app.command("e", hidden=True)
def frequencias_extrair():
    """Baixa as frequências do Moodle (equivalente a `auditar --passo extrair`)."""
    config = _carregar_config(frequencias_extrair_script.get_config, "frequencias")
    executar_script(config, frequencias_extrair_script.ESCOPOS, "extrair", "EXTRAÇÃO DE FREQUÊNCIAS")


@frequencias_app.command("compilar")
@frequencias_app.command("c", hidden=True)
def frequencias_compilar(
    passo: Annotated[
        str | None,
        typer.Option("--passo", "-p", help=_help_passo(frequencias_compilar_script.ESCOPOS)),
    ] = None,
):
    """Extrai as frequências e compila uma ata em PDF por turma."""
    config = _carregar_config(frequencias_compilar_script.get_config, "frequencias")
    executar_script(config, frequencias_compilar_script.ESCOPOS, passo, "COMPILAÇÃO DE ATAS DE FREQUÊNCIA")


# --- softskills / torpedo: subapps de script único (callback direto) ---


softskills_app = typer.Typer(
    help="Baixa as notas de soft skills do Moodle e envia ao Google Drive.",
    invoke_without_command=True,
)
app.add_typer(softskills_app, name="softskills")
app.add_typer(softskills_app, name="s", hidden=True)


# TODO: reimplementar utilizando padrões dos scripts anteriores
@softskills_app.callback(invoke_without_command=True)
def _softskills_callback(ctx: typer.Context):
    if ctx.invoked_subcommand is not None:
        return
    _executar_pipeline_simples(softskills.main)


torpedo_app = typer.Typer(
    help="Posta tópicos em fóruns do Moodle a partir de arquivos Markdown.",
    invoke_without_command=True,
)
app.add_typer(torpedo_app, name="torpedo")
app.add_typer(torpedo_app, name="t", hidden=True)


# TODO: reimplementar utilizando padrões dos scripts anteriores
@torpedo_app.callback(invoke_without_command=True)
def _torpedo_callback(ctx: typer.Context):
    if ctx.invoked_subcommand is not None:
        return
    _executar_pipeline_simples(torpedo.main)


# --- profile ---


@app.command("set-profile")
def set_profile(
    nome: Annotated[str, typer.Argument(help="Nome do profile a ativar.")],
):
    """Define o profile ativo persistido (usado por todos os comandos até ser trocado de novo)."""
    perfil.definir_perfil(nome)
    log.ok(f"Profile ativo definido como '{nome}'.")


@app.command("unset-profile")
def unset_profile():
    """Volta o profile ativo persistido para 'default' (não faz nada se já for 'default')."""
    if perfil.perfil_persistido() == perfil.PADRAO:
        log.aviso(f"O profile ativo já é '{perfil.PADRAO}'; nada a fazer.")
        return
    perfil.remover_perfil()
    log.ok(f"Profile ativo voltou a ser '{perfil.PADRAO}'.")


@app.command("migrate-legacy-config", deprecated=True)
def migrate_legacy_config():
    """[DEPRECIADO] Migra settings.json/.env/dados do layout antigo (dentro do pacote instalado)
    para o novo layout (diretórios do SO + keyring). Será removido numa atualização futura."""
    migracao.migrar_configuracao_legada()


# --- config ---


@app.command()
@app.command("c", hidden=True)
def config(
    dominio: Annotated[
        str | None,
        typer.Argument(help="Domínio a configurar (pula a seleção interativa)."),
    ] = None,
    script: Annotated[
        str | None,
        typer.Option("--script", "-s", help="Script interno do domínio: prioriza esses campos na edição/visualização."),
    ] = None,
    apenas_visualizar: Annotated[
        bool,
        typer.Option("--opcoes", "-o", help="Apenas visualizar as opções sem editar."),
    ] = False,
    limpar: Annotated[
        bool,
        typer.Option("--limpar", "-l", help="Limpar a configuração do domínio."),
    ] = False,
):
    """Configurar interativamente as opções de um domínio."""
    if apenas_visualizar and limpar:
        raise ErroUsoCLI("--opcoes e --limpar não podem ser usados juntos")
    if limpar:
        limpar_config(dominio)
    elif apenas_visualizar:
        visualizar_config(dominio, script)
    else:
        config_service(dominio, script)
