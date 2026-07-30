from scripthub.scripts.frequencias.extrair_frequencias import extrair_todas_frequencias

from .config import Config


def main(config: Config) -> None:
    """Extrai frequências de todas as turmas via HTTP.

    O XLSX baixado é um artefato transitório: só serve de entrada pra
    `integracao_google_sheets`, então vive no diretório de cache (não no de
    dados persistentes do domínio, nem num caminho configurável pelo usuário).
    """
    extrair_todas_frequencias(
        url_login=config.moodle.url_login,
        usuario=config.moodle.usuario,
        senha=config.moodle.senha,
        urls_frequencias=config.moodle.urls_frequencias,
        diretorio_saida=config.diretorio_download,
    )
