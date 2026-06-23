import sys
from typing import Annotated

import typer

from .scripts import (
    auditar_frequencias,
    auditar_relatorios,
    auditar_softskills,
    compilacao_de_relatorios,
    torpedo_de_forum,
)
from .services.config import config as config_service, visualizar as visualizar_config
from .services.menu import menu

app = typer.Typer(invoke_without_command=True)


def run():
    app()


@app.callback()
def callback(
    ctx: typer.Context,
    verboso: Annotated[bool, typer.Option("--verboso", "-v", help="Exibir erros verbosos no menu.")] = False,
):
    if ctx.invoked_subcommand is None:
        menu(verboso)


def _carregar_config(fn, nome_script: str):
    try:
        return fn()
    except (FileNotFoundError, ValueError, KeyError) as e:
        typer.echo(f"❌ Configuração inválida para {nome_script}: {e}", err=True)
        typer.echo(f"   Execute: scripthub config -s {nome_script}", err=True)
        raise typer.Exit(1)


# TODO: implementar help
@app.command()
@app.command("f", hidden=True)
def frequencias(
    passo: Annotated[int | None, typer.Option("--passo", "-p", help="Executar um passso específico do script.")] = None,
):
    config = _carregar_config(auditar_frequencias.get_config, "auditar_frequencias")
    executar_script(config, auditar_frequencias.ESCOPOS, passo)


# TODO: implementar help
@app.command()
@app.command("r", hidden=True)
def relatorios(
    modo: Annotated[
        str,
        typer.Argument(help="Escolher se executar o script no modo auditar ou compilar."),
    ],
    passo: Annotated[int | None, typer.Option("--passo", "-p", help="Executar um passso específico do script.")] = None,
):
    match modo:
        case "auditar":
            config = _carregar_config(auditar_relatorios.get_config, "auditar_relatorios")
            executar_script(config, auditar_relatorios.ESCOPOS, passo)
        case "compilar":
            if passo:
                raise ValueError('O modo compilar não aceita "passo".')
            _carregar_config(compilacao_de_relatorios.main, "compilacao_de_relatorios")
        case _:
            raise ValueError('Modo deve ser "auditar" ou "compilar".')


# TODO: implementar help
# TODO: reimplementar utilizando padrões dos scripts anteriores
@app.command()
@app.command("s", hidden=True)
def softskills():
    _carregar_config(auditar_softskills.main, "auditar_softskills")


# TODO: implementar help
# TODO: reimplementar utilizando padrões dos scripts anteriores
@app.command()
@app.command("t", hidden=True)
def torpedo():
    _carregar_config(torpedo_de_forum.main, "torpedo_de_forum")


@app.command()
@app.command("c", hidden=True)
def config(
    script: Annotated[
        str | None,
        typer.Option("--script", "-s", help="Script a configurar (pula a seleção interativa)."),
    ] = None,
    apenas_visualizar: Annotated[
        bool,
        typer.Option("--opcoes", "-o", help="Visualizar o estado das opções sem editar."),
    ] = False,
):
    """Configurar interativamente as opções de um script."""
    if apenas_visualizar:
        visualizar_config(script)
    else:
        config_service(script)


def executar_script(config, escopos, passo: int | None):
    print("=" * 80)
    print("▶ INICIANDO PIPELINE DE AUTOMATIZAÇÃO DE RELATÓRIOS")
    print("=" * 80)
    print()

    if passo is None:
        for escopo in escopos:
            escopo(config)
    elif passo <= 0 or passo >= len(escopos):
        print(
            "  ❌ O passo especificado é maior que a quantidade de passos disponíveis ou é igual o menor a 0.",
            file=sys.stderr,
        )
        print("=" * 80)
        return
    else:
        escopos[passo - 1](config)

    print("=" * 80)
    print("✔ PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
    print("=" * 80)
