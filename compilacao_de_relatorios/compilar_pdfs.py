import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from .config import Config

LARGURA_PAGINA = 210
MARGEM = 15
LARGURA_UTIL = LARGURA_PAGINA - 2 * MARGEM
LARGURA_ROTULO = 45


def normalizar_nome(nome: str) -> str:
    if not isinstance(nome, str):
        return ""
    return re.sub(r"\s+", " ", nome.strip()).lower()


def parsear_grupos(valor: str) -> tuple[str, str, str]:
    """Extrai (estado, empresa, cnpj) do campo Grupos."""
    if not isinstance(valor, str):
        return ("", "", "")
    partes = valor.split(":", 1)
    if len(partes) < 2:
        return (valor.strip(), "", "")
    estado = partes[0].strip()
    resto = partes[1].strip()
    if " - " in resto:
        empresa, cnpj = resto.rsplit(" - ", 1)
        return (estado, empresa.strip(), cnpj.strip())
    return (estado, resto.strip(), "")


def sanitizar_caminho(texto: str) -> str:
    """Remove caracteres inválidos para nomes de arquivo/pasta."""
    return re.sub(r'[\\/*?:"<>|]', "", texto).strip()


def _para_latin1(texto: str) -> str:
    """Substitui caracteres fora do Latin-1 por equivalentes ASCII."""
    substituicoes = {
        "—": " - ",  # — em dash
        "–": "-",    # – en dash
        "‘": "'",    # ' aspa simples esquerda
        "’": "'",    # ' aspa simples direita
        "“": '"',    # " aspa dupla esquerda
        "”": '"',    # " aspa dupla direita
        "…": "...",  # … reticências
        "•": "-",    # • bullet
        "·": "-",    # · ponto médio
    }
    for char, sub in substituicoes.items():
        texto = texto.replace(char, sub)
    return texto.encode("latin-1", errors="replace").decode("latin-1")


@dataclass
class DadosAluno:
    nome: str
    email: str
    estado: str
    empresa: str
    cnpj: str
    cpf: str = ""
    meses: dict[str, dict[str, str]] = field(default_factory=dict)


