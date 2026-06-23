import sys
from typing import Annotated

import typer

from ._i18n import instalar as _instalar_i18n

_instalar_i18n()

from .scripts import (
    auditar_frequencias,
    auditar_relatorios,
    auditar_softskills,
    compilacao_de_relatorios,
    torpedo_de_forum,
)
from .services.config import config as config_service, visualizar as visualizar_config
from .services.menu import menu as _menu

app = typer.Typer(help="Hub de automações para operações do bootcamp Aponti PE.")


def run():
    app()


@app.command("menu")
@app.command("m", hidden=True)
def menu_cmd():
    """Abrir o menu interativo para selecionar e executar um script."""
    _menu()


def _carregar_config(fn, nome_script: str):
    try:
        return fn()
    except (FileNotFoundError, ValueError, KeyError) as e:
        typer.echo(f"❌ Configuração inválida para {nome_script}: {e}", err=True)
        typer.echo(f"   Execute: scripthub config -s {nome_script}", err=True)
        raise typer.Exit(1)


@app.command()
@app.command("f", hidden=True)
def frequencias(
    passo: Annotated[
        int | None,
        typer.Option("--passo", "-p", help="Executar somente o passo N do pipeline (começa em 1)."),
    ] = None,
):
    """Exporta frequências de presença do Moodle para o Google Sheets."""
    config = _carregar_config(auditar_frequencias.get_config, "auditar_frequencias")
    executar_script(config, auditar_frequencias.ESCOPOS, passo)


@app.command()
@app.command("r", hidden=True)
def relatorios(
    modo: Annotated[
        str,
        typer.Argument(help="Modo de execução: 'auditar' (pipeline completo) ou 'compilar' (gerar PDFs)."),
    ],
    passo: Annotated[
        int | None,
        typer.Option("--passo", "-p", help="Executar somente o passo N do pipeline (começa em 1; indisponível no modo 'compilar')."),
    ] = None,
):
    """Processa relatórios no modo 'auditar' (pipeline completo) ou 'compilar' (gerar PDFs)."""
    match modo:
        case "auditar":
            config = _carregar_config(auditar_relatorios.get_config, "auditar_relatorios")
            executar_script(config, auditar_relatorios.ESCOPOS, passo)
        case "compilar":
            if passo:
                raise ValueError('O modo compilar não aceita "passo".')
            compilacao_de_relatorios.main()
        case _:
            raise ValueError('Modo deve ser "auditar" ou "compilar".')


@app.command("ra", hidden=True)
def relatorios_auditar(
    passo: Annotated[
        int | None,
        typer.Option("--passo", "-p", help="Executar somente o passo N do pipeline (começa em 1)."),
    ] = None,
):
    """Alias para 'scripthub relatorios auditar'."""
    config = _carregar_config(auditar_relatorios.get_config, "auditar_relatorios")
    executar_script(config, auditar_relatorios.ESCOPOS, passo)


@app.command("rc", hidden=True)
def relatorios_compilar():
    """Alias para 'scripthub relatorios compilar'."""
    _carregar_config(compilacao_de_relatorios.main, "compilacao_de_relatorios")


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

    try:
        if passo is None:
            for escopo in escopos:
                escopo(config)
        elif passo <= 0 or passo > len(escopos):
            typer.echo(f"  ❌ Passo inválido: deve ser entre 1 e {len(escopos)}.", err=True)
            raise typer.Exit(1)
        else:
            escopos[passo - 1](config)
    except (typer.Exit, SystemExit):
        raise
    except Exception as e:
        typer.echo(f"  ❌ Erro durante execução: {e}", err=True)
        raise typer.Exit(1)

    print()
    print("=" * 80)
    print("✔ PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
    print("=" * 80)
