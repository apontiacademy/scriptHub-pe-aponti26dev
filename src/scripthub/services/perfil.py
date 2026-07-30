from . import diretorios
from .erros import ErroConfiguracao, ErroUsoCLI

PADRAO = "default"

_NOME_ARQUIVO_MARCADOR = "profile"

_override: str | None = None


def _nome_invalido(nome: str) -> bool:
    return not nome or "/" in nome or "\\" in nome or nome in (".", "..") or nome.lower() == _NOME_ARQUIVO_MARCADOR


def _validar_nome(nome: str) -> None:
    if _nome_invalido(nome):
        raise ErroUsoCLI(
            f"Nome de profile inválido: '{nome}'. Não pode conter '/', '\\', ser '.'/'..', "
            "nem o nome reservado 'Profile'."
        )


def perfil_persistido() -> str:
    caminho = diretorios.caminho_arquivo_perfil()
    if not caminho.exists():
        return PADRAO
    conteudo = caminho.read_text(encoding="utf-8").strip()
    if not conteudo:
        return PADRAO
    if _nome_invalido(conteudo):
        raise ErroConfiguracao(
            f"O arquivo de profile ({caminho}) contém um nome inválido: '{conteudo}'. "
            "Corrija manualmente ou rode `scripthub unset-profile`."
        )
    return conteudo


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
