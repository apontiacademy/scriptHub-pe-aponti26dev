import os
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Identifica o caminho do arquivo atual, sobe um nível (para a pasta pai) e encontra o .env
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def fazer_login(page, login_url, username, password):
    """Realiza o login no Moodle de forma agnóstica a idioma e modo de execução."""
    print("[Moodle] Iniciando processo de login...")
    page.goto(login_url)
    page.wait_for_load_state("domcontentloaded")
    
    # -------------------------------------------------------------------------
    # 1. Tratamento do Modal (Lida com Português ou Inglês no Headless)
    # -------------------------------------------------------------------------
    try:
        # Tenta localizar o botão de Sair por texto ou pelo padrão do Moodle
        botao_sair = page.locator("#logininsidebaric, button:has-text('Sair'), button:has-text('Log out')").first
        
        # CORREÇÃO: wait_for aceita timeout para checagem ativa; is_visible não.
        botao_sair.wait_for(state="visible", timeout=2000)
        
        print("[Moodle] Sessão fantasma detectada! Clicando em 'Sair' para limpar...")
        botao_sair.click()
        page.wait_for_load_state("networkidle")
        page.goto(login_url)
        page.wait_for_load_state("domcontentloaded")
    except Exception:
        # Se não encontrar o botão em 2s, segue o fluxo normal
        pass

    # -------------------------------------------------------------------------
    # 2. Preenchimento por IDs Únicos (Imune a duplicidade e idiomas)
    # -------------------------------------------------------------------------
    print("[Moodle] Preenchendo credenciais...")
    
    # Usando o caractere '#' miramos direto no ID único do HTML
    page.locator("#username").fill(username)
    
    # Fazemos o mesmo para a senha usando o ID padrão do Moodle
    try:
        page.locator("#password").fill(password)
    except Exception:
        # Fallback de segurança caso a estrutura mude
        page.locator("input[name='password']").fill(password)
    
    # Clica no botão de envio usando o ID padrão do Moodle (#loginbtn)
    try:
        page.locator("#loginbtn").click(timeout=5000)
        page.wait_for_load_state("networkidle")
    except Exception:
        # Se falhar, tira o print de debug e tenta o clique alternativo
        page.screenshot(path="debug_falha_login.png")
        page.locator("button[type='submit']").click()
        page.wait_for_load_state("networkidle")
        
    print("[Moodle] Login realizado com sucesso!")


def baixar_relatorio(page, url, caminho_final, login_url, username, password):
    """Acessa a URL específica e gerencia o download de um único relatório."""
    print(f"[Moodle] Acessando relatório: {url}")
    page.goto(url)
    
    # Espera o carregamento completo da rede para garantir a renderização dos botões
    page.wait_for_load_state("networkidle")

    botao_download = page.get_by_role("button", name="Download")
    
    # --- VERIFICAÇÃO DE SESSÃO EXPIRADA ---
    if "login" in page.url or not botao_download.is_visible():
        print("[Moodle] Sessão expirada ou sem permissão. Reconectando...")
        fazer_login(page, login_url, username, password)
        
        # Volta para a página do relatório após o re-login
        page.goto(url)
        page.wait_for_load_state("networkidle")

    try:
        # Re-seleciona o botão após garantir estabilidade da página
        botao_download = page.get_by_role("button", name="Download")
        
        if botao_download.is_visible():
            # Timeout de segurança de 15 segundos para o disparo do download
            with page.expect_download(timeout=15000) as download_info:
                botao_download.click()
            
            download = download_info.value
            download.save_as(caminho_final)
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
    download_dir = os.getenv("MOODLE_DOWNLOAD_DIR", "./relatorios_moodle")
    urls_raw = os.getenv("MOODLE_REPORT_URLS", "")
    headless = os.getenv("MOODLE_HEADLESS", "true").lower() == "true"
    
    if not urls_raw:
        print("[Moodle] [Erro] Nenhuma URL de relatório encontrada no .env")
        return
    
    urls = [url.strip() for url in urls_raw.split(",") if url.strip()]
    os.makedirs(download_dir, exist_ok=True)

    # Inicialização do Playwright
    with sync_playwright() as p:
        # Argumentos stealth aplicados globalmente para evitar detecção
        chrome_args = ["--disable-blink-features=AutomationControlled"]
        if headless:
            chrome_args.append("--start-maximized")

        browser = p.chromium.launch(headless=headless, args=chrome_args)
        
        # Mantendo User-Agent e Viewport idênticos em ambos os modos para evitar comportamentos fantasmas
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768}
        )
        page = context.new_page()

        # Login inicial obrigatório
        fazer_login(page, login_url, username, password)

        # Loop de downloads
        for index, url in enumerate(urls, start=1):
            nome_arquivo = f"relatorio{index}.csv"
            caminho_final = os.path.join(download_dir, nome_arquivo)
            
            baixar_relatorio(page, url, caminho_final, login_url, username, password)
            
            # Pausa estratégica para não sobrecarregar o servidor do Moodle
            time.sleep(1.5)


if __name__ == "__main__":
    main()