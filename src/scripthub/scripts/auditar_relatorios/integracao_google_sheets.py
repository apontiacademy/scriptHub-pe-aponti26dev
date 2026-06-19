import sys
from pathlib import Path

import gspread
import pandas as pd

from .config import Config

DIRETORIO_BASE = Path(__file__).resolve().parent


def main(config: Config):
    """Função principal que orquestra o Escopo 3 (Integração com Google Sheets)."""
    print("=" * 80)
    print("▶ [ESCOPO 3] INTEGRAÇÃO (GOOGLE SHEETS)")
    print("=" * 80)

    caminho_csv = config.moodle.csv_saida_analise
    caminho_credenciais = config.gsheets.caminho_json_credenciais
    id_planilha = config.gsheets.id_planilha
    nome_aba = config.gsheets.nome_aba

    # Validação da existência dos arquivos antes de iniciar a operação
    if not caminho_csv.exists():
        print(
            f"  ❌ ERRO: Arquivo de auditoria não encontrado em: {caminho_csv}",
            file=sys.stderr,
        )
        print(
            "  • Certifique-se de rodar o Escopo 2 antes de iniciar o Escopo 3.",
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

    # Lendo os dados locais da coluna D do CSV gerado no Escopo 2
    print(f"  • Lendo dados locais de {caminho_csv.name}...")
    try:
        df = pd.read_csv(caminho_csv, encoding="utf-8-sig")
    except Exception:
        try:
            df = pd.read_csv(caminho_csv, encoding="latin1")
        except Exception as e:
            print(f"  ❌ ERRO: Falha ao ler o arquivo CSV local: {e}", file=sys.stderr)
            print("=" * 80)
            sys.exit(1)

    if df.shape[1] < 4:
        print(
            "  ❌ ERRO: O CSV de resultado possui menos de 4 colunas. Coluna D indisponível.",
            file=sys.stderr,
        )
        print("=" * 80)
        sys.exit(1)

    # Captura o cabeçalho da quarta coluna (Índice 3 = Coluna D) e seus respectivos valores
    cabecalho_coluna_d = df.columns[3]
    valores_coluna_d = df.iloc[:, 3].fillna("").astype(str).tolist()

    # Formata a estrutura de dados como uma lista de linhas exigida pela API do Google Sheets: [[linha1], [linha2], ...]
    dados_para_upload = [[cabecalho_coluna_d]] + [[valor] for valor in valores_coluna_d]

    # Autenticação e conexão com a API do Google Sheets
    try:
        print("  • Autenticando com a API do Google...")
        gc = gspread.service_account(filename=str(caminho_credenciais))

        print("  • Abrindo a planilha por ID...")
        planilha = gc.open_by_key(id_planilha)
        aba = planilha.worksheet(nome_aba)

        # Sobrescrevendo a Coluna D de forma segura
        print(f"  • Limpando dados antigos da Coluna D na aba '{nome_aba}'...")
        aba.batch_clear(["D:D"])

        print(f"  • Colando novos dados na Coluna D (Total de linhas: {len(dados_para_upload)})...")
        aba.update(range_name="D1", values=dados_para_upload)

        print("  ✔ Google Sheets atualizado com sucesso!")
        print("\n✔ Escopo 3 finalizado com sucesso!")

    except gspread.exceptions.WorksheetNotFound:
        print(
            f"  ❌ ERRO: A aba '{nome_aba}' não foi encontrada na planilha fornecida.",
            file=sys.stderr,
        )
        print("=" * 80)
        sys.exit(1)
    except Exception as e:
        print(
            f"  ❌ ERRO inesperado durante a integração com o Google Sheets: {e}",
            file=sys.stderr,
        )
        print("=" * 80)
        sys.exit(1)

    print("=" * 80)
