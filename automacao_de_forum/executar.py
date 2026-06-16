import argparse
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

# =========================================================================
# ANCORAGEM DINÂMICA DE ESCOPO
# =========================================================================
PASTA_ESCOPO = Path(__file__).resolve().parent

env_path = PASTA_ESCOPO / ".env"
load_dotenv(dotenv_path=env_path, override=True)

_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")


# ---------------------------------------------------------------------------
# Conversão de conteúdo
# ---------------------------------------------------------------------------

def carregar_conteudo(filepath: Path) -> tuple[str, str]:
    """Lê o arquivo .md e retorna (titulo, html_conteudo)."""
    if not filepath.exists():
        print(f"  ❌ ERRO: Arquivo não encontrado: {filepath}", file=sys.stderr)
        sys.exit(1)
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
        print("  ❌ ERRO: O arquivo .md deve ter um título na primeira linha com '#'.", file=sys.stderr)
        print("  Exemplo: # Semana 10 - Relatórios", file=sys.stderr)
        sys.exit(1)
    body = "\n".join(lines[body_start:]).strip()
    html = _md_para_html(body) if body else ""
    return title, html


def encontrar_imagem(pasta: Path, override: str | None = None) -> str | None:
    """Retorna o caminho da imagem: override explícito ou primeira imagem na pasta do escopo."""
    if override:
        path = Path(override).resolve()
        if not path.exists():
            print(f"  ❌ ERRO: Arquivo de imagem não encontrado: {override}", file=sys.stderr)
            sys.exit(1)
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

def fazer_login(page, login_url: str, username: str, password: str) -> None:
    page.goto(login_url, timeout=30_000)
    page.fill("#username", username)
    page.fill("#password", password)
    page.click('[type=submit]')
    page.wait_for_function(
        "() => !window.location.href.includes('/login')",
        timeout=30_000,
    )


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
            page.wait_for_selector(
                ".tiny_image_insert_image, .tiny_image_dropzone", timeout=6_000
            )
        except Exception:
            pass
        # O input de arquivo pode ser o fixo (#tiny_image_fileinput) ou o do dropzone
        file_input = page.locator(
            "#tiny_image_fileinput, input.drop-zone-fileinput, input[type=file][accept='image/*']"
        ).first
        if file_input.count() == 0:
            print("  [AVISO] Input de imagem do TinyMCE não encontrado — imagem ignorada.")
            # Fecha o dialog se abriu
            esc = page.locator(".tox-dialog__footer .tox-button--secondary, button[aria-label='Fechar'], button[aria-label='Close']")
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
            print("  [AVISO] Tela de detalhes da imagem não apareceu — imagem pode não ter sido inserida.")
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
        save_btn = page.locator(
            "button.tiny_image_urlentrysubmit, .modal-footer button[type=submit]"
        )
        if save_btn.count() > 0:
            save_btn.first.click()
            page.wait_for_timeout(2_000)
            return
        print("  [AVISO] Botão de salvar imagem não encontrado — imagem pode não ter sido inserida.")
        return

    # Caminho 2: input de anexo direto na área de attachments do formulário
    direct_input = page.locator(
        'input[type=file][name*="attachment"], input[type=file][name*="file"]'
    )
    if direct_input.count() > 0:
        direct_input.first.set_input_files(image_path)
        return

    # Caminho 3: filemanager widget (Moodle clássico)
    add_btn = page.locator(".filemanager .fp-btn-add, .filemanager button").first
    if add_btn.count() == 0:
        print("  [AVISO] Área de anexos não encontrada — imagem ignorada.")
        return
    add_btn.click()
    page.wait_for_selector(".fp-content, .filepicker-filelist", timeout=10_000)
    for label in ("Enviar arquivo", "Upload a file", "Carregar arquivo"):
        tab = page.get_by_text(label, exact=False)
        if tab.count() > 0:
            tab.first.click()
            break
    dialog_input = page.locator(
        '.fp-upload-form input[type=file], input[name="repo_upload_file"]'
    )
    if dialog_input.count() == 0:
        print("  [AVISO] Input de upload não encontrado — imagem ignorada.")
        return
    dialog_input.first.set_input_files(image_path)
    for label in ("Enviar este arquivo", "Upload this file", "Salvar"):
        btn = page.get_by_role("button", name=label)
        if btn.count() > 0:
            btn.first.click()
            page.wait_for_selector(".fp-btn-add", timeout=10_000)
            return
    print("  [AVISO] Botão de confirmação de upload não encontrado — imagem pode não ter sido anexada.")


