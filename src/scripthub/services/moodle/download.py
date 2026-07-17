from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scripthub.services import log

from .sessao import MoodleSessao


def _validar_csv(resp: requests.Response, url: str) -> None:
    content_type = resp.headers.get("Content-Type", "")
    if "csv" not in content_type.lower():
        raise RuntimeError(
            f"Resposta inesperada ({content_type or 'sem Content-Type'}) ao baixar relatório de {url} — esperado CSV"
        )


def baixar_relatorio(sessao: MoodleSessao, url: str, caminho_saida: Path) -> None:
    """Baixa um relatório via requisição HTTP.

    Tenta, em ordem: link de download direto; formulário com seletor de
    formato de download (`<select name="download">`, ex.: mod/feedback);
    formulário genérico (fallback). Lança RuntimeError se nenhum for encontrado.
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
        resp_download = sessao.baixar(href, caminho_saida)
        _validar_csv(resp_download, url)
        log.ok(f"Salvo em: {caminho_saida}")
        return

    # Caminho 2: formulário com seletor de formato de download (ex.: mod/feedback) —
    # identificado pelo <select name="download">, não pela ordem dos forms na
    # página, já que páginas de feedback têm outros forms (edição, filtros, etc.)
    # antes do form de exportação.
    form_download = next(
        (f for f in soup.find_all("form") if f.find("select", {"name": "download"})),
        None,
    )
    if form_download:
        data: dict[str, str] = {}
        for inp in form_download.find_all("input"):
            name = inp.get("name")
            if name:
                data[name] = inp.get("value", "")
        data["download"] = "csv"

        action = form_download.get("action", url)
        if not action.startswith("http"):
            action = urljoin(url, action)
        method = form_download.get("method", "get").lower()

        resp_download = sessao.baixar(action, caminho_saida, method=method, data=data)
        _validar_csv(resp_download, url)
        log.ok(f"Salvo em: {caminho_saida}")
        return

    # Caminho 3: formulário genérico (fallback) — ignora forms que apontem para /login/
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

        resp_download = sessao.baixar(action, caminho_saida, method="post", data=data)
        _validar_csv(resp_download, url)
        log.ok(f"Salvo em: {caminho_saida}")
        return

    raise RuntimeError(f"Link ou formulário de download não encontrado em {url}")
