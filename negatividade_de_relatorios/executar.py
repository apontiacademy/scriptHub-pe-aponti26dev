import re
import sys
from pathlib import Path

import pandas as pd

# --- Configuração de alertas ---

PALAVRAS_NEGATIVAS = [
    "péssimo",
    "pessimo",
    "ruim",
    "terrível",
    "terrivel",
    "horrível",
    "horrivel",
    "desorganizado",
    "desorganizada",
    "falta de",
    "sem suporte",
    "sem orientação",
    "sem orientacao",
    "não aprendi",
    "nao aprendi",
    "não consegui",
    "nao consegui",
    "desmotivado",
    "desmotivada",
    "abandono",
    "ignorado",
    "ignorada",
    "ninguém me ajudou",
    "ninguem me ajudou",
    "sem retorno",
    "sem resposta",
    "não fui ajudado",
    "nao fui ajudado",
    "não recebi",
    "nao recebi",
    "muito difícil",
    "muito dificil",
    "impossível",
    "impossivel",
    "mal organizado",
    "mal organizada",
    "não aprendo",
    "nao aprendo",
]

# Prefixo da questão → respostas que disparam alerta (comparação case-insensitive)
ALERTAS_NOTA: dict[str, list[str]] = {
    "1.": ["pouco claras", "nada claras"],
    "2.": ["contribuíram pouco", "contribuiram pouco", "não contribuíram", "nao contribuiram"],
    "3.": ["ruim", "péssimo", "pessimo"],
    "4.": ["insatisfatória", "insatisfatoria", "muito insatisfatória", "muito insatisfatoria"],
}


# --- Utilitários (espelhados de pente_fino.py) ---


def normalizar_nome(nome: str) -> str:
    if not isinstance(nome, str):
        return ""
    return re.sub(r"\s+", " ", nome.strip()).lower()


def parsear_grupos(valor: str) -> tuple[str, str]:
    if not isinstance(valor, str):
        return ("", "")
    partes = valor.split(":", 1)
    if len(partes) < 2:
        return (valor.strip(), "")
    estado = partes[0].strip()
    empresa = partes[1].strip().split(" - ")[0].strip()
    return (estado, empresa)


def listar_csvs(diretorio: Path) -> list[Path]:
    csvs = sorted(diretorio.glob("*.csv"))
    if not csvs:
        print("Nenhum arquivo .csv encontrado no diretório atual.")
        sys.exit(1)
    print("\nArquivos CSV encontrados:")
    for i, f in enumerate(csvs, 1):
        print(f"  [{i}] {f.name}")
    return csvs


def selecionar_planilha_geral(csvs: list[Path]) -> Path:
    while True:
        try:
            escolha = int(input("\nDigite o número da planilha GERAL de alunos: "))
            if 1 <= escolha <= len(csvs):
                return csvs[escolha - 1]
            print(f"  Digite um número entre 1 e {len(csvs)}.")
        except ValueError:
            print("  Entrada inválida. Digite apenas o número.")


def carregar_alunos(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str).fillna("")
    faltando = {"Nome", "Sobrenome"} - set(df.columns)
    if faltando:
        print(f"ERRO: A planilha geral não tem as colunas: {faltando}")
        sys.exit(1)
    df["nome_completo"] = (df["Nome"] + " " + df["Sobrenome"]).str.strip()
    df["_nome_norm"] = df["nome_completo"].apply(normalizar_nome)
    if "Grupos" in df.columns:
        grupos = df["Grupos"].apply(parsear_grupos)
        df["estado"] = grupos.apply(lambda x: x[0])
        df["empresa"] = grupos.apply(lambda x: x[1])
    else:
        df["estado"] = ""
        df["empresa"] = ""
    return df[["nome_completo", "_nome_norm", "estado", "empresa"]].drop_duplicates(subset=["_nome_norm"])


# --- Detecção de alertas ---


def _achar_coluna(colunas: list[str], prefixo: str) -> str | None:
    """Retorna o nome da coluna cujo início (sem espaços) começa com o prefixo."""
    for col in colunas:
        if col.strip().startswith(prefixo):
            return col
    return None


def detectar_alerta_nota(valor: str, prefixo_questao: str) -> bool:
    negativos = ALERTAS_NOTA.get(prefixo_questao, [])
    return valor.strip().lower() in negativos


def detectar_alerta_texto(texto: str) -> list[str]:
    """Retorna lista de palavras-chave encontradas no texto."""
    texto_lower = texto.lower()
    return [kw for kw in PALAVRAS_NEGATIVAS if kw in texto_lower]


