import sys
from typing import Annotated

import typer

from ._i18n import instalar as _instalar_i18n
from .services import log

_instalar_i18n()

from .scripts import (
    auditar_frequencias,
    auditar_relatorios,
    auditar_softskills,
    compilacao_de_relatorios,
    torpedo_de_forum,
)
from .services.config import config as config_service, limpar as limpar_config, visualizar as visualizar_config
from .services.menu import menu as _menu

app = typer.Typer(
    help="Hub de automações para operações do bootcamp Aponti PE.",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback(invoke_without_command=True)
def _callback(
    ctx: typer.Context,
    aliases: Annotated[
        bool,
        typer.Option("--aliases", "-a", help="Exibir aliases de cada comando."),
    ] = False,
):
    if aliases:
        _ALIASES = [
            ("scripthub frequencias",         "f"),
            ("scripthub relatorios auditar",  "r auditar, ra"),
            ("scripthub relatorios compilar", "r compilar, rc"),
            ("scripthub softskills",          "s"),
            ("scripthub torpedo",             "t"),
            ("scripthub config",              "c"),
            ("scripthub menu",                "m  [depreciado]"),
        ]
        typer.echo("Aliases disponíveis:\n")
        for cmd, alias in _ALIASES:
            typer.echo(f"  {cmd:<34}→  {alias}")
        raise typer.Exit()
    elif ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def run():
    app()


@app.command("menu", hidden=True)
@app.command("m", hidden=True)
def menu_cmd():
    """[DEPRECATED] Menu interativo. Prefira usar os comandos do CLI: scripthub --help"""
    _menu()


def _carregar_config(fn, nome_script: str):
    try:
        return fn()
    except (FileNotFoundError, ValueError, KeyError) as e:
        typer.echo(f"❌ Configuração inválida para {nome_script}: {e}", err=True)
        typer.echo(f"   Execute: scripthub config -s {nome_script}", err=True)
        raise typer.Exit(1)


def _help_passo(escopos) -> str:
    partes = " | ".join(
        f"{e.slug} ({', '.join(e.aliases)})" if e.aliases else e.slug
        for e in escopos
    )
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
                raise ValueError('O modo compilar não aceita "passo".')
            compilacao_de_relatorios.main()
        case _:
            raise ValueError('Modo deve ser "auditar" ou "compilar".')


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
    compilacao_de_relatorios.main()


# TODO: reimplementar utilizando padrões dos scripts anteriores
@app.command()
@app.command("s", hidden=True)
def softskills():
    """Baixa as notas de soft skills do Moodle e envia ao Google Drive."""
    auditar_softskills.main()


# TODO: reimplementar utilizando padrões dos scripts anteriores
@app.command()
@app.command("t", hidden=True)
def torpedo():
    """Posta tópicos em fóruns do Moodle a partir de arquivos Markdown."""
    torpedo_de_forum.main()


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
        log.erro("--opcoes e --limpar não podem ser usados juntos.")
        raise typer.Exit(1)
    if limpar:
        limpar_config(script)
    elif apenas_visualizar:
        visualizar_config(script)
    else:
        config_service(script)


def executar_script(config, escopos, passo: str | None, titulo: str):
    log.secao(titulo)
    total = len(escopos)

    try:
        if passo is None:
            for i, e in enumerate(escopos, 1):
                log.secao(f"PASSO {i}/{total} — {e.nome}")
                e.func(config)
        else:
            match = next(
                ((i + 1, e) for i, e in enumerate(escopos) if passo in (e.slug, *e.aliases)),
                None,
            )
            if match is None:
                disponiveis = " | ".join(
                    f"{e.slug} ({', '.join(e.aliases)})" if e.aliases else e.slug
                    for e in escopos
                )
                log.erro(f"Passo '{passo}' inválido. Disponíveis: {disponiveis}")
                raise typer.Exit(1)
            i, e = match
            log.secao(f"PASSO {i}/{total} — {e.nome}")
            e.func(config)
    except (typer.Exit, SystemExit):
        raise
    except Exception as exc:
        log.erro(f"Erro durante execução: {exc}")
        raise typer.Exit(1)

    log.ok("PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
