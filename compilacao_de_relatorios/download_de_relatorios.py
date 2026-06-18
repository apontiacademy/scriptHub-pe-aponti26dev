import sys
import time
from pathlib import Path

import questionary
from playwright.sync_api import sync_playwright

from .config import Config

BASE_DIR = Path(__file__).resolve().parent


def _caminho_relatorio(nome_mes: str, diretorio_download: Path) -> Path:
    slug = nome_mes.lower().replace(" ", "_")
    return diretorio_download / f"{slug}.csv"


def _relatorios_existentes(meses: dict[str, str], diretorio_download: Path) -> dict[str, Path]:
    return {nome_mes: _caminho_relatorio(nome_mes, diretorio_download) for nome_mes in meses}


def _todos_relatorios_existem(caminhos: dict[str, Path]) -> bool:
    return bool(caminhos) and all(caminho.exists() for caminho in caminhos.values())


def _perguntar_baixar_novamente() -> bool:
    resposta = questionary.confirm(
        "Relatórios já encontrados em dados/relatorios. Deseja baixá-los novamente?",
        default=False,
    ).ask()
    return resposta is True


def realizar_login(page, login_url, usuario, senha):
    print("  • Iniciando processo de login...")
    page.goto(login_url)
    page.wait_for_load_state("domcontentloaded")

    try:
        botao_sair = page.locator("#logininsidebaric, button:has-text('Sair'), button:has-text('Log out')").first
        botao_sair.wait_for(state="visible", timeout=2000)
        print("  • Sessão fantasma detectada! Clicando em 'Sair' para limpar...")
        botao_sair.click()
        page.wait_for_load_state("networkidle")
        page.goto(login_url)
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


def baixar_relatorio(page, url, caminho_saida, login_url, usuario, senha):
    print(f"  • Acessando relatório: {url}")
    page.goto(url)
    page.wait_for_load_state("networkidle")

    botao_download = page.get_by_role("button", name="Download")

    if "login" in page.url or not botao_download.is_visible():
        print("  • Sessão expirada ou sem permissão. Reconectando...")
        realizar_login(page, login_url, usuario, senha)
        page.goto(url)
        page.wait_for_load_state("networkidle")

    try:
        botao_download = page.get_by_role("button", name="Download")
        if botao_download.is_visible():
            with page.expect_download(timeout=15000) as informacao_download:
                botao_download.click()

            download = informacao_download.value
            download.save_as(str(caminho_saida))
            print(f"  ✔ Sucesso! Salvo em: {caminho_saida}")
        else:
            print(
                f"  ❌ ERRO: O botão de download não apareceu na página final: {url}",
                file=sys.stderr,
            )

    except Exception as e:
        print(f"  ❌ ERRO: Falha ao baixar o relatório {url}: {e}", file=sys.stderr)


def main(config: Config):
    print("=" * 80)
    print("▶ [ESCOPO 1] DOWNLOAD DE RELATÓRIOS POR MÊS (MOODLE)")
    print("=" * 80)

    meses = config.moodle.meses
    login_url = config.moodle.url_login
    usuario = config.moodle.usuario
    senha = config.moodle.senha
    headless = config.moodle.headless
    diretorio_download = config.moodle.caminho_download

    if not meses:
        print(
            "  ❌ ERRO: Nenhum mês configurado em settings.json (moodle.meses)",
            file=sys.stderr,
        )
        print("=" * 80)
        return

    diretorio_download.mkdir(parents=True, exist_ok=True)

    caminhos = _relatorios_existentes(meses, diretorio_download)
    if _todos_relatorios_existem(caminhos):
        print("\n  • Relatórios CSV já existem em dados/relatorios:")
        for nome_mes, caminho in caminhos.items():
            print(f"    - {nome_mes}: {caminho.name}")

        if not _perguntar_baixar_novamente():
            print("\n  • Download ignorado. Usando arquivos existentes.")
            print("=" * 80)
            return

    try:
        with sync_playwright() as p:
            chrome_args = ["--disable-blink-features=AutomationControlled"]

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

            for nome_mes, url in meses.items():
                caminho_saida = _caminho_relatorio(nome_mes, diretorio_download)

                print(f"\n  → Mês: {nome_mes}")
                baixar_relatorio(pagina, url, caminho_saida, login_url, usuario, senha)
                time.sleep(1.5)

        print("\n✔ Escopo 1 finalizado com sucesso!")
    except Exception as e:
        print(f"\n⚠️ Escopo 1 terminou com falhas: {e}", file=sys.stderr)

    print("=" * 80)


if __name__ == "__main__":
    configuracao_carregada = Config.load()
    main(configuracao_carregada)
