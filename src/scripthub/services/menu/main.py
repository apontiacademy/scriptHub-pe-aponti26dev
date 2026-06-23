import ast
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from scripthub.services import log

import questionary
from questionary import Style

# Encontrar o diretório src/ (raiz do projeto)
root_dir = Path(__file__)
while root_dir.name != "src" and root_dir.parent != root_dir:
    root_dir = root_dir.parent

SCRIPTS_FOLDER = root_dir / "scripthub" / "scripts"

STYLE = Style(
    [
        ("qmark", "fg:#00bfff bold"),
        ("question", "bold"),
        ("answer", "fg:#00bfff bold"),
        ("pointer", "fg:#00bfff bold"),
        ("highlighted", "fg:#00bfff bold"),
        ("selected", "fg:#00bfff"),
        ("separator", "fg:#444444"),
        ("instruction", "fg:#666666"),
        ("text", ""),
    ]
)

HEADER = """\
╔══════════════════════════════════════════╗
║           ScriptHub — Aponti PE          ║
╚══════════════════════════════════════════╝"""


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


def _read_menu_cmd(init_py: Path) -> tuple[str, ...] | None:
    src = init_py.read_text(encoding="utf-8")
    m = re.search(r"^MENU_CMD\s*=\s*(.+)$", src, re.MULTILINE)
    if not m:
        return None
    try:
        return tuple(ast.literal_eval(m.group(1).strip()))
    except (ValueError, SyntaxError):
        return None


def discover_modules(scripts_folder: Path) -> list[tuple[str, tuple[str, ...], str]]:
    modules = []
    for d in sorted(scripts_folder.iterdir()):
        if not d.is_dir() or not (d / "__init__.py").exists():
            continue
        cmd = _read_menu_cmd(d / "__init__.py")
        if cmd is None:
            continue
        desc = read_docstring(d / "main.py") if (d / "main.py").exists() else ""
        modules.append((d.name, cmd, desc))
    return modules


def run_module(cmd: tuple[str, ...]) -> int:
    scripthub_exe = shutil.which("scripthub") or "scripthub"
    result = subprocess.run([scripthub_exe, *cmd], check=False)
    return result.returncode


_QUIT = object()


def main() -> None:
    os.system("clear")
    print(HEADER)
    print()
    print("⚠️  Aviso: o menu interativo está deprecated.")
    print("   Prefira usar os comandos do CLI diretamente (scripthub --help).")
    print()

    modules = discover_modules(SCRIPTS_FOLDER)
    max_len = max((len(" ".join(cmd)) for _, cmd, _ in modules), default=0)
    choices = []
    for name, cmd, desc in modules:
        cmd_str = " ".join(cmd).ljust(max_len)
        title = f"{cmd_str}  {desc}" if desc else cmd_str
        choices.append(questionary.Choice(title=title, value=(name, cmd)))
    choices.append(questionary.Separator())
    choices.append(questionary.Choice(title="sair", value=_QUIT))

    selected = questionary.select(
        "Qual script rodar?",
        choices=choices,
        style=STYLE,
    ).ask()

    if selected is None or selected is _QUIT:
        print("Isso não é um adeus, é um até logo 👋")
        return

    name, cmd = selected

    log.secao(f"Executando: {name}")

    returncode = run_module(cmd)

    print()
    if returncode == 0:
        log.ok(f"{name} finalizado com sucesso.")
    else:
        log.erro(f"{name} finalizado com erro (código {returncode}).")
