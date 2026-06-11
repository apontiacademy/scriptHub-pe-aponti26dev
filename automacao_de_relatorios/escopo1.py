import os
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# =========================================================================
# ANCORAGEM DINÂMICA DE ESCOPO
# =========================================================================
# Caminho absoluto da pasta 'automacao_de_relatorios'
PASTA_ESCOPO = Path(__file__).resolve().parent

# Força o carregamento do .env que está EXCLUSIVAMENTE dentro desta pasta
env_path = PASTA_ESCOPO / ".env"
load_dotenv(dotenv_path=env_path, override=True)


def fazer_login(page, login_url, username, password):
    """Realiza o login no Moodle de forma agnóstica a idioma e modo de execução."""
    print("[Moodle] Iniciando processo de login...")
    page.goto(login_url)
    page.wait_for_load_state("domcontentloaded")
    
    try:
        botao_sair = page.locator("#logininsidebaric, button:has-text('Sair'), button:has-text('Log out')").first
        botao_sair.wait_for(state="visible", timeout=2000)
        print("[Moodle] Sessão fantasma detectada! Clicando em 'Sair' para limpar...")
        botao_sair.click()
        page.wait_for_load_state("networkidle")
        page.goto(login_url)
        page.wait_for_load_state("domcontentloaded")
    except Exception:
        pass

    print("[Moodle] Preenchendo credenciais...")
    page.locator("#username").fill(username)
    
    try:
        page.locator("#password").fill(password)
    except Exception:
        page.locator("input[name='password']").fill(password)
    
    try:
        page.locator("#loginbtn").click(timeout=5000)
        page.wait_for_load_state("networkidle")
    except Exception:
        page.screenshot(path=str(PASTA_ESCOPO / "debug_falha_login.png"))
        page.locator("button[type='submit']").click()
        page.wait_for_load_state("networkidle")
        
    print("[Moodle] Login realizado com sucesso!")


def baixar_relatorio(page, url, caminho_final, login_url, username, password):
    """Acessa a URL específica e gerencia o download de um único relatório."""
    print(f"[Moodle] Acessando relatório: {url}")
    page.goto(url)
    page.wait_for_load_state("networkidle")

    botao_download = page.get_by_role("button", name="Download")
    
    if "login" in page.url or not botao_download.is_visible():
        print("[Moodle] Sessão expirada ou sem permissão. Reconectando...")
        fazer_login(page, login_url, username, password)
        page.goto(url)
        page.wait_for_load_state("networkidle")

    try:
        botao_download = page.get_by_role("button", name="Download")
        if botao_download.is_visible():
            with page.expect_download(timeout=15000) as download_info:
                botao_download.click()
            
            download = download_info.value
            download.save_as(str(caminho_final))
            print(f"[Moodle] Sucesso! Salvo em: {caminho_final}")
        else:
            print(f"[Moodle] [Erro] O botão de download não apareceu na página final: {url}")
            
    except Exception as e:
        print(f"[Moodle] [Erro] Falha ao baixar o relatório {url}: {e}")


def main():
    """Função principal que orquestra o Escopo 1."""
    login_url = os.getenv("MOODLE_LOGIN_URL")
    username = os.getenv("MOODLE_USERNAME")
    password = os.getenv("MOODLE_PASSWORD")
    urls_raw = os.getenv("MOODLE_REPORT_URLS", "")
    headless = os.getenv("MOODLE_HEADLESS", "true").lower() == "true"
    
    # Pegamos o valor bruto do .env (ex: './dados/relatorios/')
    download_dir_raw = os.getenv("MOODLE_DOWNLOAD_DIR", "./dados/relatorios/")
    
    # TRATAMENTO DOS PATHS RELATIVOS: 
    # Remove o './' inicial se existir e força a criação DENTRO de automacao_de_relatorios/
    diretorio_limpo = download_dir_raw.lstrip("./")
    download_dir = (PASTA_ESCOPO / diretorio_limpo).resolve()

    if not urls_raw:
        print("[Moodle] [Erro] Nenhuma URL de relatório encontrada no .env")
        return
    
    urls = [url.strip() for url in urls_raw.split(",") if url.strip()]
    
    # Cria a estrutura de pastas (ex: automacao_de_relatorios/dados/relatorios/)
    download_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        chrome_args = ["--disable-blink-features=AutomationControlled"]
        if headless:
            chrome_args.append("--start-maximized")

        browser = p.chromium.launch(headless=headless, args=chrome_args)
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768}
        )
        page = context.new_page()

        fazer_login(page, login_url, username, password)

        for index, url in enumerate(urls, start=1):
            nome_arquivo = f"relatorio{index}.csv"
            # Monta o caminho final absoluto concatenando na nossa pasta alvo tratada
            caminho_final = download_dir / nome_arquivo
            
            baixar_relatorio(page, url, caminho_final, login_url, username, password)
            time.sleep(1.5)


if __name__ == "__main__":
    main()