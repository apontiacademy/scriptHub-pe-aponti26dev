import logging
import sys
from pathlib import Path

from . import diretorios, perfil

_NIVEL_SUCESSO = 25  # entre INFO (20) e WARNING (30)
logging.addLevelName(_NIVEL_SUCESSO, "SUCCESS")

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


def _garantir_handler() -> None:
    if _logger.handlers:
        return
    log_dir = diretorios.caminho_log(perfil.resolver_perfil())
    log_dir.mkdir(parents=True, exist_ok=True)
    _logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_dir / "scripthub.log", encoding="utf-8")
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s  %(levelname)-7s  %(comando)-25s  %(caller)-65s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler.addFilter(_ScriptFilter())
    _logger.addHandler(handler)


def secao(titulo: str) -> None:
    _garantir_handler()
    print()
    print(f"▶ {titulo}")
    _logger.info("▶ %s", titulo)


def passo(msg: str) -> None:
    _garantir_handler()
    print(f"  • {msg}")
    _logger.info("  • %s", msg)


def ok(msg: str) -> None:
    _garantir_handler()
    print(f"  ✔ {msg}")
    _logger.info("  ✔ %s", msg)


def sucesso(msg: str) -> None:
    _garantir_handler()
    print(f"  ✅ {msg}")
    _logger.log(_NIVEL_SUCESSO, "  ✅ %s", msg)


def _painel_erro(msg: str) -> None:
    from rich.console import Console
    from rich.panel import Panel

    Console(stderr=True).print(Panel(msg, border_style="red", title="Erro", title_align="left"))


def erro(msg: str) -> None:
    _garantir_handler()
    _painel_erro(msg)
    _logger.error("  ❌ %s", msg)


def traceback() -> None:
    import traceback as _tb

    from rich.console import Console

    _garantir_handler()
    Console(stderr=True).print_exception(show_locals=False)
    _logger.error(_tb.format_exc())


def aviso(msg: str) -> None:
    _garantir_handler()
    print(f"  ⚠️  {msg}")
    _logger.warning("  ⚠️  %s", msg)
