import scripthub.scripts.auditar_frequencias.exportar_frequencias as exportar_frequencias
import scripthub.scripts.auditar_frequencias.integracao_google_sheets as integracao_google_sheets

from .config import Config

ESCOPOS = [exportar_frequencias.main, integracao_google_sheets.main]


def get_config() -> Config:
    return Config.load()
