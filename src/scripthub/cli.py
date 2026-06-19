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


# TODO: implementar help
@app.command()
@app.command("f", hidden=True)
def frequencias(
    passo: Annotated[int | None, typer.Option("--passo", "-p", help="Executar um passso específico do script.")] = None,
):
    executar_script(auditar_frequencias.CONFIG, auditar_frequencias.ESCOPOS, passo)


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
            executar_script(auditar_relatorios.CONFIG, auditar_relatorios.ESCOPOS, passo)
        case "compilar":
            if passo:
                raise ValueError('O modo compilar não aceita "passo".')
            compilacao_de_relatorios.main()
        case _:
            raise ValueError('Modo deve ser "auditar" ou "compilar".')


# TODO: implementar help
# TODO: reimplementar utilizando padrões dos scripts anteriores
@app.command()
@app.command("s", hidden=True)
def softskills():
    auditar_softskills.main()


# TODO: implementar help
# TODO: reimplementar utilizando padrões dos scripts anteriores
@app.command()
@app.command("t", hidden=True)
def torpedo():
    torpedo_de_forum.main()


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
