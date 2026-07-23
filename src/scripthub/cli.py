from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import Annotated

import typer

from ._i18n import instalar as _instalar_i18n
from .services import log
from .services.erros import ErroConfiguracao, ErroScriptHub, ErroUsoCLI

_instalar_i18n()

try:
    _VERSAO = _pkg_version("scriptHub-pe-aponti26dev")
except PackageNotFoundError:
    _VERSAO = "(versão desconhecida)"

from .scripts import (
    auditar_frequencias,
    auditar_relatorios,
    compilacao_de_relatorios,
    softskills,
    torpedo,
)
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
):
    global _DEBUG
    _DEBUG = debug
    if versao:
        typer.echo(f"scripthub {_VERSAO}")
        raise typer.Exit()
    elif aliases:
        _ALIASES = [
            ("scripthub frequencias", "f"),
            ("scripthub relatorios auditar", "r auditar, ra"),
            ("scripthub relatorios compilar", "r compilar, rc"),
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


def _carregar_config(fn, nome_script: str):
    try:
        return fn()
    except ErroConfiguracao as e:
        if e.dica is None:
            e.dica = f"Execute: scripthub config -s {nome_script}"
        raise
    except KeyError as e:
        raise ErroConfiguracao(
            f"Configuração inválida para {nome_script}: {e}",
            dica=f"Execute: scripthub config -s {nome_script}",
        ) from e


def _help_passo(escopos) -> str:
    partes = " | ".join(f"{e.slug} ({', '.join(e.aliases)})" if e.aliases else e.slug for e in escopos)
    return f"Executar somente um passo do pipeline. Passos: {partes}"


@app.command()
@app.command("f", hidden=True)
def frequencias(
    passo: Annotated[
        str | None,
        typer.Option("--passo", "-p", help=_help_passo(auditar_frequencias.ESCOPOS)),
    ] = None,
):
    """Exporta frequências de presença do Moodle para o Google Sheets."""
    config = _carregar_config(auditar_frequencias.get_config, "auditar_frequencias")
    executar_script(config, auditar_frequencias.ESCOPOS, passo, "AUDITORIA DE FREQUÊNCIAS")


@app.command()
@app.command("r", hidden=True)
def relatorios(
    modo: Annotated[
        str,
        typer.Argument(help="Modo de execução: 'auditar' (pipeline completo) ou 'compilar' (gerar PDFs)."),
    ],
    passo: Annotated[
        str | None,
        typer.Option("--passo", "-p", help=_help_passo(auditar_relatorios.ESCOPOS) + " (apenas no modo 'auditar')"),
    ] = None,
):
    """Processa relatórios no modo 'auditar' (pipeline completo) ou 'compilar' (gerar PDFs)."""
    match modo:
        case "auditar":
            config = _carregar_config(auditar_relatorios.get_config, "auditar_relatorios")
            executar_script(config, auditar_relatorios.ESCOPOS, passo, "AUDITORIA DE RELATÓRIOS")
        case "compilar":
            if passo:
                raise ErroUsoCLI('O modo compilar não aceita "passo"')
            _executar_pipeline_simples(compilacao_de_relatorios.main)
        case _:
            raise ErroUsoCLI('Modo deve ser "auditar" ou "compilar"')


@app.command("ra", hidden=True)
def relatorios_auditar(
    passo: Annotated[
        str | None,
        typer.Option("--passo", "-p", help=_help_passo(auditar_relatorios.ESCOPOS)),
    ] = None,
):
    """Alias para 'scripthub relatorios auditar'."""
    config = _carregar_config(auditar_relatorios.get_config, "auditar_relatorios")
    executar_script(config, auditar_relatorios.ESCOPOS, passo, "AUDITORIA DE RELATÓRIOS")


@app.command("rc", hidden=True)
def relatorios_compilar():
    """Alias para 'scripthub relatorios compilar'."""
    _executar_pipeline_simples(compilacao_de_relatorios.main)


# TODO: reimplementar utilizando padrões dos scripts anteriores
@app.command()
@app.command("s", hidden=True)
def softskills():
    """Baixa as notas de soft skills do Moodle e envia ao Google Drive."""
    _executar_pipeline_simples(softskills.main)


# TODO: reimplementar utilizando padrões dos scripts anteriores
@app.command()
@app.command("t", hidden=True)
def torpedo():
    """Posta tópicos em fóruns do Moodle a partir de arquivos Markdown."""
    _executar_pipeline_simples(torpedo.main)


@app.command()
@app.command("c", hidden=True)
def config(
    script: Annotated[
        str | None,
        typer.Option("--script", "-s", help="Script a configurar (pula a seleção interativa)."),
    ] = None,
    apenas_visualizar: Annotated[
        bool,
        typer.Option("--opcoes", "-o", help="Apenas visualizar as opções sem editar."),
    ] = False,
    limpar: Annotated[
        bool,
        typer.Option("--limpar", "-l", help="Limpar a configuração do script."),
    ] = False,
):
    """Configurar interativamente as opções de um script."""
    if apenas_visualizar and limpar:
        raise ErroUsoCLI("--opcoes e --limpar não podem ser usados juntos")
    if limpar:
        limpar_config(script)
    elif apenas_visualizar:
        visualizar_config(script)
    else:
        config_service(script)


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
