from scripthub.services.erros import ErroConfiguracao
from scripthub.services.moodle import MoodleSessao, extrair_frequencia

from .config import Config


def main(config: Config) -> None:
    """Extrai frequências de todas as turmas via HTTP, para uso exclusivo de `compilar`."""
    urls_frequencias = config.moodle.urls_frequencias

    if not urls_frequencias:
        raise ErroConfiguracao("Nenhuma URL de frequência encontrada no settings.toml")

    diretorio_download = config.diretorio_download
    diretorio_download.mkdir(parents=True, exist_ok=True)

    sessao = MoodleSessao(
        url_login=config.moodle.url_login,
        usuario=config.moodle.usuario,
        senha=config.moodle.senha,
    )
    sessao.login()

    for nome_turma, url in urls_frequencias.items():
        extrair_frequencia(sessao, url, nome_turma, diretorio_download)
