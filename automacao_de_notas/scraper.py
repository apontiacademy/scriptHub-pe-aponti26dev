import csv as csv_mod
import os
import re
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import Page

BASE_DIR = Path(__file__).resolve().parent

# Objeto de relação das turmas FAP 2026 — metadados fixos
TURMAS_RELACAO: list[dict] = [
    {
        "nome_moodle": "Testes de Software - Turma 01",
        "turma": "01",
        "tipo": "Testes de Software",
        "dias": "Segunda e Quarta",
        "horario": "09:00 às 12:00",
        "professor": "Kathlyn Letícia",
    },
    {
        "nome_moodle": "DevOps - Turma 2",
        "turma": "02",
        "tipo": "DevOps",
        "dias": "Segunda e Quarta",
        "horario": "14:00 às 17:00",
        "professor": "Bruno Álexys",
    },
    {
        "nome_moodle": "Análise de Dados - Turma 3",
        "turma": "03",
        "tipo": "Análise de Dados",
        "dias": "Segunda e Quarta",
        "horario": "18:00 às 21:00",
        "professor": "Danilo Cavalcanti",
    },
    {
        "nome_moodle": "Testes de Software - Turma 4",
        "turma": "04",
        "tipo": "Testes de Software",
        "dias": "Terça e Quinta",
        "horario": "09:00 às 12:00",
        "professor": "Alison Matheus",
    },
    {
        "nome_moodle": "DevOps - Turma 5",
        "turma": "05",
        "tipo": "DevOps",
        "dias": "Terça e Quinta",
        "horario": "14:00 às 17:00",
        "professor": "Carlos Henrique",
    },
    {
        "nome_moodle": "Análise de Dados - Turma 6",
        "turma": "06",
        "tipo": "Análise de Dados",
        "dias": "Terça e Quinta",
        "horario": "18:00 às 21:00",
        "professor": "Danilo Farias",
    },
    {
        "nome_moodle": "Testes de Software - Turma 7",
        "turma": "07",
        "tipo": "Testes de Software",
        "dias": "Segunda e Quarta",
        "horario": "14:00 às 17:00",
        "professor": "Breno Cunha",
    },
    {
        "nome_moodle": "DevOps - Turma 8",
        "turma": "08",
        "tipo": "DevOps",
        "dias": "Terça e Quinta",
        "horario": "13:30 às 16:30",
        "professor": "Diogo Lopes",
    },
    {
        "nome_moodle": "DevOps - Turma 10",
        "turma": "10",
        "tipo": "DevOps",
        "dias": "Segunda e Quarta",
        "horario": "16:00 às 19:00",
        "professor": "Gustavo Rodrigues",
    },
    {
        "nome_moodle": "DevOps -Turma 15",
        "turma": "15",
        "tipo": "DevOps",
        "dias": "Segunda e Sexta",
        "horario": "15:00 às 18:00",
        "professor": "Silvio Monte",
    },
    {
        "nome_moodle": "DevOps - Turma 16",
        "turma": "16",
        "tipo": "DevOps",
        "dias": "Segunda e Quarta",
        "horario": "09:00 às 12:00",
        "professor": "Matheus Darlyson",
    },
    {
        "nome_moodle": "Análise de Dados - Turma 17",
        "turma": "17",
        "tipo": "Análise de Dados",
        "dias": "Segunda e Quarta",
        "horario": "18:00 às 21:00",
        "professor": "Letícia Correira",
    },
    {
        "nome_moodle": "Testes de Software - Turma 18",
        "turma": "18",
        "tipo": "Testes de Software",
        "dias": "Terça e Quinta",
        "horario": "09:00 às 12:00",
        "professor": "André Ribeiro",
    },
    {
        "nome_moodle": "DevOps - Turma 19",
        "turma": "19",
        "tipo": "DevOps",
        "dias": "Terça e Quinta",
        "horario": "14:00 às 17:00",
        "professor": "Emerson Gustavo",
    },
    {
        "nome_moodle": "Análise de Dados - Turma 20",
        "turma": "20",
        "tipo": "Análise de Dados",
        "dias": "Terça e Quinta",
        "horario": "18:00 às 21:00",
        "professor": "Vitor Gabriel",
    },
]


