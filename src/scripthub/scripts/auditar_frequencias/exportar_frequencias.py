import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scripthub.services import log
from scripthub.services.moodle import MoodleSessao

from .config import Config


def exportar_frequencia(sessao: MoodleSessao, url: str, nome_turma: str, caminho_saida: Path) -> None:
    """Baixa o XLSX de frequência de uma turma via requisição HTTP."""
    log.passo(f"Exportando frequência: {nome_turma}")
    resp = sessao.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    form = next(
        (f for f in soup.find_all("form") if "/login/" not in f.get("action", "")),
        None,
    )
    if not form:
        raise RuntimeError(f"Formulário de exportação não encontrado em {url}")

    # Coleta campos hidden/checkbox e o primeiro submit
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
            if inp.get("checked"):
                data[name] = inp.get("value", "1")
        else:
            data[name] = inp.get("value", "")

    # Marca o checkbox "Observa" explicitamente
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

    action = form.get("action", url)
    if not action.startswith("http"):
        action = urljoin(url, action)

    arquivo = caminho_saida / f"{nome_turma}.xlsx"
    sessao.baixar(action, arquivo, method="post", data=data)
    log.ok(f"Salvo em: {arquivo}")


def main(config: Config) -> None:
    """Exporta frequências de todas as turmas via HTTP."""
    urls_frequencias = config.moodle.urls_frequencias
    caminho_saida = config.moodle.caminho_exportacao

    if not urls_frequencias:
        raise RuntimeError("Nenhuma URL de frequência encontrada no settings.json")

    caminho_saida.mkdir(parents=True, exist_ok=True)

    sessao = MoodleSessao(
        url_login=config.moodle.url_login,
        usuario=config.moodle.usuario,
        senha=config.moodle.senha,
    )
    sessao.login()

    for nome_turma, url in urls_frequencias.items():
        exportar_frequencia(sessao, url, nome_turma, caminho_saida)

    log.ok("Escopo 1 finalizado com sucesso!")
