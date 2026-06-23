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

_comando_atual: str = " ".join(sys.argv[1:]) or "scripthub"
_LOG_FILE = Path(__file__).resolve()
_PACKAGE_ROOT = _LOG_FILE.parent.parent  # src/scripthub/


class _ScriptFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.comando = _comando_atual  # type: ignore[attr-defined]
        frame = sys._getframe()
        caller = "?"
        while frame is not None:
            fpath = Path(frame.f_code.co_filename).resolve()
            mod = frame.f_globals.get("__name__", "")
            if fpath != _LOG_FILE and mod != "logging":
                try:
                    rel = fpath.relative_to(_PACKAGE_ROOT)
                    module_path = ".".join(rel.with_suffix("").parts)
                    caller = f".{module_path}:{frame.f_code.co_name}"
                except ValueError:
                    caller = f"{fpath.name}:{frame.f_code.co_name}"
                break
            frame = frame.f_back
        record.caller = caller  # type: ignore[attr-defined]
        return True


_logger = logging.getLogger("scripthub")
if not _logger.handlers:
    _logger.setLevel(logging.DEBUG)
    _handler = logging.FileHandler(_log_dir / "scripthub.log", encoding="utf-8")
    _handler.setFormatter(
        logging.Formatter(
            "%(asctime)s  %(levelname)-7s  %(comando)-25s  %(caller)-65s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    _handler.addFilter(_ScriptFilter())
    _logger.addHandler(_handler)


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