def _sincronizar_editor(page) -> None:
    try:
        page.evaluate(
            "() => { if (typeof tinymce !== 'undefined' && tinymce.activeEditor)"
            " { tinymce.activeEditor.save(); } }"
        )
    except Exception:
        pass
    try:
        page.evaluate(
            "() => { if (typeof tinyMCE !== 'undefined' && tinyMCE.activeEditor)"
            " { tinyMCE.activeEditor.save(); } }"
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
    login_url: str,
    username: str,
    password: str,
) -> bool:
    try:
        page.goto(forum_url, timeout=30_000)
        if _sessao_expirada(page):
            print("  • Sessão expirada — refazendo login...")
            fazer_login(page, login_url, username, password)
            page.goto(forum_url, timeout=30_000)
        print("  • Clicando em 'Novo tópico'...")
        _clicar_novo_topico(page)
        page.wait_for_selector("#id_subject", timeout=15_000)
        print("  • Preenchendo título...")
        page.fill("#id_subject", title)
        page.wait_for_timeout(2_000)
        print("  • Preenchendo conteúdo do editor...")
        _definir_conteudo_editor(page, html_content)
        page.wait_for_timeout(1_500)
        if not _verificar_conteudo_editor(page):
            print("  • Conteúdo não detectado no editor — tentando novamente...")
            _definir_conteudo_editor(page, html_content)
            page.wait_for_timeout(1_500)
        if image_path:
            print(f"  • Anexando imagem: {Path(image_path).name}")
            _fazer_upload_imagem(page, image_path)
        print("  • Submetendo formulário...")
        _submeter_formulario(page)
        print("  • Aguardando confirmação de publicação...")
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
            print(f"  ⚠️ Moodle exibiu erro: {msg.strip()[:120]}", file=sys.stderr)
            return False
        return True
    except PlaywrightTimeoutError as exc:
        print(f"  ❌ [TIMEOUT] {exc}", file=sys.stderr)
    except RuntimeError as exc:
        print(f"  ❌ [ERRO] {exc}", file=sys.stderr)
    except Exception as exc:
        print(f"  ❌ [ERRO inesperado] {exc}", file=sys.stderr)
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(args_list: list[str] | None = None) -> None:
    print("=" * 80)
    print("▶ AUTOMAÇÃO DE POSTAGEM EM FÓRUNS (MOODLE)")
    print("=" * 80)

    parser = argparse.ArgumentParser(
        description="Publica um novo tópico de discussão em fóruns do Moodle."
    )
    parser.add_argument(
        "--content",
        default=None,
        help="Arquivo .md com o conteúdo do post (padrão: post.md na pasta do módulo).",
    )
    parser.add_argument(
        "--image",
        help="Imagem para anexar (padrão: detecta automaticamente na pasta do módulo).",
    )
    args = parser.parse_args(args_list)

    login_url = os.getenv("MOODLE_LOGIN_URL", "")
    username = os.getenv("MOODLE_USERNAME", "")
    password = os.getenv("MOODLE_PASSWORD", "")
    forum_urls_raw = os.getenv("MOODLE_FORUM_URLS", "")
    headless = os.getenv("MOODLE_HEADLESS", "true").lower() == "true"
    post_delay = int(os.getenv("MOODLE_POST_DELAY", "3"))

    post_file_env = os.getenv("MOODLE_POST_FILE", "")
    if args.content:
        post_file = Path(args.content).resolve()
    elif post_file_env:
        post_file = (PASTA_ESCOPO / post_file_env.lstrip("./")).resolve()
    else:
        post_file = PASTA_ESCOPO / "post.md"

    erros = []
    if not login_url:
        erros.append("- MOODLE_LOGIN_URL")
    if not username:
        erros.append("- MOODLE_USERNAME")
    if not password:
        erros.append("- MOODLE_PASSWORD")
    if not forum_urls_raw:
        erros.append("- MOODLE_FORUM_URLS")

    if erros:
        print("  ❌ ERRO: Variáveis de ambiente ausentes no .env:", file=sys.stderr)
        for erro in erros:
            print(f"    {erro}", file=sys.stderr)
        print("=" * 80)
        sys.exit(1)

    forum_urls = [u.strip() for u in forum_urls_raw.split(",") if u.strip()]
    if not forum_urls:
        print("  ❌ ERRO: MOODLE_FORUM_URLS está vazio.", file=sys.stderr)
        print("=" * 80)
        sys.exit(1)

    print(f"  • Carregando conteúdo: {post_file.name}")
    title, html_content = carregar_conteudo(post_file)

    image_path = encontrar_imagem(PASTA_ESCOPO, args.image)
    if image_path:
        print(f"  • Imagem detectada: {Path(image_path).name}")

    print(f"  • Publicando '{title}' em {len(forum_urls)} fórum(s)...")
    print()

    resultados: dict[str, bool] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        print(f"  • Fazendo login em {login_url}...")
        fazer_login(page, login_url, username, password)
        print("  ✔ Login realizado com sucesso.")
        print()

        for i, url in enumerate(forum_urls, 1):
            print(f"  [{i}/{len(forum_urls)}] {url}")
            sucesso = publicar_no_forum(
                page, url, title, html_content,
                image_path, login_url, username, password,
            )
            resultados[url] = sucesso
            status = "✔ Publicado" if sucesso else "❌ FALHOU"
            print(f"  {status}\n")
            if i < len(forum_urls):
                print(f"  ⏳ Aguardando {post_delay}s antes do próximo fórum...")
                page.wait_for_timeout(post_delay * 1_000)

        browser.close()

    ok = sum(1 for v in resultados.values() if v)
    falhou = len(resultados) - ok

    print("=" * 80)
    print(f"  Resumo: {ok}/{len(resultados)} fóruns publicados com sucesso.")
    if falhou:
        print(f"  ⚠️  {falhou} fórum(s) com falha:")
        for url, sucesso in resultados.items():
            if not sucesso:
                print(f"    - {url}")
        print("=" * 80)
        sys.exit(1)

    print("✔ AUTOMAÇÃO DE FÓRUNS CONCLUÍDA COM SUCESSO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
