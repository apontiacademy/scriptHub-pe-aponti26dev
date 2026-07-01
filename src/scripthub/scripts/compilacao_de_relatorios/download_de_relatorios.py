from pathlib import Path

import questionary

from scripthub.services import log
from scripthub.services.moodle import MoodleSessao, baixar_relatorio

from .config import Config


def _caminho_relatorio(nome_mes: str, diretorio_download: Path, indice: int = 1) -> Path:
    slug = nome_mes.lower().replace(" ", "_")
    return diretorio_download / f"{slug}_{indice}.csv"


def _relatorios_existentes(meses: dict[str, list[str]], diretorio_download: Path) -> dict[str, list[Path]]:
    return {
        nome_mes: [_caminho_relatorio(nome_mes, diretorio_download, i + 1) for i in range(len(urls))]
        for nome_mes, urls in meses.items()
    }


def _todos_relatorios_existem(caminhos: dict[str, list[Path]]) -> bool:
    if not caminhos:
        return False
    return all(caminho.exists() for mes_caminhos in caminhos.values() for caminho in mes_caminhos)


def _perguntar_baixar_novamente() -> bool:
    resposta = questionary.confirm(
        "Relatórios já encontrados em dados/relatorios. Deseja baixá-los novamente?",
        default=False,
    ).ask()
    return resposta is True


def main(config: Config) -> None:
    """Baixa relatórios mensais do Moodle via HTTP."""
    log.secao("DOWNLOAD DE RELATÓRIOS POR MÊS (MOODLE)")

    meses = config.moodle.meses
    diretorio_download = config.moodle.caminho_download

    if not meses:
        raise RuntimeError("Nenhum mês configurado em settings.json (moodle.meses)")

    diretorio_download.mkdir(parents=True, exist_ok=True)

    caminhos = _relatorios_existentes(meses, diretorio_download)
    if _todos_relatorios_existem(caminhos):
        log.passo("Relatórios CSV já existem em dados/relatorios.")
        if not _perguntar_baixar_novamente():
            log.passo("Download ignorado. Usando arquivos existentes.")
            return

    sessao = MoodleSessao(
        url_login=config.moodle.url_login,
        usuario=config.moodle.usuario,
        senha=config.moodle.senha,
    )
    sessao.login()

    for nome_mes, urls in meses.items():
        log.passo(f"Mês: {nome_mes}")
        for indice, url in enumerate(urls, 1):
            log.passo(f"Relatório {indice}/{len(urls)}")
            caminho_saida = _caminho_relatorio(nome_mes, diretorio_download, indice)
            baixar_relatorio(sessao, url, caminho_saida)

    log.ok("Escopo 1 finalizado com sucesso!")