class RelatorioPDF(FPDF):
    def __init__(self, nome_aluno: str):
        super().__init__()
        self._nome_aluno = nome_aluno
        self.set_margins(MARGEM, MARGEM, MARGEM)
        self.set_auto_page_break(auto=True, margin=MARGEM)

    def header(self):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, _para_latin1(self._nome_aluno), align="L")
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f"Página {self.page_no()}", align="C")

    def titulo_principal(self, nome: str):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 30, 30)
        self.multi_cell(LARGURA_UTIL, 8, _para_latin1("Relatorio de Residencia"), align="C")
        self.set_font("Helvetica", "", 13)
        self.multi_cell(LARGURA_UTIL, 7, _para_latin1(nome), align="C")
        self.ln(2)
        self.set_draw_color(60, 60, 60)
        self.set_line_width(0.5)
        self.line(MARGEM, self.get_y(), MARGEM + LARGURA_UTIL, self.get_y())
        self.ln(6)

    def secao(self, titulo: str):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 7, _para_latin1(titulo).upper(), ln=True)
        self.set_draw_color(180, 180, 180)
        self.set_line_width(0.3)
        self.line(MARGEM, self.get_y(), MARGEM + LARGURA_UTIL, self.get_y())
        self.ln(3)

    def campo(self, rotulo: str, valor: str):
        x_inicio = self.l_margin
        y_inicio = self.get_y()

        self.set_font("Helvetica", "B", 9)
        self.set_text_color(80, 80, 80)
        self.set_xy(x_inicio, y_inicio)
        self.cell(LARGURA_ROTULO, 5, f"  {rotulo}: ", new_x=XPos.RIGHT, new_y=YPos.TOP)

        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        largura_valor = self.w - self.r_margin - (x_inicio + LARGURA_ROTULO)
        self.multi_cell(
            largura_valor,
            5,
            _para_latin1(valor) if valor else "-",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

    def cabecalho_mes(self, nome_mes: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(70, 70, 70)
        self.cell(LARGURA_UTIL, 7, f"  {_para_latin1(nome_mes).upper()}", fill=True, ln=True)
        self.ln(3)

    def questao_resposta(self, numero: int, pergunta: str, resposta: str):
        recuo = 8

        self.set_font("Helvetica", "B", 9)
        self.set_text_color(50, 50, 50)
        pergunta_texto = pergunta.strip()
        if not pergunta_texto.endswith("?"):
            pergunta_texto += "?"
        self.set_x(MARGEM + recuo)
        self.multi_cell(LARGURA_UTIL - recuo, 5, _para_latin1(f"{numero}. {pergunta_texto}"))

        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        self.set_x(MARGEM + recuo * 2)
        resposta_limpa = resposta.strip()
        self.multi_cell(LARGURA_UTIL - recuo * 2, 5, _para_latin1(resposta_limpa) if resposta_limpa else "-")
        self.ln(2)


def _extrair_colunas_perguntas(df: pd.DataFrame) -> list[str]:
    """Retorna as colunas que correspondem às perguntas numeradas do relatório."""
    return [col for col in df.columns if re.match(r"^\d+\.", col.strip())]


def _carregar_cpfs(csv_residentes: Path) -> dict[str, str]:
    """Retorna dict {nome_norm: cpf} a partir do residentes.csv."""
    if not csv_residentes.exists():
        print(f"  ⚠ Aviso: {csv_residentes} não encontrado. CPF ficará em branco.", file=sys.stderr)
        return {}

    df = pd.read_csv(csv_residentes, dtype=str).fillna("")
    cpfs: dict[str, str] = {}
    for _, row in df.iterrows():
        nome_norm = normalizar_nome(row.get("residente", ""))
        cpf = row.get("cpf_residente", "").strip()
        if nome_norm:
            cpfs[nome_norm] = cpf
    return cpfs


def _carregar_relatorios(
    meses: dict[str, str],
    caminho_download: Path,
) -> dict[str, DadosAluno]:
    """Lê os CSVs por mês e agrupa os dados por aluno."""
    alunos: dict[str, DadosAluno] = {}

    for nome_mes, _ in meses.items():
        slug = nome_mes.lower().replace(" ", "_")
        caminho_csv = caminho_download / f"{slug}.csv"

        if not caminho_csv.exists():
            print(f"  ⚠ Aviso: CSV do mês '{nome_mes}' não encontrado em {caminho_csv}. Pulando.", file=sys.stderr)
            continue

        try:
            df = pd.read_csv(caminho_csv, dtype=str).fillna("")
        except Exception as e:
            print(f"  ❌ ERRO: Falha ao ler {caminho_csv}: {e}", file=sys.stderr)
            continue

        colunas_perguntas = _extrair_colunas_perguntas(df)

        for _, row in df.iterrows():
            nome_raw = row.get("Nome completo", "").strip()
            if not nome_raw:
                continue

            nome_norm = normalizar_nome(nome_raw)
            estado, empresa, cnpj = parsear_grupos(row.get("Grupos", ""))
            email = row.get("Endereço de e-mail", "").strip()
            respostas = {}
            for col in colunas_perguntas:
                pergunta = re.sub(r"^\d+\.\s*", "", col).strip()
                respostas[pergunta] = row.get(col, "").strip()

            if nome_norm not in alunos:
                alunos[nome_norm] = DadosAluno(
                    nome=nome_raw,
                    email=email,
                    estado=estado,
                    empresa=empresa,
                    cnpj=cnpj,
                )

            alunos[nome_norm].meses[nome_mes] = respostas

    return alunos


def _gerar_pdf(aluno: DadosAluno, caminho_saida: Path):
    pdf = RelatorioPDF(nome_aluno=aluno.nome)
    pdf.add_page()

    pdf.titulo_principal(aluno.nome)

    pdf.secao("Dados da Empresa")
    pdf.campo("Empresa", aluno.empresa)
    pdf.campo("CNPJ", aluno.cnpj)
    pdf.ln(4)

    pdf.secao("Dados do Aluno")
    pdf.campo("Nome", aluno.nome)
    pdf.campo("CPF", aluno.cpf)
    pdf.campo("E-mail", aluno.email)
    pdf.campo("Núcleo", aluno.estado)
    pdf.ln(4)

    for nome_mes, respostas in aluno.meses.items():
        pdf.cabecalho_mes(nome_mes)
        for i, (pergunta, resposta) in enumerate(respostas.items(), start=1):
            pdf.questao_resposta(i, pergunta, resposta)

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(caminho_saida))


def main(config: Config):
    print("=" * 80)
    print("▶ [ESCOPO 2] COMPILAÇÃO DE PDFs POR ALUNO")
    print("=" * 80)

    print("\n  • Carregando relatórios CSV...")
    alunos = _carregar_relatorios(config.moodle.meses, config.moodle.caminho_download)

    if not alunos:
        print("  ❌ ERRO: Nenhum dado de aluno encontrado nos CSVs.", file=sys.stderr)
        print("=" * 80)
        return

    print(f"  ✔ {len(alunos)} aluno(s) encontrado(s).")

    print("\n  • Carregando CPFs do residentes.csv...")
    cpfs = _carregar_cpfs(config.pdf.csv_residentes)
    for nome_norm, cpf in cpfs.items():
        if nome_norm in alunos:
            alunos[nome_norm].cpf = cpf

    print(f"  ✔ {len(cpfs)} CPF(s) carregado(s).")

    print("\n  • Gerando PDFs...")
    gerados = 0
    erros = 0

    for aluno in alunos.values():
        nome_arquivo = sanitizar_caminho(aluno.nome) + ".pdf"
        caminho_pdf = (
            config.pdf.caminho_saida
            / sanitizar_caminho(aluno.estado)
            / sanitizar_caminho(aluno.empresa)
            / nome_arquivo
        )

        try:
            _gerar_pdf(aluno, caminho_pdf)
            print(f"  ✔ {caminho_pdf.relative_to(config.pdf.caminho_saida)}")
            gerados += 1
        except Exception as e:
            print(f"  ❌ ERRO ao gerar PDF para {aluno.nome}: {e}", file=sys.stderr)
            erros += 1

    print(f"\n✔ Escopo 2 finalizado: {gerados} PDF(s) gerado(s), {erros} erro(s).")
    print("=" * 80)


if __name__ == "__main__":
    configuracao_carregada = Config.load()
    main(configuracao_carregada)
