import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from scripthub.services import log

from .config import Config

BASE_DIR = Path(__file__).resolve().parent


def realizar_login(page, login_url, usuario, senha):
    """Realiza o login no Moodle de forma agnóstica a idioma e modo de execução."""
    log.passo("Iniciando processo de login...")
    page.goto(login_url)
    page.wait_for_load_state("domcontentloaded")

    try:
        # Trata possíveis sessões ativas sobrepostas
        botao_sair = page.locator("#logininsidebaric, button:has-text('Sair'), button:has-text('Log out')").first
        botao_sair.wait_for(state="visible", timeout=2000)
        log.passo("Sessão fantasma detectada! Clicando em 'Sair' para limpar...")
        botao_sair.click()
        page.wait_for_load_state("networkidle")
        page.goto(login_url)
        page.wait_for_load_state("domcontentloaded")
    except Exception:
        pass

    log.passo("Preenchendo credenciais...")
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

    log.ok("Login realizado com sucesso!")


def baixar_relatorio(page, url, caminho_saida, login_url, usuario, senha):
    """Acessa uma URL específica e gerencia o download de um único relatório."""
    log.passo(f"Acessando relatório: {url}")
    page.goto(url)
    page.wait_for_load_state("networkidle")

    botao_download = page.get_by_role("button", name="Download")

    if "login" in page.url or not botao_download.is_visible():
        log.passo("Sessão expirada ou sem permissão. Reconectando...")
        realizar_login(page, login_url, usuario, senha)
        page.goto(url)
        page.wait_for_load_state("networkidle")

    try:
        botao_download = page.get_by_role("button", name="Download")
        if botao_download.is_visible():
            with page.expect_download(timeout=15000) as informacao_download:
                botao_download.click()

            download = informacao_download.value
            # Conversão explícita de Path para string para execução cross-platform robusta
            download.save_as(str(caminho_saida))
            log.ok(f"Sucesso! Salvo em: {caminho_saida}")
        else:
            log.erro(f"O botão de download não apareceu na página final: {url}")

    except Exception as e:
        log.erro(f"Falha ao baixar o relatório {url}: {e}")


def main(config: Config):
    """Função principal que orquestra o Escopo 1."""
    login_url = config.moodle.url_login
    usuario = config.moodle.usuario
    senha = config.moodle.senha
    urls_moodle = config.moodle.urls_relatorios
    headless = config.moodle.headless
    diretorio_download = config.moodle.caminho_download_relatorio

    if not urls_moodle:
        raise RuntimeError("Nenhuma URL de relatório encontrada no settings.json")

    # Cria a estrutura de diretórios usando o objeto Path nativo vindo do Config
    diretorio_download.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as p:
            chrome_args = ["--disable-blink-features=AutomationControlled"]

            # --start-maximized requer headless=False para funcionar corretamente
            if not headless:
                chrome_args.append("--start-maximized")

            navegador = p.chromium.launch(headless=headless, args=chrome_args)

            contexto = navegador.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 "
                "Safari/537.36",
                viewport={"width": 1366, "height": 768},
            )
            pagina = contexto.new_page()

            realizar_login(pagina, login_url, usuario, senha)

            # Itera sobre a lista limpa vinda do Config
            for indice, url in enumerate(urls_moodle, start=1):
                nome_arquivo = f"relatorio{indice}.csv"
                caminho_saida = diretorio_download / nome_arquivo
                baixar_relatorio(pagina, url, caminho_saida, login_url, usuario, senha)
                time.sleep(1.5)

        log.ok("Escopo 1 finalizado com sucesso!")
    except Exception as e:
        log.erro(f"Escopo 1 terminou com falhas: {e}")
