import scripthub.scripts.auditar_relatorios.backup as backup
import scripthub.scripts.auditar_relatorios.download_de_relatorios as download_de_relatorios
import scripthub.scripts.auditar_relatorios.integracao_google_sheets as integracao_google_sheets
import scripthub.scripts.auditar_relatorios.middleware_analise_de_relatorios as middleware_analise_de_relatorios

from .config import Config


def main():
    # Carrega as configurações unificadas (GUI settings.json + .env) uma única vez
    config = Config.load()

    # Banner de abertura do Pipeline Geral
    print("=" * 80)
    print("▶ INICIANDO PIPELINE DE AUTOMATIZAÇÃO DE RELATÓRIOS")
    print("=" * 80)
    print()  # Quebra de linha para dar respiro visual

    # Injetando a mesma instância de 'config' em todos os escopos sequencialmente
    download_de_relatorios.main(config)
    print()

    middleware_analise_de_relatorios.main(config)
    print()

    integracao_google_sheets.main(config)
    print()

    backup.main(config)
    print()

    # Banner de encerramento de sucesso absoluto
    print("=" * 80)
    print("✔ PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
