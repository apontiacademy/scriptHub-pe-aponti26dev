import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from scripthub.services import log
from scripthub.services.moodle import MoodleSessao

from .config import Config

# =========================================================================
# ANCORAGEM DINÂMICA DE ESCOPO
# =========================================================================
PASTA_ESCOPO = Path(__file__).resolve().parent

_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")


# ---------------------------------------------------------------------------
# Conversão de conteúdo
# ---------------------------------------------------------------------------


def carregar_conteudo(filepath: Path) -> tuple[str, str]:
    """Lê o arquivo .md e retorna (titulo, html_conteudo)."""
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
    text = filepath.read_text(encoding="utf-8").strip()
    lines = text.splitlines()
    title = ""
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("# "):
            title = line.strip()[2:].strip()
            body_start = i + 1
            break
    if not title:
        raise ValueError(
            "O arquivo .md deve ter um título na primeira linha com '#'. "
            "Exemplo: # Semana 10 - Relatórios"
        )
    body = "\n".join(lines[body_start:]).strip()
    html = _md_para_html(body) if body else ""
    return title, html


def encontrar_imagem(pasta: Path, override: str | None = None) -> str | None:
    """Retorna o caminho da imagem: override explícito ou primeira imagem na pasta do escopo."""
    if override:
        path = Path(override).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de imagem não encontrado: {override}")
        return str(path)
    for ext in _IMAGE_EXTENSIONS:
        matches = sorted(pasta.glob(f"*{ext}"))
        if matches:
            return str(matches[0])
    return None


