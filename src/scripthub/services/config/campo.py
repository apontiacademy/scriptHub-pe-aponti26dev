from dataclasses import dataclass, field
from typing import Literal

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
OrigemCampo = Literal["env", "settings"]


@dataclass
class Campo:
    chave: str
    rotulo: str
    tipo: TipoCampo
    origem: OrigemCampo
    descricao: str = ""
    obrigatorio: bool = True
    env_var: str | None = None
    json_chaves: list[str] = field(default_factory=list)
