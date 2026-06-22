import os
import subprocess
import sys
from pathlib import Path

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


def discover_modules(scripts_folder: Path) -> list[tuple[str, str]]:
    modules = []
    for d in sorted(scripts_folder.iterdir()):
        if not d.is_dir():
            continue
        if not (d / "__init__.py").exists():
            continue
        main_py = d / "main.py"
        if not main_py.exists():
            continue
        desc = read_docstring(main_py)
        modules.append((d.name, desc))
    return modules


def run_module(name: str) -> int:
    result = subprocess.run([sys.executable, "-m", name], check=False, cwd=SCRIPTS_FOLDER)
    return result.returncode


_QUIT = object()


# TODO: implementar modo verboso do menu
def main(verboso: bool) -> None:
    feedback: str | None = None

    while True:
        os.system("clear")
        print(HEADER)
        print()

        if feedback:
            print(feedback)
            print()

        modules = discover_modules(SCRIPTS_FOLDER)
        max_len = max((len(name) for name, _ in modules), default=0)
        choices = []
        for name, desc in modules:
            bracketed = f"[{name}]"
            if desc:
                title = f"{bracketed:<{max_len + 2}}  {desc}"
            else:
                title = bracketed
            choices.append(questionary.Choice(title=title, value=name))
        choices.append(questionary.Separator())
        choices.append(questionary.Choice(title="[ sair ]", value=_QUIT))

        selected = questionary.select(
            "Qual script rodar?",
            choices=choices,
            style=STYLE,
        ).ask()

        if selected is None or selected is _QUIT:
            print("Isso não é um adeus, é um até logo 👋")
            break

        returncode = run_module(selected)
        if returncode == 0:
            feedback = f"✅ {selected} finalizado com sucesso."
        else:
            feedback = f"❌ {selected} finalizado com erro (código {returncode})."
