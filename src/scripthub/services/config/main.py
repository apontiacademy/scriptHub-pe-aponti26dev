import ast
import dataclasses
import re
from pathlib import Path

import questionary

import scripthub

from .. import log
from ..erros import ErroUsoCLI
from .campo import Campo, resolver_dependencias
from .esquemas import ALIASES_CLI, ESQUEMAS
from .persistencia import _script_dir, carregar_valores, persistir
from .ui import STYLE, exibir_campos, obter_input, selecionar_campos, selecionar_script
from .validacao import validar_campo

SCRIPTS_FOLDER = Path(scripthub.__file__).resolve().parent / "scripts"


def _read_cli_cmd(init_py: Path) -> tuple[str, ...] | None:
    src = init_py.read_text(encoding="utf-8")
    match = re.search(r"^CLI_CMD\s*=\s*(.+)$", src, re.MULTILINE)
    if not match:
        return None
    try:
        return tuple(ast.literal_eval(match.group(1).strip()))
    except (ValueError, SyntaxError):
        return None


def read_docstring(main_py: Path) -> str:
    src = main_py.read_text(encoding="utf-8")
    stripped = src.lstrip()
    for quote in ('"""', "'''"):
        if stripped.startswith(quote):
            rest = stripped[len(quote) :]
            end = rest.find(quote)
            if end != -1:
                lines = rest[:end].strip().splitlines()
                return lines[0] if lines else ""
    return ""


def discover_modules(scripts_folder: Path) -> list[tuple[str, tuple[str, ...], str]]:
    modules = []
    for directory in sorted(scripts_folder.iterdir()):
        if not directory.is_dir() or not (directory / "__init__.py").exists():
            continue
        command = _read_cli_cmd(directory / "__init__.py")
        if command is None:
            continue
        description = read_docstring(directory / "main.py") if (directory / "main.py").exists() else ""
        modules.append((directory.name, command, description))
    return modules


def _tem_pendencias(nome_script: str) -> bool:
    campos = ESQUEMAS[nome_script]
    valores = carregar_valores(nome_script, campos)
    campos = resolver_dependencias(campos, valores)
    return not all(validar_campo(c, valores.get(c.chave))[0] for c in campos)


def _escopar_por_script(campos: list[Campo], script: str | None) -> list[Campo]:
    """Torna não-obrigatório qualquer campo marcado para outro(s) script(s) que
    não o informado — evita que um domínio fique permanentemente `⚠️ pendente`
    para quem só usa um dos scripts que o compõem."""
    if script is None:
        return campos
    return [
        dataclasses.replace(campo, obrigatorio=False) if campo.scripts and script not in campo.scripts else campo
        for campo in campos
    ]


def _priorizar_por_script(campos: list[Campo], script: str | None) -> list[Campo]:
    if script is None:
        return campos

    def prioridade(campo: Campo) -> int:
        if script in campo.scripts:
            return 0
        if not campo.scripts:
            return 1
        return 2

    return sorted(campos, key=prioridade)


def config(nome_script: str | None = None, script: str | None = None) -> None:
    if nome_script is not None:
        nome_script = ALIASES_CLI.get(nome_script, nome_script)
        if nome_script not in ESQUEMAS:
            nomes = ", ".join(sorted(ESQUEMAS.keys()))
            raise ErroUsoCLI(f"Domínio '{nome_script}' não encontrado. Domínios disponíveis: {nomes}")
    else:
        modulos = discover_modules(SCRIPTS_FOLDER)
        modulos_com_esquema = [
            (nome, cmd, desc, _tem_pendencias(nome)) for nome, cmd, desc in modulos if nome in ESQUEMAS
        ]

        if not modulos_com_esquema:
            log.aviso("Nenhum script com configuração disponível foi encontrado.")
            return

        nome_script = selecionar_script(modulos_com_esquema)
        if nome_script is None:
            return

    campos = ESQUEMAS[nome_script]
    valores = carregar_valores(nome_script, campos)

    print()
    campos_resolvidos = _priorizar_por_script(
        _escopar_por_script(resolver_dependencias(campos, valores), script), script
    )
    selecionados = selecionar_campos(campos_resolvidos, valores)

    if not selecionados:
        log.aviso("Nenhum campo selecionado. Nada foi alterado.")
        return

    novos_valores = dict(valores)
    for campo in selecionados:
        if campo.depende_de and not novos_valores.get(campo.depende_de):
            novos_valores[campo.chave] = None
            continue
        campo_efetivo = resolver_dependencias([campo], novos_valores)[0]
        novo = obter_input(campo_efetivo, valores.get(campo.chave))
        novos_valores[campo.chave] = novo

    print()
    persistir(nome_script, campos, novos_valores)
    log.ok(f"Configuração de {nome_script} salva com sucesso!")


def visualizar(nome_script: str | None = None, script: str | None = None) -> None:
    if nome_script is not None:
        nome_script = ALIASES_CLI.get(nome_script, nome_script)
        if nome_script not in ESQUEMAS:
            nomes = ", ".join(sorted(ESQUEMAS.keys()))
            raise ErroUsoCLI(f"Domínio '{nome_script}' não encontrado. Domínios disponíveis: {nomes}")
    else:
        modulos = discover_modules(SCRIPTS_FOLDER)
        modulos_com_esquema = [
            (nome, cmd, desc, _tem_pendencias(nome)) for nome, cmd, desc in modulos if nome in ESQUEMAS
        ]

        if not modulos_com_esquema:
            log.aviso("Nenhum script com configuração disponível foi encontrado.")
            return

        nome_script = selecionar_script(modulos_com_esquema)
        if nome_script is None:
            return

    campos = ESQUEMAS[nome_script]
    valores = carregar_valores(nome_script, campos)

    log.passo(f"Configuração atual de {nome_script}:")
    campos_resolvidos = _priorizar_por_script(
        _escopar_por_script(resolver_dependencias(campos, valores), script), script
    )
    exibir_campos(campos_resolvidos, valores)


def limpar(nome_script: str | None = None) -> None:
    if nome_script is not None:
        nome_script = ALIASES_CLI.get(nome_script, nome_script)
        if nome_script not in ESQUEMAS:
            nomes = ", ".join(sorted(ESQUEMAS.keys()))
            raise ErroUsoCLI(f"Domínio '{nome_script}' não encontrado. Domínios disponíveis: {nomes}")
    else:
        modulos = discover_modules(SCRIPTS_FOLDER)
        modulos_com_esquema = [
            (nome, cmd, desc, _tem_pendencias(nome)) for nome, cmd, desc in modulos if nome in ESQUEMAS
        ]

        if not modulos_com_esquema:
            log.aviso("Nenhum script com configuração disponível foi encontrado.")
            return

        nome_script = selecionar_script(modulos_com_esquema)
        if nome_script is None:
            return

    pasta = _script_dir(nome_script)
    arquivos = [pasta / ".env", pasta / "settings.json"]
    existentes = [a for a in arquivos if a.exists()]

    if not existentes:
        log.aviso(f"Nenhuma configuração encontrada para '{nome_script}'.")
        return

    log.passo("Arquivos que serão removidos:")
    for a in existentes:
        log.passo(str(a))

    if not questionary.confirm("Deseja apagar esses arquivos?", default=False, style=STYLE).ask():
        log.aviso("Operação cancelada.")
        return

    for a in existentes:
        a.unlink()
        log.ok(f"Removido: {a.name}")
    log.ok(f"Configuração de {nome_script} limpa com sucesso!")
