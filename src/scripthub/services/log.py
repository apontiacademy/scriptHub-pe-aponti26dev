import logging
import sys
from pathlib import Path


def _find_project_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


_log_dir = _find_project_root() / "logs"
_log_dir.mkdir(exist_ok=True)

_script_atual: str = "scripthub"


class _ScriptFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.script = _script_atual  # type: ignore[attr-defined]
        return True


_logger = logging.getLogger("scripthub")
if not _logger.handlers:
    _logger.setLevel(logging.DEBUG)
    _handler = logging.FileHandler(_log_dir / "scripthub.log", encoding="utf-8")
    _handler.setFormatter(
        logging.Formatter(
            "%(asctime)s  %(levelname)-7s  %(script)-24s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    _handler.addFilter(_ScriptFilter())
    _logger.addHandler(_handler)


def set_script(nome: str) -> None:
    global _script_atual
    _script_atual = nome


def secao(titulo: str) -> None:
    print()
    print(f"▶ {titulo}")
    _logger.info("▶ %s", titulo)


def passo(msg: str) -> None:
    print(f"  • {msg}")
    _logger.info("  • %s", msg)


def ok(msg: str) -> None:
    print(f"  ✔ {msg}")
    _logger.info("  ✔ %s", msg)


def erro(msg: str) -> None:
    print(f"  ❌ {msg}", file=sys.stderr)
    _logger.error("  ❌ %s", msg)


def aviso(msg: str) -> None:
    print(f"  ⚠️  {msg}")
    _logger.warning("  ⚠️  %s", msg)
