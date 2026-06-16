import subprocess
import sys
from pathlib import Path

import questionary

ROOT = Path(__file__).parent


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
        modules = discover_modules(ROOT)
        max_len = max((len(name) for name, _ in modules), default=0)
        choices = []
        for name, desc in modules:
            title = f"{name:<{max_len}}  —  {desc}" if desc else name
            choices.append(questionary.Choice(title=title, value=name))
        choices.append(questionary.Separator())
        choices.append(questionary.Choice(title="Sair", value=_QUIT))

        selected = questionary.select("Qual script rodar?", choices=choices).ask()

        if selected is None or selected is _QUIT:
            break

        run_module(selected)


if __name__ == "__main__":
    main()
