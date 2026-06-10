import os
from pathlib import Path

import escopo1
from dotenv import load_dotenv

# Localiza o arquivo .env na pasta pai
enviroment_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=enviroment_path)

# Configurações globais carregadas do .env
MOODLE_USERNAME = os.getenv("MOODLE_USERNAME")
MOODLE_PASSWORD = os.getenv("MOODLE_PASSWORD")
# TODO: Adicionar outras variáveis globais conforme os próximos escopos demandarem

def executar_escopo_1():
    print("--- [Iniciando Escopo 1] ---")
    escopo1.main()
    print("--- [Escopo 1 Concluído] ---\n")

def executar_escopo_2():
    print("--- [Iniciando Escopo 2] ---")
    # TODO: Implementar a lógica do segundo escopo do pipeline
    print("--- [Escopo 2 Concluído] ---\n")

def executar_escopo_3():
    print("--- [Iniciando Escopo 3] ---")
    # TODO: Implementar a lógica do terceiro escopo do pipeline
    print("--- [Escopo 3 Concluído] ---\n")

def executar_escopo_4():
    print("--- [Iniciando Escopo 4] ---")
    # TODO: Implementar a lógica do quarto escopo do pipeline (geração final do relatório/README)
    print("--- [Escopo 4 Concluído] ---\n")

def main():
    print("=== INICIANDO PIPELINE DE AUTOMATIZAÇÃO ===\n")
    
    # Execução sequencial dos escopos
    executar_escopo_1()
    executar_escopo_2()
    executar_escopo_3()
    executar_escopo_4()
    
    print("=== PIPELINE EXECUTADO COM SUCESSO ===")

if __name__ == "__main__":
    main()