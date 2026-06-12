
import automacao_de_relatorios.escopo1 as escopo1
import automacao_de_relatorios.escopo2 as escopo2
import automacao_de_relatorios.escopo3 as escopo3
import automacao_de_relatorios.escopo4 as escopo4

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
    escopo1.main(config)
    print()

    escopo2.main(config)
    print()

    escopo3.main(config)
    print()

    escopo4.main(config)
    print()
    
    # Banner de encerramento de sucesso absoluto
    print("=" * 80)
    print("✔ PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
    print("=" * 80)


if __name__ == "__main__":
    main()