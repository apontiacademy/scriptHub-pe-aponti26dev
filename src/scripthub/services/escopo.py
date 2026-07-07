from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Escopo:
    slug: str
    nome: str
    func: Callable
    aliases: tuple[str, ...] = ()
