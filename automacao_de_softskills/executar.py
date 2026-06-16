import requests
from .download_softskills import (
    login,
    download_bootcamp_data,
)
from .processamento import (
    get_approved_courses,
    build_softskills_resultado,
    build_aprovados_bootcamp,
)
from .config import Config


def main():
    """Função principal que orquestra todo o pipeline de softskills."""
    print("=" * 80)
    print("▶ INICIANDO PIPELINE DE AUTOMATIZAÇÃO DE SOFTSKILLS")
    print("=" * 80)
    print()  # Quebra de linha para dar respiro visual

    # Carrega as configurações unificadas (GUI settings.json + .env) uma única vez
    config = Config.load()

    # Cria uma sessão requests para ser reutilizada
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    try:
        # 1. Autenticação e download de dados do bootcamp
        print("=" * 80)
        print("▶ [ETAPA 1] DOWNLOAD DE DADOS DO BOOTCAMP")
        print("=" * 80)

        login(session, config)
        bootcamp_data = download_bootcamp_data(session, config)

        # 2. Processamento e geração de relatórios consolidados
        print("\n" + "=" * 80)
        print("▶ [ETAPA 2] PROCESSAMENTO DE DADOS")
        print("=" * 80)

        softskills_lookup = build_softskills_resultado(config, bootcamp_data)

        # 3. Coleta e processamento de dados de aprovados
        print("\n" + "=" * 80)
        print("▶ [ETAPA 3] PROCESSAMENTO DE APROVADOS")
        print("=" * 80)

        approved_courses = get_approved_courses(session, config)
        build_aprovados_bootcamp(config, session, approved_courses, softskills_lookup)

        # Banner de encerramento de sucesso absoluto
        print("\n" + "=" * 80)
        print("✔ PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
        print("=" * 80)

    except Exception as e:
        print(f"\n⚠️ PIPELINE TERMINOU COM FALHAS: {e}")
        print("=" * 80)
        raise


if __name__ == "__main__":
    main()
