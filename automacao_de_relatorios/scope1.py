import sys
import time
from pathlib import Path

from config import Config  # Imports our centralized Dataclass
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent


def login(page, login_url, username, password):
    """Logs into Moodle in a language-agnostic and execution-mode-agnostic way."""
    print("  • Iniciando processo de login...")
    page.goto(login_url)
    page.wait_for_load_state("domcontentloaded")
    
    try:
        logout_btn = page.locator("#logininsidebaric, button:has-text('Sair'), button:has-text('Log out')").first
        logout_btn.wait_for(state="visible", timeout=2000)
        print("  • Sessão fantasma detectada! Clicando em 'Sair' para limpar...")
        logout_btn.click()
        page.wait_for_load_state("networkidle")
        page.goto(login_url)
        page.wait_for_load_state("domcontentloaded")
    except Exception:
        pass

    print("  • Preenchendo credenciais...")
    page.locator("#username").fill(username)
    
    try:
        page.locator("#password").fill(password)
    except Exception:
        page.locator("input[name='password']").fill(password)
    
    try:
        page.locator("#loginbtn").click(timeout=5000)
        page.wait_for_load_state("networkidle")
    except Exception:
        page.screenshot(path=str(BASE_DIR / "debug_falha_login.png"))
        page.locator("button[type='submit']").click()
        page.wait_for_load_state("networkidle")
        
    print("  ✔ Login realizado com sucesso!")


def download_report(page, url, output_path, login_url, username, password):
    """Accesses a specific URL and manages the download of a single report."""
    print(f"  • Acessando relatório: {url}")
    page.goto(url)
    page.wait_for_load_state("networkidle")

    download_btn = page.get_by_role("button", name="Download")
    
    if "login" in page.url or not download_btn.is_visible():
        print("  • Sessão expirada ou sem permissão. Reconectando...")
        login(page, login_url, username, password)
        page.goto(url)
        page.wait_for_load_state("networkidle")

    try:
        download_btn = page.get_by_role("button", name="Download")
        if download_btn.is_visible():
            with page.expect_download(timeout=15000) as download_info:
                download_btn.click()
            
            download = download_info.value
            download.save_as(str(output_path))
            print(f"  ✔ Sucesso! Salvo em: {output_path}")
        else:
            print(f"  ❌ ERRO: O botão de download não apareceu na página final: {url}", file=sys.stderr)
            
    except Exception as e:
        print(f"  ❌ ERRO: Falha ao baixar o relatório {url}: {e}", file=sys.stderr)


def main(config: Config):
    """Main function that orchestrates Scope 1."""
    print("=" * 80)
    print("▶ [ESCOPO 1] EXTRAÇÃO DE RELATÓRIOS (MOODLE)")
    print("=" * 80)
    
    login_url = config.moodle.login_url
    username = config.moodle.username
    password = config.moodle.password
    moodle_urls = config.moodle.report_urls
    headless = config.moodle.headless
    download_dir = config.moodle.report_download_path

    if not moodle_urls:
        print("  ❌ ERRO: Nenhuma URL de relatório encontrada no settings.json", file=sys.stderr)
        print("=" * 80)
        return
    
    download_dir.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as p:
            chrome_args = ["--disable-blink-features=AutomationControlled"]
            
            if not headless:
                chrome_args.append("--start-maximized")

            browser = p.chromium.launch(headless=headless, args=chrome_args)
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768}
            )
            page = context.new_page()

            login(page, login_url, username, password)

            for index, url in enumerate(moodle_urls, start=1):
                filename = f"relatorio{index}.csv"
                output_path = download_dir / filename
                
                download_report(page, url, output_path, login_url, username, password)
                time.sleep(1.5)
                
        print("\n✔ Escopo 1 finalizado com sucesso!")
    except Exception as e:
        print(f"\n⚠️ Escopo 1 terminou com falhas: {e}", file=sys.stderr)
        
    print("=" * 80)


if __name__ == "__main__":
    loaded_config = Config.load()
    main(loaded_config)