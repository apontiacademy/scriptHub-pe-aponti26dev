from . import diretorios
from .erros import ErroUsoCLI

PADRAO = "default"

_override: str | None = None


def _validar_nome(nome: str) -> None:
    if not nome or "/" in nome or "\\" in nome or nome in (".", ".."):
        raise ErroUsoCLI(f"Nome de profile inválido: '{nome}'. Não pode conter '/', '\\', nem ser '.'/'..'.")


def perfil_persistido() -> str:
    caminho = diretorios.caminho_arquivo_perfil()
    if not caminho.exists():
        return PADRAO
    conteudo = caminho.read_text(encoding="utf-8").strip()
    return conteudo or PADRAO


def definir_perfil(nome: str) -> None:
    _validar_nome(nome)
    caminho = diretorios.caminho_arquivo_perfil()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(nome, encoding="utf-8")


def remover_perfil() -> None:
    caminho = diretorios.caminho_arquivo_perfil()
    if caminho.exists():
        caminho.unlink()


def definir_override(nome: str | None) -> None:
    global _override
    if nome is not None:
        _validar_nome(nome)
    _override = nome


def resolver_perfil() -> str:
    if _override is not None:
        return _override
    return perfil_persistido()
