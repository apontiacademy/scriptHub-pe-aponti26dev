import automacao.escopo1 as escopo1
import automacao.escopo2 as escopo2
import automacao.escopo3 as escopo3  # 🚀 O novo integrante do time


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