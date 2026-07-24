import scripthub.scripts.frequencias.auditar.extrair_frequencias as extrair_frequencias
import scripthub.scripts.frequencias.auditar.integracao_google_sheets as integracao_google_sheets
from scripthub.services.escopo import Escopo

from .config import Config

ESCOPOS = [
    Escopo("extrair", "EXTRAÇÃO DE FREQUÊNCIAS (MOODLE)", extrair_frequencias.main, ("e",)),
    Escopo("integrar", "INTEGRAÇÃO (GOOGLE SHEETS)", integracao_google_sheets.main, ("i",)),
]


def get_config() -> Config:
    return Config.load()
