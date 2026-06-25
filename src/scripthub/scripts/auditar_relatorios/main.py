import scripthub.scripts.auditar_relatorios.backup as backup
import scripthub.scripts.auditar_relatorios.download_de_relatorios as download_de_relatorios
import scripthub.scripts.auditar_relatorios.integracao_google_sheets as integracao_google_sheets
import scripthub.scripts.auditar_relatorios.middleware_analise_de_relatorios as middleware_analise_de_relatorios

from .config import Config

ESCOPOS = [
    ("EXTRAÇÃO DE RELATÓRIOS (MOODLE)", download_de_relatorios.main),
    ("ANÁLISE PENTE-FINO (MIDDLEWARE)", middleware_analise_de_relatorios.main),
    ("INTEGRAÇÃO (GOOGLE SHEETS)", integracao_google_sheets.main),
    ("BACKUP AUTOMÁTICO (.XLSX)", backup.main),
]


def get_config() -> Config:
    return Config.load()
