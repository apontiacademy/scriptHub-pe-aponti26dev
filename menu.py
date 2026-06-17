import os
import subprocess
import sys
from pathlib import Path

import questionary
from questionary import Style

ROOT = Path(__file__).parent

STYLE = Style([
    ("qmark",        "fg:#00bfff bold"),
    ("question",     "bold"),
    ("answer",       "fg:#00bfff bold"),
    ("pointer",      "fg:#00bfff bold"),
    ("highlighted",  "fg:#00bfff bold"),
    ("selected",     "fg:#00bfff"),
    ("separator",    "fg:#444444"),
    ("instruction",  "fg:#666666"),
    ("text",         ""),
])

HEADER = """\
╔══════════════════════════════════════════╗
║           ScriptHub — Aponti PE          ║
╚══════════════════════════════════════════╝"""


def read_docstring(main_py: Path) -> str:
    src = main_py.read_text(encoding="utf-8")
    stripped = src.lstrip()
    for quote in ('"""', "'''"):
        if stripped.startswith(quote):
            rest = stripped[len(quote):]
            end = rest.find(quote)
            if end != -1:
                lines = rest[:end].strip().splitlines()
                return lines[0] if lines else ""
    return ""


def discover_modules(root: Path) -> list[tuple[str, str]]:
    modules = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        if not (d / "__init__.py").exists():
            continue
        main_py = d / "__main__.py"
        if not main_py.exists():
            continue
        desc = read_docstring(main_py)
        modules.append((d.name, desc))
    return modules


def run_module(name: str) -> None:
    subprocess.run([sys.executable, "-m", name], check=False, cwd=ROOT)


_QUIT = object()


def main() -> None:
    while True:
        os.system("clear")
        print(HEADER)
        print()

        modules = discover_modules(ROOT)
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
            os.system("clear")
            break

        run_module(selected)


if __name__ == "__main__":
    main()
