import sys
from pathlib import Path

from pentefino.services.script import main as executar_analise_core

from .config import Config

BASE_DIR = Path(__file__).resolve().parent


# TODO: implementar modo verboso
def main(config: Config, verboso: bool):
    """Função principal que orquestra o Escopo 2 (Middleware / Análise de Dados)."""
    print("=" * 80)
    print("▶ [ESCOPO 2] ANÁLISE PENTE-FINO (MIDDLEWARE)")
    print("=" * 80)

    print("  • Mapeando caminhos e variáveis a partir da configuração central...")

    diretorio_relatorios = config.moodle.caminho_download_relatorio
    csv_residentes = config.moodle.csv_residentes
    csv_saida = config.moodle.csv_saida_analise
    modo_analise = "feitos"

    # Garante que o diretório pai do arquivo de saída exista antes de rodar o Core
    if csv_saida:
        csv_saida.parent.mkdir(parents=True, exist_ok=True)

    # Converte os objetos Path para str() ao montar a lista de argumentos para a CLI do Core
    argumentos_cli = []
    if diretorio_relatorios:
        argumentos_cli.extend(["-d", str(diretorio_relatorios)])
    if csv_residentes:
        argumentos_cli.extend(["-p", str(csv_residentes)])
    if modo_analise:
        argumentos_cli.extend(["-m", modo_analise])
    if csv_saida:
        argumentos_cli.extend(["-o", str(csv_saida)])

    print(f"  • Injetando argumentos no Core: {' '.join(argumentos_cli)}")

    try:
        # Executa a análise do core enviando a lista limpa de strings
        executar_analise_core(argumentos_cli)
        print("\n✔ Escopo 2 finalizado com sucesso!")
    except Exception as e:
        print(f"\n⚠️ Escopo 2 terminou com falhas: {e}", file=sys.stderr)

    print("=" * 80)
