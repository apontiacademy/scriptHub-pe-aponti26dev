import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scripthub.services import log
from scripthub.services.erros import ErroConfiguracao, ErroIntegracao
from scripthub.services.moodle import MoodleSessao

from .config import Config

_ASSINATURA_ZIP = b"PK\x03\x04"


def _e_xlsx_valido(arquivo: Path) -> bool:
    """XLSX é um ZIP — detecta o formato pela assinatura mágica do arquivo."""
    with arquivo.open("rb") as f:
        return f.read(len(_ASSINATURA_ZIP)) == _ASSINATURA_ZIP


def exportar_frequencia(sessao: MoodleSessao, url: str, nome_turma: str, caminho_saida: Path) -> None:
    """Baixa o XLSX de frequência de uma turma via requisição HTTP."""
    log.passo(f"Exportando frequência: {nome_turma}")
    resp = sessao.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # A página tem outros <form> além do de exportação (ex.: o botão de
    # "ativar/desativar edição" que posta para editmode.php) — o mform real
    # do Moodle é identificável pelo id "mformN_..." gerado pelo moodleform
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
            # BeautifulSoup representa o atributo booleano "checked" (sem
            # valor) como string vazia — falsy em Python — então a presença
            # do atributo precisa ser checada com has_attr, não get()
            if inp.has_attr("checked"):
                data[name] = inp.get("value", "1")
        else:
            data[name] = inp.get("value", "")

    # Coleta selects (ex.: grupo, formato) — usa a opção marcada como
    # "selected" ou, na ausência, a primeira opção (default do navegador)
    for select in form.find_all("select"):
        name = select.get("name")
        if not name or select.has_attr("multiple"):
            continue
        opcoes = select.find_all("option")
        if not opcoes:
            continue
        selecionada = next((o for o in opcoes if o.has_attr("selected")), opcoes[0])
        data[name] = selecionada.get("value", "")

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

    # Formato do arquivo exportado é sempre XLSX — força explicitamente em
    # vez de depender da ordem das opções do select no Moodle
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


def main(config: Config) -> None:
    """Exporta frequências de todas as turmas via HTTP."""
    urls_frequencias = config.moodle.urls_frequencias
    caminho_saida = config.moodle.caminho_exportacao

    if not urls_frequencias:
        raise ErroConfiguracao("Nenhuma URL de frequência encontrada no settings.json")

    caminho_saida.mkdir(parents=True, exist_ok=True)

    sessao = MoodleSessao(
        url_login=config.moodle.url_login,
        usuario=config.moodle.usuario,
        senha=config.moodle.senha,
    )
    sessao.login()

    for nome_turma, url in urls_frequencias.items():
        exportar_frequencia(sessao, url, nome_turma, caminho_saida)
