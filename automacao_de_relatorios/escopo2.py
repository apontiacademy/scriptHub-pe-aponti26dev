import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# =========================================================================
# ANCORAGEM DINÂMICA DE ESCOPO
# =========================================================================
# Caminho absoluto da pasta 'automacao_de_relatorios'
PASTA_ESCOPO = Path(__file__).resolve().parent

# Força a inclusão da raiz (ou da pasta correta) no sys.path se o core precisar
if str(PASTA_ESCOPO.parent) not in sys.path:
    sys.path.append(str(PASTA_ESCOPO.parent))

# Importa o main do seu script de análise (ajuste o path de import se necessário)
from auditoria_de_relatorios.executar import main as executar_analise_core  # noqa: E402

# Força o carregamento do .env que está EXCLUSIVAMENTE dentro desta pasta de automação
env_path = PASTA_ESCOPO / ".env"
load_dotenv(dotenv_path=env_path, override=True)


def tratar_caminho_relativo(valor_env: str | None) -> str | None:
    """Se o caminho for relativo (começar com ./), ancora ele dentro da PASTA_ESCOPO."""
    if not valor_env:
        return None
    if valor_env.startswith("./") or valor_env.startswith("../"):
        # Remove o './' ou limpa e resolve baseado na pasta do escopo
        caminho_limpo = valor_env.lstrip("./")
        return str((PASTA_ESCOPO / caminho_limpo).resolve())
    return str(Path(valor_env).resolve())


def main():
    print("\n--- [Middleware Escopo 2: Mapeando Variáveis de Ambiente] ---")
    
    # Captura os dados configurados no seu .env local e trata os caminhos dinamicamente
    pasta_origem_raw = os.getenv("MOODLE_DOWNLOAD_DIR")
    planilha_alunos_raw = os.getenv("MOODLE_STUDENTS_CSV")
    arquivo_saida_raw = os.getenv("MOODLE_ANALYSIS_OUTPUT_CSV", "./dados/resultado.csv")
    
    modo_analise = "feitos"

    # Converte tudo para caminhos absolutos ancorados na pasta do pacote
    pasta_origem = tratar_caminho_relativo(pasta_origem_raw)
    planilha_alunos = tratar_caminho_relativo(planilha_alunos_raw)
    arquivo_saida = tratar_caminho_relativo(arquivo_saida_raw)

    # Garante que as pastas de output existam antes de rodar o Core
    if arquivo_saida:
        Path(arquivo_saida).parent.mkdir(parents=True, exist_ok=True)

    # Monta a lista de argumentos exatamente como a CLI do core espera
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
    
    # Executa enviando a lista limpa diretamente no parâmetro mapeado do Core
    executar_analise_core(argumentos_cli)


if __name__ == "__main__":
    main()