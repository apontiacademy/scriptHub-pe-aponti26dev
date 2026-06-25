from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Escopo:
    slug: str
    nome: str
    func: Callable
    aliases: tuple[str, ...] = ()
