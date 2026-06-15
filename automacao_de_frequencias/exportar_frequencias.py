import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from .config import Config

BASE_DIR = Path(__file__).resolve().parent


def realizar_login(page, url_login, usuario, senha):
    """Realiza o login no Moodle de forma agnóstica a idioma e modo de execução."""
    print("  • Iniciando processo de login...")
    page.goto(url_login)
    page.wait_for_load_state("domcontentloaded")

    try:
        # Trata possíveis sessões ativas sobrepostas
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


def exportar_frequencia(
    page, url, nome_turma, caminho_saida, url_login, usuario, senha
):
    """Exporta a frequência de uma turma específica."""
    print(f"  • Exportando frequência: {nome_turma}")
    page.goto(url)
    page.wait_for_load_state("networkidle")

    if "login" in page.url:
        print("  • Sessão expirada. Reconectando...")
        realizar_login(page, url_login, usuario, senha)
        page.goto(url)
        page.wait_for_load_state("networkidle")

    try:
        checkbox = page.get_by_label(re.compile(r"observa", re.IGNORECASE))
        if not checkbox.is_checked():
            checkbox.check()

        caminho_arquivo = caminho_saida / f"{nome_turma}.xlsx"
        with page.expect_download(timeout=15000) as download_info:
            page.get_by_role("button", name="OK").click()

        download_info.value.save_as(str(caminho_arquivo))
        print(f"  ✔ Salvo em: {caminho_arquivo}")

    except Exception as e:
        print(f"  ❌ ERRO ao exportar {nome_turma}: {e}", file=sys.stderr)


def main(config: Config):
    """Função principal que orquestra o pipeline de exportação de frequências."""
    print("=" * 80)
    print("▶ [ESCOPO 1] EXPORTAÇÃO DE FREQUÊNCIAS (MOODLE)")
    print("=" * 80)

    url_login = config.moodle.url_login
    usuario = config.moodle.usuario
    senha = config.moodle.senha
    urls_frequencias = config.moodle.urls_frequencias
    caminho_saida = config.moodle.caminho_exportacao

    if not urls_frequencias:
        print(
            "  ❌ ERRO: Nenhuma URL de frequência encontrada no settings.json",
            file=sys.stderr,
        )
        print("=" * 80)
        return

    caminho_saida.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as p:
            chrome_args = ["--disable-blink-features=AutomationControlled"]
            navegador = p.chromium.launch(headless=True, args=chrome_args)
            contexto = navegador.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768},
            )
            pagina = contexto.new_page()

            realizar_login(pagina, url_login, usuario, senha)

            for nome_turma, url in urls_frequencias.items():
                exportar_frequencia(
                    pagina, url, nome_turma, caminho_saida, url_login, usuario, senha
                )
                time.sleep(1.5)

        print("\n✔ Escopo 1 finalizado com sucesso!")
    except Exception as e:
        print(f"\n⚠️ Escopo 1 terminou com falhas: {e}", file=sys.stderr)

    print("=" * 80)
