from scripthub.scripts.frequencias.extrair_frequencias import extrair_todas_frequencias

from .config import Config


def main(config: Config) -> None:
    """Extrai frequências de todas as turmas via HTTP, para uso exclusivo de `compilar`."""
    extrair_todas_frequencias(
        url_login=config.moodle.url_login,
        usuario=config.moodle.usuario,
        senha=config.moodle.senha,
        urls_frequencias=config.moodle.urls_frequencias,
        diretorio_saida=config.diretorio_download,
    )
