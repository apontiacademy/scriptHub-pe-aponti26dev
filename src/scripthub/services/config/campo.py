import dataclasses
from dataclasses import dataclass, field
from typing import Any, Literal

TipoCampo = Literal[
    "texto",
    "senha",
    "url",
    "caminho",
    "bool",
    "int",
    "lista_url",
    "dict_str_url",
    "dict_str_lista_url",
]
OrigemCampo = Literal["settings", "keyring"]


@dataclass
class Campo:
    chave: str
    rotulo: str
    tipo: TipoCampo
    origem: OrigemCampo
    descricao: str = ""
    obrigatorio: bool = True
    json_chaves: list[str] = field(default_factory=list)
    depende_de: str | None = None
    caminho_absoluto: bool = False
    scripts: tuple[str, ...] = field(default_factory=tuple)


def resolver_dependencias(campos: list[Campo], valores: dict[str, Any]) -> list[Campo]:
    """Retorna cópias dos campos com `obrigatorio` recalculado: quando `depende_de`
    está definido, o campo passa a ser obrigatório se e somente se o valor do
    campo referenciado for verdadeiro."""
    resolvidos = []
    for campo in campos:
        if campo.depende_de is not None:
            campo = dataclasses.replace(campo, obrigatorio=bool(valores.get(campo.depende_de)))
        resolvidos.append(campo)
    return resolvidos