def _md_para_html(text: str) -> str:
    text = re.sub(r"^[-*] (.+)$", r"<li>\1</li>", text, flags=re.MULTILINE)
    text = re.sub(r"(<li>.*</li>\n?)+", lambda m: f"<ul>{m.group()}</ul>", text)
    text = re.sub(r"^### (.+)$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
    text = re.sub(r"^## (.+)$", r"<h2>\1</h2>", text, flags=re.MULTILINE)
    text = re.sub(r"^# (.+)$", r"<h1>\1</h1>", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    blocks = re.split(r"\n{2,}", text)
    result = []
    for block in blocks:
        block = block.strip()
        if block and not block.startswith("<"):
            block = f"<p>{block}</p>"
        if block:
            result.append(block)
    return "\n".join(result)


# ---------------------------------------------------------------------------
# Automação Playwright
# ---------------------------------------------------------------------------


def _injetar_cookies(contexto, sessao: MoodleSessao) -> None:
    """Transfere cookies da sessão HTTP para o contexto do Playwright."""
    parsed = urlparse(sessao.url_login)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    cookies = [
        {"name": c.name, "value": c.value, "url": base_url, "path": c.path or "/"}
        for c in sessao._session.cookies
    ]
    if cookies:
        contexto.add_cookies(cookies)


def _sessao_expirada(page) -> bool:
    return "/login" in page.url


def _clicar_novo_topico(page) -> None:
    candidates = [
        ("button", "Adicionar tópico de discussão"),
        ("link", "Adicionar tópico de discussão"),
        ("button", "Adicionar um novo tópico de discussão"),
        ("link", "Adicionar um novo tópico de discussão"),
        ("link", "Add a new discussion topic"),
        ("button", "Add a new discussion topic"),
        ("link", "Adicionar tópico"),
        ("link", "Add topic"),
    ]
    for role, name in candidates:
        loc = page.get_by_role(role, name=name)
        if loc.count() > 0:
            loc.first.click()
            return
    link = page.locator('a[href*="post.php"]').first
    if link.count() > 0:
        link.click()
        return
    raise RuntimeError("Botão de novo tópico não encontrado na página do fórum.")


def _definir_conteudo_editor(page, html_content: str) -> None:
    try:
        page.wait_for_function(
            "() => (typeof tinymce !== 'undefined' && tinymce.activeEditor !== null)"
            " || (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor !== null)"
            " || document.querySelector('.editor_atto_content') !== null"
            " || document.getElementById('id_messageeditable') !== null",
            timeout=10_000,
        )
    except Exception:
        pass
    try:
        if page.evaluate("typeof tinymce !== 'undefined' && tinymce.activeEditor !== null"):
            page.evaluate("(html) => tinymce.activeEditor.setContent(html)", html_content)
            return
    except Exception:
        pass
    try:
        if page.evaluate("typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor !== null"):
            page.evaluate("(html) => tinyMCE.activeEditor.setContent(html)", html_content)
            return
    except Exception:
        pass
    for selector in (".editor_atto_content", "#id_messageeditable"):
        if page.locator(selector).count() > 0:
            page.evaluate(
                f"(html) => document.querySelector('{selector}').innerHTML = html",
                html_content,
            )
            return
    if page.locator("#id_message").count() > 0:
        page.fill("#id_message", html_content)
        return
    raise RuntimeError("Editor de conteúdo do fórum não encontrado.")


def _verificar_conteudo_editor(page) -> bool:
    """Retorna True se o editor tem conteúdo não-vazio."""
    try:
        content = page.evaluate(
            "() => {"
            "  if (typeof tinymce !== 'undefined' && tinymce.activeEditor)"
            "    return tinymce.activeEditor.getContent();"
            "  if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor)"
            "    return tinyMCE.activeEditor.getContent();"
            "  return null;"
            "}"
        )
        if content and content.strip() not in ("", "<p></p>", "<p><br></p>"):
            return True
    except Exception:
        pass
    for selector in (".editor_atto_content", "#id_messageeditable"):
        el = page.locator(selector)
        if el.count() > 0:
            html = el.inner_html()
            if html and html.strip() not in ("", "<br>", "<p><br></p>"):
                return True
    return False


def _fazer_upload_imagem(page, image_path: str) -> None:
    # Caminho 1: botão de imagem na toolbar do TinyMCE (plugin tiny_image do Moodle)
    img_btn = page.locator('button[data-mce-name="tiny_media_image"]')
    if img_btn.count() > 0:
        img_btn.first.click()
        try:
            page.wait_for_selector(".tiny_image_insert_image, .tiny_image_dropzone", timeout=6_000)
        except Exception:
            pass
        # O input de arquivo pode ser o fixo (#tiny_image_fileinput) ou o do dropzone
        file_input = page.locator(
            "#tiny_image_fileinput, input.drop-zone-fileinput, input[type=file][accept='image/*']"
        ).first
        if file_input.count() == 0:
            log.aviso("Input de imagem do TinyMCE não encontrado — imagem ignorada.")
            # Fecha o dialog se abriu
            esc = page.locator(
                ".tox-dialog__footer .tox-button--secondary, button[aria-label='Fechar'], button[aria-label='Close']"
            )
            if esc.count() > 0:
                esc.first.click()
            return
        file_input.set_input_files(image_path)
        # Aguarda o Moodle processar o upload e exibir "Detalhes da imagem"
        try:
            page.wait_for_selector(
                ".tiny_image_image_details, .tiny_image_preview",
                timeout=20_000,
            )
        except Exception:
            log.aviso("Tela de detalhes da imagem não apareceu — imagem pode não ter sido inserida.")
            cancel = page.locator("button[data-action='cancel'], button[data-action='hide']")
            if cancel.count() > 0:
                cancel.first.click()
            page.wait_for_timeout(500)
            return
        page.wait_for_timeout(500)
        # Marca como decorativa para evitar bloqueio por validação de alt text
        decorativa = page.locator("input.tiny_image_presentation")
        if decorativa.count() > 0 and not decorativa.is_checked():
            decorativa.check()
        # Usa o seletor CSS específico da classe do plugin tiny_image
        save_btn = page.locator("button.tiny_image_urlentrysubmit, .modal-footer button[type=submit]")
        if save_btn.count() > 0:
            save_btn.first.click()
            page.wait_for_timeout(2_000)
            return
        log.aviso("Botão de salvar imagem não encontrado — imagem pode não ter sido inserida.")
        return

    # Caminho 2: input de anexo direto na área de attachments do formulário
    direct_input = page.locator('input[type=file][name*="attachment"], input[type=file][name*="file"]')
    if direct_input.count() > 0:
        direct_input.first.set_input_files(image_path)
        return

    # Caminho 3: filemanager widget (Moodle clássico)
    add_btn = page.locator(".filemanager .fp-btn-add, .filemanager button").first
    if add_btn.count() == 0:
        log.aviso("Área de anexos não encontrada — imagem ignorada.")
        return
    add_btn.click()
    page.wait_for_selector(".fp-content, .filepicker-filelist", timeout=10_000)
    for label in ("Enviar arquivo", "Upload a file", "Carregar arquivo"):
        tab = page.get_by_text(label, exact=False)
        if tab.count() > 0:
            tab.first.click()
            break
    dialog_input = page.locator('.fp-upload-form input[type=file], input[name="repo_upload_file"]')
    if dialog_input.count() == 0:
        log.aviso("Input de upload não encontrado — imagem ignorada.")
        return
    dialog_input.first.set_input_files(image_path)
    for label in ("Enviar este arquivo", "Upload this file", "Salvar"):
        btn = page.get_by_role("button", name=label)
        if btn.count() > 0:
            btn.first.click()
            page.wait_for_selector(".fp-btn-add", timeout=10_000)
            return
    log.aviso("Botão de confirmação de upload não encontrado — imagem pode não ter sido anexada.")


def _sincronizar_editor(page) -> None:
    try:
        page.evaluate(
            "() => { if (typeof tinymce !== 'undefined' && tinymce.activeEditor) { tinymce.activeEditor.save(); } }"
        )
    except Exception:
        pass
    try:
        page.evaluate(
            "() => { if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor) { tinyMCE.activeEditor.save(); } }"
        )
    except Exception:
        pass


def _submeter_formulario(page) -> None:
    _sincronizar_editor(page)
    page.wait_for_timeout(1_500)
    btn = page.locator("#id_submitbutton")
    if btn.count() > 0:
        btn.first.scroll_into_view_if_needed()
        btn.first.click()
        return
    for label in (
        "Enviar mensagem ao fórum",
        "Publicar no fórum",
        "Post to forum",
        "Submit",
        "Enviar",
    ):
        loc = page.get_by_role("button", name=label)
        if loc.count() > 0:
            loc.first.click()
            return
    raise RuntimeError("Botão de submissão não encontrado.")


def publicar_no_forum(
    page,
    forum_url: str,
    title: str,
    html_content: str,
    image_path: str | None,
    sessao: MoodleSessao,
) -> bool:
    try:
        page.goto(forum_url, timeout=30_000)
        if _sessao_expirada(page):
            log.passo("Sessão expirada — refazendo login...")
            sessao.login()
            _injetar_cookies(page.context, sessao)
            page.goto(forum_url, timeout=30_000)
        log.passo("Clicando em 'Novo tópico'...")
        _clicar_novo_topico(page)
        page.wait_for_selector("#id_subject", timeout=15_000)
        log.passo("Preenchendo título...")
        page.fill("#id_subject", title)
        page.wait_for_timeout(2_000)
        log.passo("Preenchendo conteúdo do editor...")
        _definir_conteudo_editor(page, html_content)
        page.wait_for_timeout(1_500)
        if not _verificar_conteudo_editor(page):
            log.passo("Conteúdo não detectado no editor — tentando novamente...")
            _definir_conteudo_editor(page, html_content)
            page.wait_for_timeout(1_500)
        if image_path:
            log.passo(f"Anexando imagem: {Path(image_path).name}")
            _fazer_upload_imagem(page, image_path)
        log.passo("Submetendo formulário...")
        _submeter_formulario(page)
        log.passo("Aguardando confirmação de publicação...")
        page.wait_for_url(lambda url: "post.php" not in url, timeout=30_000)
        # Verifica erros reais: elementos visíveis com texto de erro (evita
        # falso-positivo do .error usado como classe de estilo em campos Moodle).
        erro_real = page.evaluate(
            "() => {"
            "  const sels = ['.alert-danger', '.notifyproblem', '#id_error_message'];"
            "  for (const s of sels) {"
            "    const el = document.querySelector(s);"
            "    if (el && el.offsetParent !== null && el.textContent.trim()) return true;"
            "  }"
            "  return false;"
            "}"
        )
        if erro_real:
            msg = page.locator(".alert-danger, .notifyproblem, #id_error_message").first.inner_text()
            log.aviso(f"Moodle exibiu erro: {msg.strip()[:120]}")
            return False
        return True
    except PlaywrightTimeoutError as exc:
        log.erro(f"[TIMEOUT] {exc}")
    except RuntimeError as exc:
        log.erro(f"[ERRO] {exc}")
    except Exception as exc:
        log.erro(f"[ERRO inesperado] {exc}")
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    log.secao("AUTOMAÇÃO DE POSTAGEM EM FÓRUNS (MOODLE)")

    # Carrega as configurações unificadas (settings.json + .env)
    config = Config.load()

    login_url = config.moodle.url_login
    username = config.moodle.usuario
    password = config.moodle.senha
    forum_urls = config.moodle.urls_foruns
    headless = config.moodle.headless
    post_delay = config.moodle.post_delay

    post_file = config.moodle.caminho_post_file

    if not post_file.exists():
        raise FileNotFoundError(f"Arquivo de post não encontrado em: {post_file}")

    if not forum_urls:
        raise ValueError("Nenhuma URL de fórum encontrada no settings.json")

    log.passo(f"Carregando conteúdo: {post_file.name}")
    title, html_content = carregar_conteudo(post_file)

    if config.moodle.caminho_imagem:
        log.passo(f"Imagem detectada: {config.moodle.caminho_imagem.name}")
        image_path = str(config.moodle.caminho_imagem)
    else:
        image_path = None

    log.passo(f"Publicando '{title}' em {len(forum_urls)} fórum(s)...")

    resultados: dict[str, bool] = {}

    log.passo(f"Fazendo login em {login_url}...")
    sessao = MoodleSessao(login_url, username, password)
    sessao.login()
    log.ok("Login realizado com sucesso.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        _injetar_cookies(context, sessao)
        page = context.new_page()

        for i, url in enumerate(forum_urls, 1):
            log.passo(f"[{i}/{len(forum_urls)}] {url}")
            sucesso = publicar_no_forum(
                page,
                url,
                title,
                html_content,
                image_path,
                sessao,
            )
            resultados[url] = sucesso
            if sucesso:
                log.ok("Publicado")
            else:
                log.erro("FALHOU")
            if i < len(forum_urls):
                log.passo(f"Aguardando {post_delay}s antes do próximo fórum...")
                page.wait_for_timeout(post_delay * 1_000)

        browser.close()

    ok_count = sum(1 for v in resultados.values() if v)
    falhou = len(resultados) - ok_count

    log.ok(f"Resumo: {ok_count}/{len(resultados)} fóruns publicados com sucesso.")
    if falhou:
        log.aviso(f"{falhou} fórum(s) com falha:")
        for url, sucesso in resultados.items():
            if not sucesso:
                log.passo(f"  - {url}")
        raise RuntimeError(f"{falhou} fórum(s) falharam ao publicar.")

    log.ok("AUTOMAÇÃO DE FÓRUNS CONCLUÍDA COM SUCESSO!")
