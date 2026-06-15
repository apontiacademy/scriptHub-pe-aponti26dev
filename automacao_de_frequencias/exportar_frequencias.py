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
