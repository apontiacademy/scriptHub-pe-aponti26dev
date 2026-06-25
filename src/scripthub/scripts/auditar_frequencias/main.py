import scripthub.scripts.auditar_frequencias.exportar_frequencias as exportar_frequencias
import scripthub.scripts.auditar_frequencias.integracao_google_sheets as integracao_google_sheets

from scripthub.services.escopo import Escopo

from .config import Config

ESCOPOS = [
    Escopo("exportar", "EXPORTAÇÃO DE FREQUÊNCIAS (MOODLE)", exportar_frequencias.main, ("e",)),
    Escopo("integrar", "INTEGRAÇÃO (GOOGLE SHEETS)",         integracao_google_sheets.main, ("i",)),
]


def get_config() -> Config:
    return Config.load()
