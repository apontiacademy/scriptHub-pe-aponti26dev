from pathlib import Path

from scripthub.services import log
from scripthub.services.moodle import MoodleSessao, baixar_relatorio

from .config import Config


def main(config: Config) -> None:
    """Baixa todos os relatórios do Moodle via HTTP."""
    urls_relatorios = config.moodle.urls_relatorios
    diretorio_download = config.moodle.caminho_download_relatorio

    if not urls_relatorios:
        raise RuntimeError("Nenhuma URL de relatório encontrada no settings.json")

    diretorio_download.mkdir(parents=True, exist_ok=True)

    sessao = MoodleSessao(
        url_login=config.moodle.url_login,
        usuario=config.moodle.usuario,
        senha=config.moodle.senha,
    )
    sessao.login()

    for indice, url in enumerate(urls_relatorios, start=1):
        caminho_saida = diretorio_download / f"relatorio{indice}.csv"
        baixar_relatorio(sessao, url, caminho_saida)

    log.ok("Escopo 1 finalizado com sucesso!")
