import automacao_de_relatorios.escopo1 as escopo1
import automacao_de_relatorios.escopo2 as escopo2
import automacao_de_relatorios.escopo3 as escopo3


def main():
    print("=== INICIANDO PIPELINE DE AUTOMATIZAÇÃO ===")

    print("\n--- [Iniciando Escopo 1: Automação de Downloads] ---")
    escopo1.main()
    
    print("\n--- [Iniciando Escopo 2: Middleware de Processamento] ---")
    escopo2.main()

    print("\n--- [Iniciando Escopo 3: Integração com Google Sheets] ---")
    escopo3.main()
    
    print("\n=== PIPELINE DE AUTOMATIZAÇÃO CONCLUÍDO COM SUCESSO ===")


if __name__ == "__main__":
    main()