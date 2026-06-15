import automacao_de_frequencias.exportar_frequencias as exportar_frequencias

from .config import Config


def main():
    config = Config.load()

    print("=" * 80)
    print("▶ INICIANDO PIPELINE DE EXPORTAÇÃO DE FREQUÊNCIAS")
    print("=" * 80)
    print()

    exportar_frequencias.main(config)
    print()

    print("=" * 80)
    print("✔ PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
