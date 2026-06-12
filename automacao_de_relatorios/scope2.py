import sys
from pathlib import Path

from config import Config

from auditoria_de_relatorios.executar import main as run_analysis_core

BASE_DIR = Path(__file__).resolve().parent


def main(config: Config):
    """Main function that orchestrates Scope 2 (Middleware / Data Analysis)."""
    print("=" * 80)
    print("▶ [ESCOPO 2] ANÁLISE PENTE-FINO (MIDDLEWARE)")
    print("=" * 80)
    
    print("  • Mapeando caminhos e variáveis a partir da configuração central...")
    
    reports_dir = config.moodle.report_download_path
    students_csv = config.moodle.students_csv
    output_csv = config.moodle.report_analysis_output_csv
    analysis_mode = "feitos"

    if output_csv:
        output_csv.parent.mkdir(parents=True, exist_ok=True)

    cli_args = []
    if reports_dir:
        cli_args.extend(["-d", str(reports_dir)])
    if students_csv:
        cli_args.extend(["-p", str(students_csv)])
    if analysis_mode:
        cli_args.extend(["-m", analysis_mode])
    if output_csv:
        cli_args.extend(["-o", str(output_csv)])

    print(f"  • Injetando argumentos no Core: {' '.join(cli_args)}")
    
    try:
        run_analysis_core(cli_args)
        print("\n✔ Escopo 2 finalizado com sucesso!")
    except Exception as e:
        print(f"\n⚠️ Escopo 2 terminou com falhas: {e}", file=sys.stderr)
        
    print("=" * 80)


if __name__ == "__main__":
    loaded_config = Config.load()
    main(loaded_config)