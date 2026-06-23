from pathlib import Path

from pentefino.services.script import main as executar_analise_core

from scripthub.services import log

from .config import Config

BASE_DIR = Path(__file__).resolve().parent


def main(config: Config):
    """Função principal que orquestra o Escopo 2 (Middleware / Análise de Dados)."""
    log.secao("[ESCOPO 2] ANÁLISE PENTE-FINO (MIDDLEWARE)")

    log.passo("Mapeando caminhos e variáveis a partir da configuração central...")

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

    log.passo(f"Injetando argumentos no Core: {' '.join(argumentos_cli)}")

    try:
        # Executa a análise do core enviando a lista limpa de strings
        executar_analise_core(argumentos_cli)
        log.ok("Escopo 2 finalizado com sucesso!")
    except Exception as e:
        log.erro(f"Escopo 2 terminou com falhas: {e}")
