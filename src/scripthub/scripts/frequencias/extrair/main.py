import scripthub.scripts.frequencias.extrair.extrair_frequencias as extrair_frequencias
from scripthub.services.escopo import Escopo

from .config import Config

ESCOPOS = [
    Escopo("extrair", "EXTRAÇÃO DE FREQUÊNCIAS (MOODLE)", extrair_frequencias.main, ("e",)),
]


def get_config() -> Config:
    return Config.load()
