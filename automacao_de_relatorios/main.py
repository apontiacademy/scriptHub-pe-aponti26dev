from config import Config

# Imports all packaged scopes with English aliases
import automacao_de_relatorios.scope1 as scope1
import automacao_de_relatorios.scope2 as scope2
import automacao_de_relatorios.scope3 as scope3
import automacao_de_relatorios.scope4 as scope4


def main():
    # Loads unified configurations (GUI settings.json + .env) once
    config = Config.load()

    # Banner de abertura do Pipeline Geral
    print("=" * 80)
    print("▶ INICIANDO PIPELINE DE AUTOMATIZAÇÃO DE RELATÓRIOS")
    print("=" * 80)
    print()  # Quebra de linha para dar respiro visual

    # CORRIGIDO: Injetando a mesma instância de 'config' em todos os escopos sequencialmente
    scope1.main(config)
    print()

    scope2.main(config)
    print()

    scope3.main(config)
    print()

    scope4.main(config)
    print()
    
    # Banner de encerramento de sucesso absoluto
    print("=" * 80)
    print("✔ PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
    print("=" * 80)


if __name__ == "__main__":
    main()