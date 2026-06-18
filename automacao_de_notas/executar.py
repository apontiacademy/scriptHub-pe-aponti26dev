import csv
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from . import integracao_drive
from . import scraper
from .config import Config

DIRETORIO_BASE = Path(__file__).resolve().parent


def _norm(texto: str) -> str:
    return re.sub(r"\s+", " ", texto.strip()).lower()


_CAMPOS_ID = ["Professor", "Turma", "Dias", "Horário", "Nome Turma", "Tipo", "Aluno", "E-mail"]


def _escrever_csv(caminho: Path, dados: list[dict], atividades: list[str]) -> int:
    fieldnames = _CAMPOS_ID + [f"Nota {at}" for at in atividades]
    rows: list[dict] = []

    for dado in dados:
        turma = dado["turma"]
        notas = dado["notas"]
        for part in dado["participantes"]:
            email = part["email"]
            notas_part = notas.get(email) or notas.get(_norm(part["nome"]), {})
            row: dict = {
                "Professor": turma["professor"],
                "Turma": turma["turma"],
                "Dias": turma["dias"],
                "Horário": turma["horario"],
                "Nome Turma": turma["nome_moodle"],
                "Tipo": turma["tipo"],
                "Aluno": part["nome"],
                "E-mail": email,
            }
            for at in atividades:
                row[f"Nota {at}"] = notas_part.get(at, "0")
            rows.append(row)

    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


# ── Helpers de cache ───────────────────────────────────────────────────────────

def _dir_cache(config: Config) -> Path:
    d = config.output_dir / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _path_urls(config: Config) -> Path:
    return _dir_cache(config) / "turmas_urls.json"


def _path_turma(config: Config, num: str) -> Path:
    return _dir_cache(config) / f"turma_{num}.json"


def _urls_em_cache(config: Config) -> bool:
    return _path_urls(config).exists()


def _turma_completa(config: Config, num: str) -> bool:
    """Turma completa = cache existe E tem atividades (grader report não veio vazio)."""
    p = _path_turma(config, num)
    if not p.exists():
        return False
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return bool(data.get("atividades"))
    except Exception:
        return False


