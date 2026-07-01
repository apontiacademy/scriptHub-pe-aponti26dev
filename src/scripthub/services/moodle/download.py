from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scripthub.services import log

from .sessao import MoodleSessao


def baixar_relatorio(sessao: MoodleSessao, url: str, caminho_saida: Path) -> None:
    """Baixa um relatório via requisição HTTP.

    Tenta primeiro um link de download direto; cai no envio do formulário
    caso não exista link. Lança RuntimeError se não encontrar nem um nem outro.
    """
    log.passo(f"Acessando relatório: {url}")
    resp = sessao.get(url)  # lança RuntimeError se sessão expirada
    soup = BeautifulSoup(resp.text, "html.parser")

    # Caminho 1: link de download direto
    link = soup.find("a", string=re.compile(r"[Dd]ownload"))
    if link and link.get("href"):
        href = link["href"]
        if not href.startswith("http"):
            href = urljoin(url, href)
        sessao.baixar(href, caminho_saida)
        log.ok(f"Salvo em: {caminho_saida}")
        return

    # Caminho 2: formulário — ignora forms que apontem para /login/
    form = next(
        (f for f in soup.find_all("form") if "/login/" not in f.get("action", "")),
        None,
    )
    if form:
        data: dict[str, str] = {}
        submit_adicionado = False
        for inp in form.find_all("input"):
            tipo = inp.get("type", "text").lower()
            name = inp.get("name")
            if not name:
                continue
            if tipo == "submit":
                if not submit_adicionado:
                    data[name] = inp.get("value", "")
                    submit_adicionado = True
            elif tipo != "button":
                data[name] = inp.get("value", "")

        action = form.get("action", url)
        if not action.startswith("http"):
            action = urljoin(url, action)

        sessao.baixar(action, caminho_saida, method="post", data=data)
        log.ok(f"Salvo em: {caminho_saida}")
        return

    raise RuntimeError(f"Link ou formulário de download não encontrado em {url}")
