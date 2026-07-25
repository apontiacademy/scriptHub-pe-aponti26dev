from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from fpdf import FPDF

from scripthub.services import log
from scripthub.services.erros import ErroConfiguracao, FalhaParcial

from .config import Config
from .extrair_frequencias import DIRETORIO_DOWNLOAD
from .parser_frequencias import (
    CORES_STATUS,
    Sessao,
    Turma,
    agrupar_sessoes_por_mes,
    carregar_turma,
    contar_faltas,
    excedeu_limite_faltas_mes,
    justificativas_do_periodo,
    percentual_faltas,
    registros_do_periodo,
)

_MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}
LARGURA_PAGINA = 297  # A4 paisagem
ALTURA_PAGINA = 210
MARGEM = 12
LARGURA_UTIL = LARGURA_PAGINA - 2 * MARGEM


@dataclass
class LinhaAluno:
    nome: str
    statuses: list[str]
    faltas: int
    percentual: float
    destacar: bool


@dataclass
class PaginaMensal:
    mes: str
    ano: int
    sessoes: list[Sessao]
    linhas: list[LinhaAluno] = field(default_factory=list)
    justificativas: list[tuple[str, date, str]] = field(default_factory=list)


@dataclass
class LinhaResumo:
    nome: str
    id_estudante: str
    identificacao_usuario: str
    email: str
    pr: int
    at: int
    ju: int
    faltas: int
    percentual: float


def _sanitizar_nome_arquivo(texto: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", texto).strip()


def montar_paginas_mensais(turma: Turma) -> list[PaginaMensal]:
    paginas = []
    for (ano, mes), sessoes_mes in agrupar_sessoes_por_mes(turma.sessoes).items():
        pagina = PaginaMensal(mes=_MESES_PT[mes], ano=ano, sessoes=sessoes_mes)
        for aluno in turma.alunos:
            registros = registros_do_periodo(aluno, sessoes_mes)
            faltas, total = contar_faltas(registros)
            pagina.linhas.append(
                LinhaAluno(
                    nome=aluno.nome,
                    statuses=[r.status for r in registros],
                    faltas=faltas,
                    percentual=percentual_faltas(faltas, total),
                    destacar=excedeu_limite_faltas_mes(aluno, sessoes_mes),
                )
            )
            for data_sessao, texto in justificativas_do_periodo(aluno, sessoes_mes):
                pagina.justificativas.append((aluno.nome, data_sessao, texto))
        paginas.append(pagina)
    return paginas


def montar_resumo_geral(turma: Turma) -> list[LinhaResumo]:
    resumo = []
    for aluno in turma.alunos:
        registros = registros_do_periodo(aluno, turma.sessoes)
        faltas, total = contar_faltas(registros)
        resumo.append(
            LinhaResumo(
                nome=aluno.nome,
                id_estudante=aluno.id_estudante,
                identificacao_usuario=aluno.identificacao_usuario,
                email=aluno.email,
                pr=sum(1 for r in registros if r.status == "PR"),
                at=sum(1 for r in registros if r.status == "AT"),
                ju=sum(1 for r in registros if r.status == "JU"),
                faltas=faltas,
                percentual=percentual_faltas(faltas, total),
            )
        )
    return resumo


class AtaPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="L", format="A4")
        self.set_margins(MARGEM, MARGEM, MARGEM)
        self.set_auto_page_break(auto=True, margin=MARGEM)
        self._turma = ""
        self._subtitulo = ""

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, self._turma, ln=True)
        self.set_font("Helvetica", "", 11)
        self.cell(0, 6, self._subtitulo, ln=True)
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 5, f"Página {self.page_no()}", align="C")

    def pagina_mensal(self, turma_nome: str, pagina: PaginaMensal):
        self._turma = turma_nome
        self._subtitulo = f"{pagina.mes}/{pagina.ano}"
        self.add_page()

        n_sessoes = len(pagina.sessoes)
        col_nome = 55
        col_extra = 20  # faltas + %
        largura_disponivel = LARGURA_UTIL - col_nome - 2 * col_extra
        col_sessao = largura_disponivel / max(n_sessoes, 1)

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(210, 210, 210)
        self.cell(col_nome, 6, "Aluno", border=1, fill=True)
        for sessao in pagina.sessoes:
            self.cell(col_sessao, 6, sessao.data.strftime("%d/%m"), border=1, fill=True, align="C")
        self.cell(col_extra, 6, "Faltas", border=1, fill=True, align="C")
        self.cell(col_extra, 6, "% Faltas", border=1, fill=True, align="C", ln=True)

        self.set_font("Helvetica", "", 8)
        for linha in pagina.linhas:
            if linha.destacar:
                self.set_fill_color(245, 200, 200)
                preenchido = True
            else:
                self.set_fill_color(255, 255, 255)
                preenchido = True
            self.cell(col_nome, 6, linha.nome[:38], border=1, fill=preenchido)
            x_inicio = self.get_x()
            y_inicio = self.get_y()
            for _status in linha.statuses:
                self.cell(col_sessao, 6, "", border=1, fill=preenchido)
            self.cell(col_extra, 6, str(linha.faltas), border=1, fill=preenchido, align="C")
            self.cell(col_extra, 6, f"{linha.percentual:.1f}%", border=1, fill=preenchido, align="C", ln=True)

            raio = min(col_sessao, 6) * 0.28
            for i, status in enumerate(linha.statuses):
                cx = x_inicio + col_sessao * i + col_sessao / 2
                cy = y_inicio + 3
                self.set_fill_color(*CORES_STATUS[status])
                self.ellipse(cx - raio, cy - raio, raio * 2, raio * 2, style="F")

        self._legenda()
        self._rodape_justificativas(pagina.justificativas)

    def _legenda(self):
        self.ln(4)
        self.set_font("Helvetica", "B", 8)
        legendas = [("PR", "Presente"), ("AU", "Falta"), ("AT", "Atraso"), ("JU", "Justificada")]
        for codigo, rotulo in legendas:
            self.set_fill_color(*CORES_STATUS[codigo])
            self.ellipse(self.get_x() + 1, self.get_y() + 1, 3, 3, style="F")
            self.set_x(self.get_x() + 5)
            self.cell(30, 5, rotulo)

    def _rodape_justificativas(self, justificativas: list[tuple[str, date, str]]):
        if not justificativas:
            return
        self.ln(6)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 5, "Justificativas", ln=True)
        self.set_font("Helvetica", "", 8)
        for nome, data_sessao, texto in justificativas:
            self.multi_cell(0, 5, f"{data_sessao.strftime('%d/%m/%Y')} — {nome}: {texto}")

    def pagina_resumo(self, turma_nome: str, resumo: list[LinhaResumo]):
        self._turma = turma_nome
        self._subtitulo = "Resumo geral"
        self.add_page()

        colunas = [
            ("Aluno", 45),
            ("ID", 15),
            ("Usuário", 25),
            ("E-mail", 55),
            ("PR", 15),
            ("AT", 15),
            ("JU", 15),
            ("Faltas", 15),
            ("% Faltas", 20),
        ]
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(210, 210, 210)
        for titulo, largura in colunas:
            self.cell(largura, 6, titulo, border=1, fill=True, align="C")
        self.ln(6)

        self.set_font("Helvetica", "", 8)
        for linha in resumo:
            valores = [
                linha.nome[:30],
                linha.id_estudante,
                linha.identificacao_usuario[:16],
                linha.email[:34],
                str(linha.pr),
                str(linha.at),
                str(linha.ju),
                str(linha.faltas),
                f"{linha.percentual:.1f}%",
            ]
            for (_, largura), valor in zip(colunas, valores, strict=True):
                self.cell(largura, 6, valor, border=1)
            self.ln(6)