def realizar_login(page: Page, url_login: str, usuario: str, senha: str) -> None:
    print("  • Iniciando processo de login...")
    page.goto(url_login)
    page.wait_for_load_state("domcontentloaded")

    try:
        botao_sair = page.locator(
            "#logininsidebaric, button:has-text('Sair'), button:has-text('Log out')"
        ).first
        botao_sair.wait_for(state="visible", timeout=2000)
        print("  • Sessão fantasma detectada! Clicando em 'Sair' para limpar...")
        botao_sair.click()
        page.wait_for_load_state("networkidle")
        page.goto(url_login)
        page.wait_for_load_state("domcontentloaded")
    except Exception:
        pass

    print("  • Preenchendo credenciais...")
    page.locator("#username").fill(usuario)
    try:
        page.locator("#password").fill(senha)
    except Exception:
        page.locator("input[name='password']").fill(senha)

    try:
        page.locator("#loginbtn").click(timeout=5000)
        page.wait_for_load_state("networkidle")
    except Exception:
        page.screenshot(path=str(BASE_DIR / "debug_falha_login.png"))
        page.locator("button[type='submit']").click()
        page.wait_for_load_state("networkidle")

    print("  ✔ Login realizado com sucesso!")


def _soup(page: Page) -> BeautifulSoup:
    return BeautifulSoup(page.content(), "html.parser")


def _extrair_id_curso(url: str) -> str:
    match = re.search(r"[?&]id=(\d+)", url)
    return match.group(1) if match else ""


def _normalizar_url(url: str, base_url: str) -> str:
    if url.startswith("http"):
        return url
    if url.startswith("/"):
        return base_url.rstrip("/") + url
    return base_url.rstrip("/") + "/" + url


def _nome_normalizado(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.strip()).lower()


def get_turmas(page: Page, url_turmas: str) -> list[dict]:
    """Navega pela árvore de categorias e mapeia as URLs dos cursos para TURMAS_RELACAO."""
    base_url = "/".join(url_turmas.split("/")[:3])

    print("  • Navegando pela árvore de categorias...")
    page.goto(url_turmas)
    page.wait_for_load_state("networkidle")

    caminho_categorias = [
        "Formação Acelerada em Programação",
        "FAP 2026",
        "FAP. Formação Acelerada em Programação 2026",
    ]

    for categoria in caminho_categorias:
        try:
            link = page.locator(f"a:has-text('{categoria}')").first
            link.wait_for(state="visible", timeout=10000)
            link.click()
            page.wait_for_load_state("networkidle")
            print(f"    ✔ Entrou em: {categoria}")
        except Exception as e:
            print(f"    ⚠ Não encontrou '{categoria}': {e}", file=sys.stderr)
            break

    soup = _soup(page)
    links_cursos: dict[str, str] = {}

    for a in soup.find_all("a", href=re.compile(r"course/view\.php\?id=\d+")):
        nome = _nome_normalizado(a.get_text())
        href = _normalizar_url(a.get("href", ""), base_url)
        if nome:
            links_cursos[nome] = href

    print(f"  • {len(links_cursos)} curso(s) encontrado(s) na categoria")

    turmas_com_url: list[dict] = []
    nao_encontradas: list[str] = []

    for turma in TURMAS_RELACAO:
        nome_alvo = _nome_normalizado(turma["nome_moodle"])
        url_encontrada = links_cursos.get(nome_alvo)
        if not url_encontrada:
            for nome_pag, url_pag in links_cursos.items():
                if nome_alvo in nome_pag or nome_pag in nome_alvo:
                    url_encontrada = url_pag
                    break

        if url_encontrada:
            turmas_com_url.append({**turma, "url": url_encontrada})
        else:
            nao_encontradas.append(turma["nome_moodle"])

    if nao_encontradas:
        print(f"  ⚠ Turmas não localizadas: {nao_encontradas}", file=sys.stderr)

    print(f"  • {len(turmas_com_url)} turma(s) com URL mapeada")
    return turmas_com_url


def _limpar_nome(nome: str) -> str:
    """Remove 'Selecione 'Nome'' e artefatos similares do UI do Moodle."""
    nome = re.sub(r"^Selecione\s*['\"]?\s*", "", nome, flags=re.IGNORECASE)
    nome = re.sub(r"[\s.]*['\"]?\s*$", "", nome)
    return nome.strip()


