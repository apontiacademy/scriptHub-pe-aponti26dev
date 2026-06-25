import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scripthub.services import log
from scripthub.services.moodle import MoodleSessao

from .config import Config


def baixar_relatorio(sessao: MoodleSessao, url: str, caminho_saida: Path) -> None:
    """Baixa um relatório CSV via requisição HTTP."""
    log.passo(f"Acessando relatório: {url}")
    resp = sessao.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Tenta link de download direto primeiro
    link = soup.find("a", string=re.compile(r"[Dd]ownload"))
    if link and link.get("href"):
        href = link["href"]
        if not href.startswith("http"):
            href = urljoin(url, href)
        sessao.baixar(href, caminho_saida)
        log.ok(f"Salvo em: {caminho_saida}")
        return

    # Tenta form com submit button "Download"
    form = soup.find("form")
    if form:
        data = {}
        for inp in form.find_all("input"):
            tipo = inp.get("type", "text").lower()
            name = inp.get("name")
            if not name:
                continue
            if tipo == "submit":
                if re.search(r"[Dd]ownload", inp.get("value", "")):
                    data[name] = inp.get("value", "")
            elif tipo not in ("button",):
                data[name] = inp.get("value", "")

        action = form.get("action", url)
        if not action.startswith("http"):
            action = urljoin(url, action)

        sessao.baixar(action, caminho_saida, method="post", data=data)
        log.ok(f"Salvo em: {caminho_saida}")
        return

    raise RuntimeError(f"Botão ou link de Download não encontrado em {url}")


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
