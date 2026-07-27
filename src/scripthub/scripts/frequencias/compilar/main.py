import scripthub.scripts.frequencias.compilar.extrair_frequencias as extrair_frequencias
import scripthub.scripts.frequencias.compilar.gerar_atas as gerar_atas
from scripthub.services.escopo import Escopo

from .config import Config

ESCOPOS = [
    Escopo("extrair", "EXTRAÇÃO DE FREQUÊNCIAS (MOODLE)", extrair_frequencias.main, ("e",)),
    Escopo("gerar", "GERAÇÃO DE ATAS EM PDF", gerar_atas.main, ("g",)),
]


def get_config() -> Config:
    return Config.load()
