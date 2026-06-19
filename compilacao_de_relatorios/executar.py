import compilacao_de_relatorios.compilar_pdfs as compilar_pdfs
import compilacao_de_relatorios.download_de_relatorios as download_de_relatorios

from .config import Config


def main():
    config = Config.load()

    print("=" * 80)
    print("▶ INICIANDO PIPELINE DE COMPILAÇÃO DE RELATÓRIOS")
    print("=" * 80)
    print()

    download_de_relatorios.main(config)
    print()

    compilar_pdfs.main(config)
    print()

    print("=" * 80)
    print("✔ PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
