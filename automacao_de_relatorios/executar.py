import automacao_de_relatorios.escopo1 as escopo1
import automacao_de_relatorios.escopo2 as escopo2
import automacao_de_relatorios.escopo3 as escopo3
import automacao_de_relatorios.escopo4 as escopo4


def main():
    # Banner de abertura do Pipeline Geral
    print("=" * 80)
    print("▶ INICIANDO PIPELINE DE AUTOMATIZAÇÃO DE RELATÓRIOS")
    print("=" * 80)
    print()  # Quebra de linha para dar respiro visual

    # Execução sequencial dos escopos empacotados
    escopo1.main()
    print()

    escopo2.main()
    print()

    escopo3.main()
    print()

    escopo4.main()
    print()

    # Banner de encerramento de sucesso absoluto
    print("=" * 80)
    print("✔ PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