def get_participantes(page: Page, turma_url: str, base_url: str) -> list[dict]:
    """Extrai participantes da aba Participantes do curso."""
    course_id = _extrair_id_curso(turma_url)
    url_base_part = f"{base_url}/user/index.php?id={course_id}&perpage=5000"

    participantes: list[dict] = []
    pagina = 0

    while True:
        url_pag = url_base_part + (f"&page={pagina}" if pagina > 0 else "")
        page.goto(url_pag)
        page.wait_for_load_state("networkidle")
        soup = _soup(page)

        tabela = soup.find("table", {"id": "participants"}) or soup.select_one("table.generaltable")

        if not tabela:
            print(f"    ⚠ Tabela de participantes não encontrada (curso {course_id})", file=sys.stderr)
            break

        tbody = tabela.find("tbody") or tabela
        linhas = tbody.find_all("tr")

        if not linhas:
            break

        for linha in linhas:
            celulas = linha.find_all("td")
            if len(celulas) < 2:
                continue

            nome_el = celulas[0].find("a") or celulas[0]
            nome = _limpar_nome(nome_el.get_text(strip=True))

            email = ""
            for cel in celulas[1:]:
                texto = cel.get_text(strip=True)
                if "@" in texto:
                    email = texto.strip().lower()
                    break

            if nome and "@" in email:
                participantes.append({"nome": nome, "email": email})

        if len(linhas) < 5000:
            break

        pagina += 1
        time.sleep(0.3)

    return participantes


# Colunas de identificação do aluno no CSV de exportação — não são notas
_COLS_ID = {
    "nome completo", "sobrenome", "nome", "username", "número de id", "id number",
    "endereço de e-mail", "email address", "e-mail", "email",
    "instituição", "institution", "departamento", "department",
}


def _parse_export_csv(caminho: Path) -> tuple[list[str], dict]:
    """
    Faz o parse do CSV exportado pelo Moodle (/grade/export/txt/).
    Retorna (lista_atividades, {email_ou_nome: {atividade: nota}}).
    """
    atividades: list[str] = []
    notas: dict = {}

    with open(caminho, encoding="utf-8-sig") as f:
        reader = csv_mod.DictReader(f)
        if not reader.fieldnames:
            return [], {}

        # Identifica quais colunas são de nota (não são de identificação)
        for col in reader.fieldnames:
            if col.strip().lower() not in _COLS_ID and col.strip():
                atividades.append(col.strip())

        VAZIO = {"-", "–", "—", ""}

        for row in reader:
            email = (
                row.get("Endereço de e-mail")
                or row.get("Email address")
                or row.get("E-mail")
                or row.get("email")
                or ""
            ).strip().lower()

            nome_completo = (
                row.get("Nome completo")
                or f"{row.get('Nome', '')} {row.get('Sobrenome', '')}".strip()
            )
            chave = email if email else _nome_normalizado(nome_completo)
            if not chave:
                continue

            notas_aluno: dict = {}
            for at in atividades:
                valor = (row.get(at) or "").strip()
                if valor in VAZIO:
                    valor = "0"
                else:
                    # Extrai apenas o número quando vem como "8,00" ou "8.00 (8.00)"
                    m = re.match(r"^([\d.,]+)", valor)
                    valor = m.group(1) if m else "0"
                notas_aluno[at] = valor

            notas[chave] = notas_aluno

    return atividades, notas


def get_notas(page: Page, turma_url: str, base_url: str) -> tuple[list[str], dict]:
    """
    Extrai notas via exportação CSV nativa do Moodle (mais confiável que parsing do grader report).
    Fallback: JavaScript direto no DOM do grader report.
    """
    course_id = _extrair_id_curso(turma_url)

    # ── Estratégia 1: Download CSV do exportador de notas ────────────────────
    url_export = f"{base_url}/grade/export/txt/index.php?id={course_id}"
    page.goto(url_export)
    page.wait_for_load_state("networkidle")

    tmp_path = BASE_DIR / f"_tmp_export_{course_id}.csv"

    try:
        with page.expect_download(timeout=30000) as dl_info:
            # Seleciona todos os itens de nota, se houver checkbox
            for sel in ["#checkall", "a:has-text('Selecionar tudo')", "a:has-text('Select all')"]:
                try:
                    page.click(sel, timeout=2000)
                    break
                except Exception:
                    pass

            # Clica no botão de exportação/download
            clicou = False
            for sel in [
                "input[type='submit'][name='nosubmit']",
                "input[type='submit'][value*='Download']",
                "input[type='submit'][value*='Baixar']",
                "input[type='submit'][value*='Exportar']",
                "button:has-text('Download')",
                "button:has-text('Baixar')",
                "input[type='submit']",
                "button[type='submit']",
            ]:
                try:
                    page.click(sel, timeout=4000)
                    clicou = True
                    break
                except Exception:
                    pass

            if not clicou:
                raise RuntimeError("Botão de exportação não encontrado")

        dl_info.value.save_as(str(tmp_path))
        atividades, notas = _parse_export_csv(tmp_path)
        tmp_path.unlink(missing_ok=True)

        if atividades:
            return atividades, notas

        print("    ⚠ Export retornou sem colunas de nota — tentando grader report...", file=sys.stderr)

    except Exception as e:
        print(f"    ⚠ Export CSV falhou ({e}) — tentando grader report...", file=sys.stderr)
        tmp_path.unlink(missing_ok=True)

    # ── Estratégia 2: JavaScript direto no grader report ─────────────────────
    return _get_notas_via_js(page, course_id, base_url)


