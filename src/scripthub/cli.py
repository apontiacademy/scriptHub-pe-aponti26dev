import sys

import typer

from .scripts import auditar_frequencias, auditar_relatorios, auditar_softskills, torpedo_de_forum
from .scripts.menu import menu

app = typer.Typer(invoke_without_command=True)


def run():
    app()


@app.callback()
def callback(
    ctx: typer.Context,
    verboso: bool = typer.Option(False, "--verboso", "-v", help="Exibir erros verbosos."),
):
    ctx.obj = {"verboso": verboso}
    if ctx.invoked_subcommand is None:
        menu(verboso)


# TODO: implementar help
# TODO: implementar verboso
@app.command()
def frequencias(
    ctx: typer.Context,
    passo: int | None = typer.Option(None, "--passo", "-p", help="Executar um passo específico do script."),
):
    # executar_modulo_script_com_ctx(auditar_frequencias, ctx)
    executar_script(auditar_frequencias.CONFIG, auditar_frequencias.ESCOPOS, ctx.obj["verboso"], passo)


# TODO: implementar help
# TODO: implementar verboso
@app.command()
def relatorios(
    ctx: typer.Context,
    passo: int | None = typer.Option(None, "--passo", "-p", help="Executar um passo específico do script."),
):
    # executar_modulo_script_com_ctx(auditar_relatorios, ctx)
    executar_script(auditar_relatorios.CONFIG, auditar_relatorios.ESCOPOS, ctx.obj["verboso"], passo)


# TODO: implementar help
# TODO: implementar verboso
# TODO: reimplementar utilizando padrões dos scripts anteriores
@app.command()
def softskills(ctx: typer.Context):
    auditar_softskills.main(ctx.obj["verboso"])


# TODO: implementar help
# TODO: implementar verboso
# TODO: reimplementar utilizando padrões dos scripts anteriores
@app.command()
def torpedo(ctx: typer.Context):
    torpedo_de_forum.main(ctx.obj["verboso"])


# ALIASES
freq = frequencias
rel = relatorios
soft = softskills
torp = torpedo


def executar_script(config, escopos, verboso: bool, passo: int | None):
    print("=" * 80)
    print("▶ INICIANDO PIPELINE DE AUTOMATIZAÇÃO DE RELATÓRIOS")
    print("=" * 80)
    print()

    if passo is None:
        for escopo in escopos:
            escopo(config, verboso)
    elif passo <= 0 or passo >= len(escopos):
        print(
            "  ❌ O passo especificado é maior que a quantidade de passos disponíveis ou é igual o menor a 0.",
            file=sys.stderr,
        )
        print("=" * 80)
        return
    else:
        escopos[passo - 1](config, verboso)

    print("=" * 80)
    print("✔ PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
    print("=" * 80)
