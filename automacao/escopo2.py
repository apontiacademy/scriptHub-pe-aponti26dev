# automacao/escopo2.py
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Garante que a raiz do projeto esteja no sys.path para encontrar a pasta 'analise'
raiz_projeto = Path(__file__).resolve().parent.parent
if str(raiz_projeto) not in sys.path:
    sys.path.append(str(raiz_projeto))

# Importa o main do seu script de análise
from analise.pente_fino import main as executar_analise_core  # noqa: E402

# Carrega o .env localizado na raiz do projeto
env_path = raiz_projeto / '.env'
load_dotenv(dotenv_path=env_path)


def main():
    print("\n--- [Middleware Escopo 2: Mapeando Variáveis de Ambiente] ---")
    
    # Captura os dados configurados no seu .env
    pasta_origem = os.getenv("MOODLE_DOWNLOAD_DIR")
    planilha_alunos = os.getenv("MOODLE_STUDENTS_CSV")
    modo_analise = os.getenv("MOODLE_ANALYSIS_MODO", "nao_feitos")
    arquivo_saida = os.getenv("MOODLE_ANALYSIS_OUTPUT_CSV", "resultado.csv")

    # Monta a lista de argumentos exatamente como a CLI do pente_fino espera
    argumentos_cli = []
    if pasta_origem:
        argumentos_cli.extend(["-d", pasta_origem])
    if planilha_alunos:
        argumentos_cli.extend(["-p", planilha_alunos])
    if modo_analise:
        argumentos_cli.extend(["-m", modo_analise])
    if arquivo_saida:
        argumentos_cli.extend(["-o", arquivo_saida])

    print(f"[Middleware] Injetando argumentos no Core: {' '.join(argumentos_cli)}")
    
    # --- ABORDAGEM LIMPA ---
    # Enviamos os argumentos coletados do .env diretamente para o core,
    # sem precisar mexer ou sujar o sys.argv global do Python.
    executar_analise_core(argumentos_cli)


if __name__ == "__main__":
    main()