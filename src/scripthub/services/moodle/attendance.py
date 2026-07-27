import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scripthub.services import log
from scripthub.services.erros import ErroIntegracao

from .sessao import MoodleSessao

_ASSINATURA_ZIP = b"PK\x03\x04"


def _e_xlsx_valido(arquivo: Path) -> bool:
    """XLSX é um ZIP — detecta o formato pela assinatura mágica do arquivo."""
    with arquivo.open("rb") as f:
        return f.read(len(_ASSINATURA_ZIP)) == _ASSINATURA_ZIP


def extrair_frequencia(sessao: MoodleSessao, url: str, nome_turma: str, caminho_saida: Path) -> None:
    """Baixa o XLSX de frequência de uma turma via requisição HTTP (mod/attendance)."""
    log.passo(f"Extraindo frequência: {nome_turma}")
    resp = sessao.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    form = next(
        (
            f
            for f in soup.find_all("form")
            if "/login/" not in f.get("action", "") and re.match(r"mform\d", f.get("id", ""))
        ),
        None,
    )
    if not form:
        raise ErroIntegracao(f"Formulário de exportação não encontrado em {url}")

    data = {}
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
        elif tipo == "button":
            continue
        elif tipo == "checkbox":
            if inp.has_attr("checked"):
                data[name] = inp.get("value", "1")
        else:
            data[name] = inp.get("value", "")

    for select in form.find_all("select"):
        name = select.get("name")
        if not name or select.has_attr("multiple"):
            continue
        opcoes = select.find_all("option")
        if not opcoes:
            continue
        selecionada = next((o for o in opcoes if o.has_attr("selected")), opcoes[0])
        data[name] = selecionada.get("value", "")

    label = form.find("label", string=re.compile(r"observa", re.IGNORECASE))
    if label and label.get("for"):
        inp = form.find("input", {"id": label["for"]})
        if inp and inp.get("name"):
            data[inp["name"]] = inp.get("value", "1")
    else:
        for inp in form.find_all("input", {"type": "checkbox"}):
            if re.search(r"observa", inp.get("id", "") + inp.get("name", ""), re.IGNORECASE):
                if inp.get("name"):
                    data[inp["name"]] = inp.get("value", "1")
                break

    if "format" in data:
        data["format"] = "excel"

    action = form.get("action", url)
    if not action.startswith("http"):
        action = urljoin(url, action)

    arquivo = caminho_saida / f"{nome_turma}.xlsx"
    sessao.baixar(action, arquivo, method="post", data=data)

    if not _e_xlsx_valido(arquivo):
        raise ErroIntegracao(
            f"Resposta do Moodle não é um arquivo Excel válido para {nome_turma} — "
            "o formulário de exportação pode ter mudado"
        )

    log.ok(f"Salvo em: {arquivo}")
