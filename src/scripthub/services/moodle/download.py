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


def _baixar_e_validar(
    sessao: MoodleSessao,
    action: str,
    caminho_saida: Path,
    url: str,
    *,
    method: str = "get",
    data: dict[str, str] | None = None,
) -> None:
    resp_download = sessao.baixar(action, caminho_saida, method=method, data=data)
    try:
        _validar_csv(resp_download, url)
    except RuntimeError:
        caminho_saida.unlink(missing_ok=True)
        raise
    log.ok(f"Salvo em: {caminho_saida}")


def _campos_de_form(form) -> dict[str, str]:
    """Coleta os campos de um <form> em um dict nome→valor.

    Inclui todo <input> exceto botões (do tipo submit, só o primeiro é
    incluído; do tipo button, nenhum) e todo <select> (valor da opção
    marcada como selected, ou a primeira opção se nenhuma estiver marcada).
    """
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

    for sel in form.find_all("select"):
        name = sel.get("name")
        if not name:
            continue
        opcao = sel.find("option", selected=True) or sel.find("option")
        data[name] = opcao.get("value", "") if opcao else ""

    return data


def baixar_relatorio(sessao: MoodleSessao, url: str, caminho_saida: Path) -> None:
    """Baixa um relatório via requisição HTTP.

    Tenta, em ordem: link de download direto; formulário com seletor de
    formato de download (`<select name="download">`, ex.: mod/feedback);
    formulário genérico (fallback). Lança RuntimeError se nenhum for encontrado.
    """
    log.passo(f"Acessando relatório: {url}")
    resp = sessao.get(url)  # lança RuntimeError se sessão expirada
    soup = BeautifulSoup(resp.text, "html.parser")
    forms = soup.find_all("form")

    # Caminho 1: link de download direto
    link = soup.find("a", string=re.compile(r"[Dd]ownload"))
    if link and link.get("href"):
        href = link["href"]
        if not href.startswith("http"):
            href = urljoin(url, href)
        _baixar_e_validar(sessao, href, caminho_saida, url)
        return

    # Caminho 2: formulário com seletor de formato de download (ex.: mod/feedback) —
    # identificado pelo <select name="download">, não pela ordem dos forms na
    # página, já que páginas de feedback têm outros forms (edição, filtros, etc.)
    # antes do form de exportação.
    form_download = next(
        (f for f in forms if "/login/" not in f.get("action", "") and f.find("select", {"name": "download"})),
        None,
    )
    if form_download:
        select_download = form_download.find("select", {"name": "download"})
        opcoes = {opt.get("value", "") for opt in select_download.find_all("option")}
        if "csv" not in opcoes:
            raise RuntimeError(
                f"Formulário de exportação em {url} não oferece a opção CSV (opções disponíveis: {sorted(opcoes)})"
            )

        data = _campos_de_form(form_download)
        data["download"] = "csv"

        action = form_download.get("action", url)
        if not action.startswith("http"):
            action = urljoin(url, action)
        method = form_download.get("method", "get").lower()

        _baixar_e_validar(sessao, action, caminho_saida, url, method=method, data=data)
        return

    # Caminho 3: formulário genérico (fallback) — ignora forms que apontem para /login/
    form = next(
        (f for f in forms if "/login/" not in f.get("action", "")),
        None,
    )
    if form:
        data = _campos_de_form(form)

        action = form.get("action", url)
        if not action.startswith("http"):
            action = urljoin(url, action)

        method = form.get("method", "post").lower()
        _baixar_e_validar(sessao, action, caminho_saida, url, method=method, data=data)
        return

    raise RuntimeError(f"Link ou formulário de download não encontrado em {url}")
