import scripthub.scripts.auditar_frequencias.exportar_frequencias as exportar_frequencias
import scripthub.scripts.auditar_frequencias.integracao_google_sheets as integracao_google_sheets

from .config import Config

ESCOPOS = [
    ("EXPORTAÇÃO DE FREQUÊNCIAS (MOODLE)", exportar_frequencias.main),
    ("INTEGRAÇÃO (GOOGLE SHEETS)", integracao_google_sheets.main),
]


def get_config() -> Config:
    return Config.load()
