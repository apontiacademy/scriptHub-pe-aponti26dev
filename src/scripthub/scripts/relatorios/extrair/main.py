import scripthub.scripts.relatorios.extrair.download_de_relatorios as download_de_relatorios
from scripthub.services.escopo import Escopo

from .config import Config

ESCOPOS = [
    Escopo("extrair", "EXTRAÇÃO DE RELATÓRIOS (MOODLE)", download_de_relatorios.main, ("e",)),
]


def get_config() -> Config:
    return Config.load()