def _gerar_pdf_turma(turma: Turma, caminho_saida: Path) -> None:
    pdf = AtaPDF()
    for pagina in montar_paginas_mensais(turma):
        pdf.pagina_mensal(turma.nome, pagina)
    pdf.pagina_resumo(turma.nome, montar_resumo_geral(turma))
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(caminho_saida))


def main(config: Config) -> None:
    """Gera uma ata de frequência (PDF) por turma a partir dos XLSX extraídos."""
    log.secao("GERAÇÃO DE ATAS EM PDF")

    arquivos_xlsx = list(DIRETORIO_DOWNLOAD.glob("*.xlsx"))
    if not arquivos_xlsx:
        raise ErroConfiguracao(
            "Nenhum XLSX de frequência encontrado. Execute `frequencias compilar --passo extrair` antes."
        )

    erros = 0
    for arquivo in arquivos_xlsx:
        turma = carregar_turma(arquivo)
        nome_arquivo = _sanitizar_nome_arquivo(turma.nome) + ".pdf"
        caminho_saida = config.atas.caminho_saida / nome_arquivo
        try:
            _gerar_pdf_turma(turma, caminho_saida)
            log.ok(f"{caminho_saida.name}")
        except Exception as e:
            log.erro(f"Falha ao gerar ata para {turma.nome}: {e}")
            erros += 1

    if erros:
        raise FalhaParcial(f"{erros} ata(s) falharam ao gerar de {len(arquivos_xlsx)} turma(s).")

    log.ok(f"{len(arquivos_xlsx) - erros} ata(s) gerada(s) com sucesso.")


if __name__ == "__main__":
    try:
        main(Config.load())
    except Exception as e:
        log.erro(str(e))
        sys.exit(1)
