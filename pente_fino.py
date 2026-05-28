import re
import sys
from pathlib import Path

import pandas as pd


def normalizar_nome(nome: str) -> str:
    if not isinstance(nome, str):
        return ""
    return re.sub(r"\s+", " ", nome.strip()).lower()


def parsear_grupos(valor: str) -> tuple[str, str]:
    """Extrai estado e empresa do campo Grupos.

    Formato esperado: 'Pernambuco: Aponti PE - 00.501.070/0001-23'
    Retorna: (estado, empresa)
    """
    if not isinstance(valor, str):
        return ("", "")
    partes = valor.split(":", 1)
    if len(partes) < 2:
        return (valor.strip(), "")
    estado = partes[0].strip()
    resto = partes[1].strip()
    empresa = resto.split(" - ")[0].strip()
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

    colunas_necessarias = {"Nome", "Sobrenome"}
    faltando = colunas_necessarias - set(df.columns)
    if faltando:
        print(f"ERRO: A planilha geral não tem as colunas: {faltando}")
        sys.exit(1)

    df["nome_completo"] = (df["Nome"] + " " + df["Sobrenome"]).str.strip()
    df["_nome_norm"] = df["nome_completo"].apply(normalizar_nome)

    if "Grupos" in df.columns:
        grupos_parsed = df["Grupos"].apply(parsear_grupos)
        df["estado"] = grupos_parsed.apply(lambda x: x[0])
        df["empresa"] = grupos_parsed.apply(lambda x: x[1])
    else:
        df["estado"] = ""
        df["empresa"] = ""

    return df[["nome_completo", "_nome_norm", "estado", "empresa"]].drop_duplicates(
        subset=["_nome_norm"]
    )


def carregar_relatorio(path: Path) -> set[str]:
    df = pd.read_csv(path, dtype=str).fillna("")

    if "Nome completo" not in df.columns:
        print(f"  AVISO: '{path.name}' não tem coluna 'Nome completo'. Pulando.")
        return set()

    return {normalizar_nome(n) for n in df["Nome completo"] if n.strip()}


def calcular_ausencias(
    df_alunos: pd.DataFrame, relatorios: dict[str, set[str]]
) -> pd.DataFrame:
    linhas = []
    for _, aluno in df_alunos.iterrows():
        ausentes = [
            nome_rel
            for nome_rel, respondentes in relatorios.items()
            if aluno["_nome_norm"] not in respondentes
        ]
        if ausentes:
            linhas.append(
                {
                    "nome_completo": aluno["nome_completo"],
                    "estado": aluno["estado"],
                    "empresa": aluno["empresa"],
                    "relatorios_ausentes": ", ".join(sorted(ausentes)),
                    "total_ausencias": len(ausentes),
                }
            )
    return pd.DataFrame(linhas)


def exibir_resultado(df: pd.DataFrame, nomes_relatorios: list[str]) -> None:
    print(f"\nRelatórios processados: {', '.join(sorted(nomes_relatorios))}")
    print("-" * 80)

    if df.empty:
        print("\nTodos os alunos responderam todos os relatórios.")
        return

    col_nome = max(df["nome_completo"].str.len().max(), len("Nome Completo"))
    col_estado = max(df["estado"].str.len().max(), len("Estado"))
    col_empresa = max(df["empresa"].str.len().max(), len("Empresa"))

    header = (
        f"{'Nome Completo':<{col_nome}}  "
        f"{'Estado':<{col_estado}}  "
        f"{'Empresa':<{col_empresa}}  "
        f"Relatórios Ausentes"
    )
    print(f"\nAlunos com ausências:\n{header}")
    print("-" * len(header))

    for _, row in df.iterrows():
        print(
            f"{row['nome_completo']:<{col_nome}}  "
            f"{row['estado']:<{col_estado}}  "
            f"{row['empresa']:<{col_empresa}}  "
            f"{row['relatorios_ausentes']}"
        )

    print(f"\nTotal: {len(df)} aluno(s) com pelo menos 1 ausência.")


def salvar_resultado(df: pd.DataFrame, destino: Path) -> None:
    if df.empty:
        print("Nenhuma ausência encontrada. Arquivo de resultado não gerado.")
        return
    df.to_csv(destino, index=False, encoding="utf-8-sig")
    print(f"Resultado salvo em: {destino}")


def main() -> None:
    diretorio = Path(".")
    csvs = listar_csvs(diretorio)
    planilha_geral = selecionar_planilha_geral(csvs)

    print(f"\nCarregando planilha geral: {planilha_geral.name}")
    df_alunos = carregar_alunos(planilha_geral)
    print(f"  {len(df_alunos)} aluno(s) encontrado(s).")

    relatorios_paths = [p for p in csvs if p != planilha_geral]
    if not relatorios_paths:
        print("Nenhum relatório encontrado além da planilha geral. Encerrando.")
        sys.exit(0)

    relatorios: dict[str, set[str]] = {}
    for path in relatorios_paths:
        respondentes = carregar_relatorio(path)
        if respondentes or "Nome completo" in pd.read_csv(path, nrows=0).columns:
            relatorios[path.stem] = respondentes

    if not relatorios:
        print("Nenhum relatório válido encontrado. Encerrando.")
        sys.exit(0)

    df_resultado = calcular_ausencias(df_alunos, relatorios)
    exibir_resultado(df_resultado, list(relatorios.keys()))
    salvar_resultado(df_resultado, diretorio / "resultado_auditoria.csv")


if __name__ == "__main__":
    main()
