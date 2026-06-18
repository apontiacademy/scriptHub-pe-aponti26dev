import scripthub.scripts.auditar_frequencias.exportar_frequencias as exportar_frequencias
import scripthub.scripts.auditar_frequencias.integracao_google_sheets as integracao_google_sheets

from .config import Config


def main():
    """Ponto de entrada principal do pipeline de exportação de frequências."""
    config = Config.load()

    print("=" * 80)
    print("▶ INICIANDO PIPELINE DE EXPORTAÇÃO DE FREQUÊNCIAS")
    print("=" * 80)
    print()

    exportar_frequencias.main(config)
    print()

    integracao_google_sheets.main(config)
    print()

    print("=" * 80)
    print("✔ PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
