import scripthub.scripts.compilacao_de_relatorios.compilar_pdfs as compilar_pdfs
import scripthub.scripts.compilacao_de_relatorios.download_de_relatorios as download_de_relatorios

from scripthub.services import log

from .config import Config


def main():
    config = Config.load()

    log.secao("PIPELINE DE COMPILAÇÃO DE RELATÓRIOS")

    download_de_relatorios.main(config)

    compilar_pdfs.main(config)

    log.ok("PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")


if __name__ == "__main__":
    import sys
    try:
        main()
    except Exception as e:
        log.erro(str(e))
        sys.exit(1)
