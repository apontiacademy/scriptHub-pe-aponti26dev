import scripthub.scripts.auditar_relatorios.backup as backup
import scripthub.scripts.auditar_relatorios.download_de_relatorios as download_de_relatorios
import scripthub.scripts.auditar_relatorios.integracao_google_sheets as integracao_google_sheets
import scripthub.scripts.auditar_relatorios.middleware_analise_de_relatorios as middleware_analise_de_relatorios

from scripthub.services.escopo import Escopo

from .config import Config

ESCOPOS = [
    Escopo("extrair",  "EXTRAÇÃO DE RELATÓRIOS (MOODLE)",  download_de_relatorios.main,           ("e",)),
    Escopo("analisar", "ANÁLISE PENTE-FINO (MIDDLEWARE)",   middleware_analise_de_relatorios.main, ("a",)),
    Escopo("integrar", "INTEGRAÇÃO (GOOGLE SHEETS)",        integracao_google_sheets.main,         ("i",)),
    Escopo("salvar",   "BACKUP AUTOMÁTICO (.XLSX)",         backup.main,                           ("s",)),
]


def get_config() -> Config:
    return Config.load()