_JS_GRADER = """
() => {
    const IGNORAR = new Set([
        '', '-', 'ações', 'acoes', 'selecionar', 'nome completo',
        'endereço de e-mail', 'e-mail', 'email', 'actions', 'select',
        'first name', 'surname', 'last name', 'username',
    ]);

    const table = document.querySelector('table.gradestable')
        || document.querySelector('#user-grades')
        || document.querySelector('table[id*="grade"]')
        || (() => {
            for (const t of document.querySelectorAll('table'))
                if (t.querySelector('.grade') || t.querySelector('[class*="grade"]')) return t;
            return null;
        })();

    if (!table) return null;

    const headers = [], headerIdxs = [];
    const thead = table.querySelector('thead');
    if (thead) {
        const rows = [...thead.querySelectorAll('tr')];
        const last = rows[rows.length - 1];
        [...last.querySelectorAll('th')].forEach((th, idx) => {
            const t = th.textContent.trim();
            if (t && !IGNORAR.has(t.toLowerCase())) { headers.push(t); headerIdxs.push(idx); }
        });
    }

    const rows = [];
    const tbody = table.querySelector('tbody');
    if (tbody) {
        [...tbody.querySelectorAll('tr')].forEach(tr => {
            const cells = [...tr.querySelectorAll('td, th')];
            if (!cells.length) return;
            let email = '', nome = '';
            for (let i = 0; i < Math.min(cells.length, 5); i++) {
                const t = cells[i].textContent.trim();
                if (!email && t.includes('@')) email = t.toLowerCase();
                else if (!nome && t.length > 2) nome = t;
                if (email && nome) break;
            }
            const grades = headerIdxs.map(idx => cells[idx] ? cells[idx].textContent.trim() : '');
            if (nome || email) rows.push({ nome, email, grades });
        });
    }
    return { headers, rows };
}
"""


def _get_notas_via_js(page: Page, course_id: str, base_url: str) -> tuple[list[str], dict]:
    """Fallback: extrai notas via JavaScript no grader report."""
    url_notas = f"{base_url}/grade/report/grader/index.php?id={course_id}"
    page.goto(url_notas)
    page.wait_for_load_state("networkidle")

    for seletor in ["table.gradestable", "#user-grades", "table"]:
        try:
            page.wait_for_selector(seletor, timeout=8000)
            break
        except Exception:
            continue

    for seletor in ["a.grader-toggle-expand-all", "[data-action='expandAll']",
                    "a:has-text('Expandir tudo')", "a:has-text('Expand all')"]:
        try:
            page.click(seletor, timeout=2000)
            page.wait_for_load_state("networkidle")
            break
        except Exception:
            continue

    resultado = page.evaluate(_JS_GRADER)
    if not resultado:
        return [], {}

    atividades: list[str] = resultado.get("headers", [])
    VAZIO = {"-", "–", "—", " ", "N/A", ""}
    notas: dict = {}

    for row in resultado.get("rows", []):
        email = (row.get("email") or "").strip().lower()
        nome = (row.get("nome") or "").strip()
        chave = email if email else _nome_normalizado(nome)
        if not chave:
            continue

        notas_aluno: dict = {}
        grades = row.get("grades", [])
        for i, atividade in enumerate(atividades):
            valor = grades[i] if i < len(grades) else ""
            if valor in VAZIO:
                valor = "0"
            else:
                m = re.match(r"^([\d.,]+)", valor)
                if m:
                    valor = m.group(1)
            notas_aluno[atividade] = valor

        notas[chave] = notas_aluno

    return atividades, notas
