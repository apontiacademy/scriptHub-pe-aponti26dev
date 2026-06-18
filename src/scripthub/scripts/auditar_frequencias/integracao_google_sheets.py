import sys
from pathlib import Path

import gspread
import pandas as pd

from .config import Config

DIRETORIO_BASE = Path(__file__).resolve().parent


def main(config: Config):
    """Função principal que orquestra o Escopo 2 (Integração com Google Sheets)."""
    print("=" * 80)
    print("▶ [ESCOPO 2] INTEGRAÇÃO (GOOGLE SHEETS)")
    print("=" * 80)

    caminho_exportacao = config.moodle.caminho_exportacao
    caminho_credenciais = config.gsheets.caminho_json_credenciais
    id_planilha = config.gsheets.id_planilha

    # Validação da existência dos arquivos antes de iniciar a operação
    if not caminho_exportacao.exists():
        print(
            f"  ❌ ERRO: Diretório de exportação não encontrado em: {caminho_exportacao}",
            file=sys.stderr,
        )
        print("=" * 80)
        sys.exit(1)

    if not caminho_credenciais.exists():
        print(
            f"  ❌ ERRO: Arquivo de credenciais do Google não encontrado em: {caminho_credenciais}",
            file=sys.stderr,
        )
        print("=" * 80)
        sys.exit(1)

    if not id_planilha:
        print(
            "  ❌ ERRO: id_planilha não configurado no arquivo de configurações.",
            file=sys.stderr,
        )
        print("=" * 80)
        sys.exit(1)

    # Buscar todos os arquivos XLSX no diretório de exportação
    arquivos_xlsx = list(caminho_exportacao.glob("*.xlsx"))

    if not arquivos_xlsx:
        print("  ⚠️ Nenhum arquivo XLSX encontrado no diretório de exportação.")
        print("  • Certifique-se de rodar o Escopo 1 antes de iniciar o Escopo 2.")
        print("=" * 80)
        sys.exit(1)

    # Autenticação e conexão com a API do Google Sheets
    try:
        print("  • Autenticando com a API do Google...")
        gc = gspread.service_account(filename=str(caminho_credenciais))

        print("  • Abrindo a planilha por ID...")
        planilha = gc.open_by_key(id_planilha)

        # Processar cada arquivo XLSX
        for arquivo_xlsx in arquivos_xlsx:
            nome_arquivo = arquivo_xlsx.stem  # Remove a extensão .xlsx
            print(f"  • Processando arquivo: {arquivo_xlsx.name}")

            # Ler o arquivo XLSX com pandas
            try:
                df = pd.read_excel(arquivo_xlsx)
                # Converter NaN para strings vazias para compatibilidade com JSON
                df = df.fillna("")
                # Renomear headers "Unnamed: x" para vazios
                df.columns = df.columns.str.replace(r"^Unnamed: \d+$", "", regex=True)
                dados_para_upload = [df.columns.tolist()] + df.values.tolist()
            except Exception as e:
                print(f"  ❌ ERRO: Falha ao ler o arquivo {arquivo_xlsx.name}: {e}", file=sys.stderr)
                continue

            # Verificar se a página já existe
            try:
                worksheet = planilha.worksheet(nome_arquivo)
                print(f"  • Página '{nome_arquivo}' já existe, atualizando...")
            except gspread.exceptions.WorksheetNotFound:
                # Criar nova página
                print(f"  • Criando nova página: '{nome_arquivo}'")
                worksheet = planilha.add_worksheet(title=nome_arquivo, rows=100, cols=20)

            # Limpar dados antigos e atualizar com novos dados
            print(f"  • Atualizando dados na página '{nome_arquivo}'...")
            worksheet.clear()
            worksheet.update(range_name="A1", values=dados_para_upload)
            print(f"  ✔ Página '{nome_arquivo}' atualizada com sucesso!")

        print("\n✔ Escopo 2 finalizado com sucesso!")

    except gspread.exceptions.SpreadsheetNotFound:
        print(
            f"  ❌ ERRO: A planilha com ID '{id_planilha}' não foi encontrada.",
            file=sys.stderr,
        )
        print("=" * 80)
        sys.exit(1)
    except Exception as e:
        import traceback

        print(
            f"  ❌ ERRO inesperado durante a integração com o Google Sheets: {e}",
            file=sys.stderr,
        )
        print("  Detalhes do erro:", file=sys.stderr)
        traceback.print_exc()
        print("=" * 80)
        sys.exit(1)

    print("=" * 80)


if __name__ == "__main__":
    # Carrega as configurações unificadas e injeta na main
    configuracao_carregada = Config.load()
    main(configuracao_carregada)