def analisar_relatorio(path: Path, df_alunos: pd.DataFrame) -> list[dict]:
    df = pd.read_csv(path, dtype=str).fillna("")
    colunas = list(df.columns)

    if "Nome completo" not in colunas:
        print(f"  AVISO: '{path.name}' não tem coluna 'Nome completo'. Pulando.")
        return []

    # Mapear prefixo → nome real da coluna no CSV
    colunas_nota = {prefixo: _achar_coluna(colunas, prefixo) for prefixo in ALERTAS_NOTA}
    col_q5 = _achar_coluna(colunas, "5.")
    col_q6 = _achar_coluna(colunas, "6.")

    # Índice de alunos para lookup rápido
    idx_alunos = df_alunos.set_index("_nome_norm")

    alertas = []
    for _, row in df.iterrows():
        nome_norm = normalizar_nome(row["Nome completo"])
        if nome_norm not in idx_alunos.index:
            continue  # resposta de aluno não cadastrado na lista geral

        aluno = idx_alunos.loc[nome_norm]

        # Alertas por nota
        for prefixo, col in colunas_nota.items():
            if col and detectar_alerta_nota(row[col], prefixo):
                alertas.append(
                    {
                        "nome_completo": aluno["nome_completo"],
                        "estado": aluno["estado"],
                        "empresa": aluno["empresa"],
                        "relatorio": path.stem,
                        "tipo_alerta": "nota_baixa",
                        "detalhe": f"{col.strip()[:60]} → '{row[col]}'",
                    }
                )

        # Alertas por texto (Q5 e Q6)
        for col_texto in [col_q5, col_q6]:
            if not col_texto:
                continue
            palavras = detectar_alerta_texto(row[col_texto])
            if palavras:
                alertas.append(
                    {
                        "nome_completo": aluno["nome_completo"],
                        "estado": aluno["estado"],
                        "empresa": aluno["empresa"],
                        "relatorio": path.stem,
                        "tipo_alerta": "texto_negativo",
                        "detalhe": f"{col_texto.strip()[:50]} | keywords: {', '.join(palavras)}",
                    }
                )

    return alertas


# --- Saída ---


def exibir_resultado(alertas: list[dict]) -> None:
    if not alertas:
        print("\nNenhum alerta de negatividade detectado.")
        return

    df = pd.DataFrame(alertas)

    # --- Visão detalhada ---
    print(f"\n{'=' * 80}")
    print("ALERTAS DETALHADOS")
    print(f"{'=' * 80}")

    col_nome = max(df["nome_completo"].str.len().max(), len("Nome"))
    col_rel = max(df["relatorio"].str.len().max(), len("Relatório"))
    col_tipo = max(df["tipo_alerta"].str.len().max(), len("Tipo"))

    header = f"{'Nome':<{col_nome}}  {'Relatório':<{col_rel}}  {'Tipo':<{col_tipo}}  Detalhe"
    print(header)
    print("-" * min(len(header) + 40, 120))

    for _, row in df.iterrows():
        print(
            f"{row['nome_completo']:<{col_nome}}  "
            f"{row['relatorio']:<{col_rel}}  "
            f"{row['tipo_alerta']:<{col_tipo}}  "
            f"{row['detalhe']}"
        )

    # --- Resumo por aluno ---
    print(f"\n{'=' * 80}")
    print("RESUMO POR ALUNO")
    print(f"{'=' * 80}")

    resumo = (
        df.groupby(["nome_completo", "estado", "empresa"])
        .agg(total_alertas=("tipo_alerta", "count"))
        .reset_index()
        .sort_values("total_alertas", ascending=False)
    )

    for _, row in resumo.iterrows():
        print(f"{row['nome_completo']}  |  {row['estado']}  |  {row['empresa']}  |  {row['total_alertas']} alerta(s)")

    print(f"\nTotal: {len(resumo)} aluno(s) com alertas | {len(df)} ocorrência(s).")


def salvar_resultado(alertas: list[dict], destino: Path) -> None:
    if not alertas:
        print("Nenhum alerta. Arquivo não gerado.")
        return
    pd.DataFrame(alertas).to_csv(destino, index=False, encoding="utf-8-sig")
    print(f"Resultado salvo em: {destino}")


# --- Main ---


def main() -> None:
    diretorio = Path(".")
    csvs = listar_csvs(diretorio)
    planilha_geral = selecionar_planilha_geral(csvs)

    print(f"\nCarregando planilha geral: {planilha_geral.name}")
    df_alunos = carregar_alunos(planilha_geral)
    print(f"  {len(df_alunos)} aluno(s) carregado(s).")

    relatorios = [p for p in csvs if p != planilha_geral]
    if not relatorios:
        print("Nenhum relatório encontrado além da planilha geral. Encerrando.")
        sys.exit(0)

    todos_alertas: list[dict] = []
    for path in relatorios:
        alertas = analisar_relatorio(path, df_alunos)
        todos_alertas.extend(alertas)

    exibir_resultado(todos_alertas)
    salvar_resultado(todos_alertas, diretorio / "alertas_negatividade.csv")


if __name__ == "__main__":
    main()