def _salvar_urls(config: Config, turmas: list[dict]) -> None:
    _path_urls(config).write_text(
        json.dumps(turmas, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _carregar_urls(config: Config) -> list[dict]:
    return json.loads(_path_urls(config).read_text(encoding="utf-8"))


def _salvar_turma(config: Config, num: str, participantes: list, atividades: list, notas: dict) -> None:
    _path_turma(config, num).write_text(
        json.dumps(
            {"participantes": participantes, "atividades": atividades, "notas": notas},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _carregar_turma(config: Config, num: str) -> tuple[list, list, dict]:
    data = json.loads(_path_turma(config, num).read_text(encoding="utf-8"))
    return data["participantes"], data["atividades"], data["notas"]


# ── Pipeline ───────────────────────────────────────────────────────────────────

def main() -> None:
    config = Config.load()

    print("=" * 80)
    print("▶ INICIANDO PIPELINE DE NOTAS FAP 2026")
    print("=" * 80)
    print()

    config.output_dir.mkdir(parents=True, exist_ok=True)
    _dir_cache(config)

    # ── 1. URLs das turmas (cache) ────────────────────────────────────────────
    if _urls_em_cache(config):
        print("[CACHE] URLs das turmas já mapeadas.")
        turmas = _carregar_urls(config)
        print(f"  {len(turmas)} turma(s) carregada(s) do cache")
    else:
        turmas = None  # será preenchido pelo browser

    # ── 2. Decide quais turmas precisam de scraping ───────────────────────────
    turmas_a_scraping: list[dict] = []
    if turmas is not None:
        turmas_a_scraping = [t for t in turmas if not _turma_completa(config, t["turma"])]
        n_cache = len(turmas) - len(turmas_a_scraping)
        if n_cache:
            print(f"[CACHE] {n_cache} turma(s) com dados completos — pulando scraping.")
        if turmas_a_scraping:
            print(f"  → {len(turmas_a_scraping)} turma(s) precisam ser baixadas.")

    precisa_browser = turmas is None or bool(turmas_a_scraping)

    # ── 3. Scraping (somente se necessário) ───────────────────────────────────
    if precisa_browser:
        print()
        try:
            with sync_playwright() as p:
                chrome_args = ["--disable-blink-features=AutomationControlled"]
                if not config.moodle.headless:
                    chrome_args.append("--start-maximized")

                navegador = p.chromium.launch(headless=config.moodle.headless, args=chrome_args)
                contexto = navegador.new_context(
                    user_agent=(
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1366, "height": 768},
                )
                pagina = contexto.new_page()

                scraper.realizar_login(
                    pagina, config.moodle.url_login, config.moodle.usuario, config.moodle.senha
                )
                print()

                # Descoberta de URLs (primeira execução)
                if turmas is None:
                    print("Buscando turmas...")
                    turmas = scraper.get_turmas(pagina, config.moodle.url_turmas)
                    if not turmas:
                        print("❌ Nenhuma turma encontrada.", file=sys.stderr)
                        navegador.close()
                        return
                    _salvar_urls(config, turmas)
                    print(f"  {len(turmas)} turma(s) mapeada(s)")
                    print()
                    turmas_a_scraping = [t for t in turmas if not _turma_completa(config, t["turma"])]

                # Scraping por turma
                total = len(turmas_a_scraping)
                for i, turma in enumerate(turmas_a_scraping, 1):
                    print(f"[{i}/{total}] {turma['nome_moodle']}")

                    print("  • Extraindo participantes...")
                    participantes = scraper.get_participantes(pagina, turma["url"], config.moodle.url)
                    print(f"    {len(participantes)} participante(s)")

                    print("  • Extraindo notas...")
                    atividades, notas = scraper.get_notas(pagina, turma["url"], config.moodle.url)
                    print(f"    {len(atividades)} atividade(s) | {len(notas)} aluno(s) com nota")

                    _salvar_turma(config, turma["turma"], participantes, atividades, notas)
                    time.sleep(1.0)

                navegador.close()

        except Exception as e:
            print(f"\n❌ Erro durante o scraping: {e}", file=sys.stderr)
            raise

    print()

    # ── 4. Agrega dados do cache ──────────────────────────────────────────────
    print("Agregando dados...")

    vistas_atividades: list[str] = []
    dados_turmas: list[dict] = []

    for turma in turmas:
        participantes, atividades, notas = _carregar_turma(config, turma["turma"])

        for at in atividades:
            if at not in vistas_atividades:
                vistas_atividades.append(at)

        dados_turmas.append(
            {"turma": turma, "participantes": participantes, "notas": notas, "atividades": atividades}
        )

    todas_atividades = vistas_atividades

    # ── 5. Montar CSVs ────────────────────────────────────────────────────────
    print("Montando planilhas...")

    turmas_sem_notas = [
        dado["turma"]["nome_moodle"] for dado in dados_turmas if not dado["atividades"]
    ]

    if turmas_sem_notas:
        txt_path = config.output_dir / "sem_notas.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Turmas sem notas registradas no momento da extração:\n\n")
            for nome in turmas_sem_notas:
                f.write(f"  - {nome}\n")
            f.write("\nNestas turmas todas as colunas de nota foram preenchidas com 0.\n")
        print(f"⚠ {len(turmas_sem_notas)} turma(s) sem notas → {txt_path}")

    _SLUG_TIPO = {
        "DevOps": "devops",
        "Análise de Dados": "dados",
        "Testes de Software": "testes",
    }

    csvs_gerados: list[Path] = []

    # CSV geral — union de todas as atividades de todas as trilhas
    csv_geral = config.output_dir / "fap26_geral.csv"
    n_geral = _escrever_csv(csv_geral, dados_turmas, todas_atividades)
    print(f"✓ {csv_geral.name} — {n_geral} linha(s) | {len(todas_atividades)} coluna(s) de nota")
    csvs_gerados.append(csv_geral)

    # CSVs por tipo — apenas as colunas daquele tipo
    tipos_dados: dict[str, dict] = {}
    for dado in dados_turmas:
        tipo = dado["turma"]["tipo"]
        if tipo not in tipos_dados:
            tipos_dados[tipo] = {"registros": [], "atividades": []}
        tipos_dados[tipo]["registros"].append(dado)
        for at in dado["atividades"]:
            if at not in tipos_dados[tipo]["atividades"]:
                tipos_dados[tipo]["atividades"].append(at)

    for tipo, info in tipos_dados.items():
        slug = _SLUG_TIPO.get(tipo, tipo.lower().replace(" ", "_"))
        csv_tipo = config.output_dir / f"fap26_{slug}.csv"
        n = _escrever_csv(csv_tipo, info["registros"], info["atividades"])
        print(f"✓ {csv_tipo.name} — {n} linha(s) | {len(info['atividades'])} coluna(s) de nota  [{tipo}]")
        csvs_gerados.append(csv_tipo)

    print()

    # ── 6. Upload para o Drive ────────────────────────────────────────────────
    print("Enviando para o Google Drive...")
    falhas: list[str] = []
    for csv_path in csvs_gerados:
        print(f"  → {csv_path.name}")
        try:
            integracao_drive.upload_to_drive(str(csv_path), config)
        except Exception as e:
            print(f"  ❌ Erro ao enviar {csv_path.name}: {e}", file=sys.stderr)
            falhas.append(csv_path.name)
    if falhas:
        print(f"\n⚠ {len(falhas)} arquivo(s) não enviado(s): {', '.join(falhas)}", file=sys.stderr)
    print()

    print("=" * 80)
    print("✔ PIPELINE CONCLUÍDO COM SUCESSO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
