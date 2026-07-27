from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from scripthub.services import log
from scripthub.services.erros import ErroConfiguracao, FalhaParcial

from .config import Config
from .extrair_frequencias import DIRETORIO_DOWNLOAD
from .parser_frequencias import (
    CORES_STATUS,
    Sessao,
    Turma,
    agrupar_sessoes_por_mes,
    calcular_percentual,
    carregar_turma,
    contar_faltas,
    excedeu_limite_faltas_mes,
    justificativas_do_periodo,
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
MARGEM = 12
LARGURA_UTIL = LARGURA_PAGINA - 2 * MARGEM

LARGURA_LOGO_MAX = 65
ALTURA_LOGO_MAX = 32
ALTURA_ASSINATURA_MAX = 40
ESPACAMENTO_CAPA = 8
MARGEM_TOPO_LOGO = 28


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
class LinhaResumoMensal:
    mes: str
    ano: int
    percentual_pr: float
    percentual_at: float
    percentual_ju: float
    percentual_au: float


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
    percentual_ju: float


def _sanitizar_nome_arquivo(texto: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", texto).strip()


def _truncar_para_largura(pdf: FPDF, texto: str, largura_max: float) -> str:
    """Trunca `texto` para caber em `largura_max` (mm) na fonte atual de `pdf`,
    adicionando reticências após o último caractere que coube."""
    largura_disponivel = largura_max - 2 * pdf.c_margin
    if pdf.get_string_width(texto) <= largura_disponivel:
        return texto
    reticencias = "..."
    largura_reticencias = pdf.get_string_width(reticencias)
    truncado = ""
    for char in texto:
        if pdf.get_string_width(truncado + char) + largura_reticencias > largura_disponivel:
            break
        truncado += char
    return truncado + reticencias


def _para_latin1(texto: str) -> str:
    """Substitui caracteres fora do Latin-1 por equivalentes ASCII."""
    substituicoes = {
        "—": " - ",  # — em dash
        "–": "-",  # – en dash
        "‘": "'",  # ‘ aspa simples esquerda
        "’": "'",  # ’ aspa simples direita
        "“": '"',  # “ aspa dupla esquerda
        "”": '"',  # ” aspa dupla direita
        "…": "...",  # … reticências
        "•": "-",  # • bullet
        "·": "-",  # · ponto médio
    }
    for char, sub in substituicoes.items():
        texto = texto.replace(char, sub)
    return texto.encode("latin-1", errors="replace").decode("latin-1")


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
                    percentual=calcular_percentual(faltas, total),
                    destacar=excedeu_limite_faltas_mes(aluno, sessoes_mes),
                )
            )
            for data_sessao, texto in justificativas_do_periodo(aluno, sessoes_mes):
                pagina.justificativas.append((aluno.nome, data_sessao, texto))
        paginas.append(pagina)
    return paginas


def todas_justificativas(paginas: list[PaginaMensal]) -> list[tuple[str, date, str]]:
    return [justificativa for pagina in paginas for justificativa in pagina.justificativas]


def agrupar_justificativas_por_data(
    justificativas: list[tuple[str, date, str]],
) -> dict[date, list[tuple[str, str]]]:
    agrupado: dict[date, list[tuple[str, str]]] = {}
    for nome, data_sessao, texto in justificativas:
        agrupado.setdefault(data_sessao, []).append((nome, texto))
    return agrupado


def montar_resumo_mensal_turma(turma: Turma) -> list[LinhaResumoMensal]:
    linhas = []
    for (ano, mes), sessoes_mes in agrupar_sessoes_por_mes(turma.sessoes).items():
        contagens = {"PR": 0, "AT": 0, "JU": 0, "AU": 0}
        total = 0
        for aluno in turma.alunos:
            for registro in registros_do_periodo(aluno, sessoes_mes):
                contagens[registro.status] += 1
                total += 1
        linhas.append(
            LinhaResumoMensal(
                mes=_MESES_PT[mes],
                ano=ano,
                percentual_pr=calcular_percentual(contagens["PR"], total),
                percentual_at=calcular_percentual(contagens["AT"], total),
                percentual_ju=calcular_percentual(contagens["JU"], total),
                percentual_au=calcular_percentual(contagens["AU"], total),
            )
        )
    return linhas


def montar_resumo_geral(turma: Turma) -> list[LinhaResumo]:
    resumo = []
    for aluno in turma.alunos:
        registros = registros_do_periodo(aluno, turma.sessoes)
        faltas, total = contar_faltas(registros)
        ju = sum(1 for r in registros if r.status == "JU")
        resumo.append(
            LinhaResumo(
                nome=aluno.nome,
                id_estudante=aluno.id_estudante,
                identificacao_usuario=aluno.identificacao_usuario,
                email=aluno.email,
                pr=sum(1 for r in registros if r.status == "PR"),
                at=sum(1 for r in registros if r.status == "AT"),
                ju=ju,
                faltas=faltas,
                percentual=calcular_percentual(faltas, total),
                percentual_ju=calcular_percentual(ju, total),
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
        self._pagina_capa = False

    def header(self):
        if self._pagina_capa:
            return
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, _para_latin1(self._turma), ln=True)  # TODO: substituir por new_x e new_y
        self.set_font("Helvetica", "", 11)
        self.cell(0, 6, _para_latin1(self._subtitulo), ln=True)  # TODO: substituir por new_x e new_y
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 5, _para_latin1(f"Página {self.page_no()}"), align="C")

    def pagina_capa(self, turma_nome: str, caminho_logo: Path | None, caminho_assinatura: Path | None):
        logo_existe = caminho_logo is not None and caminho_logo.exists()
        assinatura_existe = caminho_assinatura is not None and caminho_assinatura.exists()

        self._pagina_capa = True
        self.add_page()

        if logo_existe:
            x_logo = (self.w - LARGURA_LOGO_MAX) / 2
            self.image(
                str(caminho_logo),
                x=x_logo,
                y=MARGEM_TOPO_LOGO,
                w=LARGURA_LOGO_MAX,
                h=ALTURA_LOGO_MAX,
                keep_aspect_ratio=True,
            )

        altura_titulo = 14
        altura_turma = 11
        altura_bloco = altura_titulo + ESPACAMENTO_CAPA + altura_turma

        y = (self.h - altura_bloco) / 2

        self.set_y(y)
        self.set_font("Helvetica", "B", 26)
        self.cell(
            0, altura_titulo, _para_latin1("Registro de Frequências"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )
        y += altura_titulo + ESPACAMENTO_CAPA

        self.set_y(y)
        self.set_font("Helvetica", "", 18)
        self.cell(0, altura_turma, _para_latin1(turma_nome), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        if assinatura_existe:
            x = MARGEM
            y_assinatura = self.h - self.b_margin - ALTURA_ASSINATURA_MAX
            self.image(
                str(caminho_assinatura),
                x=x,
                y=y_assinatura,
                w=LARGURA_UTIL,
                h=ALTURA_ASSINATURA_MAX,
                keep_aspect_ratio=True,
            )

        self._pagina_capa = False

    def pagina_resumo_turma(self, turma_nome: str, linhas: list[LinhaResumoMensal]):
        self._turma = turma_nome
        self._subtitulo = "Resumo geral da turma"
        self.add_page()

        colunas = [
            ("Mês", 93),
            ("% PR", 45),
            ("% AT", 45),
            ("% JU", 45),
            ("% AU", 45),
        ]
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(210, 210, 210)
        for titulo, largura in colunas:
            self.cell(largura, 6, _para_latin1(titulo), border=1, fill=True, align="C")
        self.ln(6)

        self.set_font("Helvetica", "", 8)
        for linha in linhas:
            valores = [
                _para_latin1(f"{linha.mes}/{linha.ano}"),
                _para_latin1(f"{linha.percentual_pr:.1f}%"),
                _para_latin1(f"{linha.percentual_at:.1f}%"),
                _para_latin1(f"{linha.percentual_ju:.1f}%"),
                _para_latin1(f"{linha.percentual_au:.1f}%"),
            ]
            for (_, largura), valor in zip(colunas, valores, strict=True):
                self.cell(largura, 6, valor, border=1, align="C")
            self.ln(6)

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
        self.cell(col_nome, 6, _para_latin1("Aluno"), border=1, fill=True)
        for sessao in pagina.sessoes:
            self.cell(col_sessao, 6, sessao.data.strftime("%d/%m"), border=1, fill=True, align="C")
        self.cell(col_extra, 6, _para_latin1("Faltas"), border=1, fill=True, align="C")
        self.cell(
            col_extra, 6, _para_latin1("% Faltas"), border=1, fill=True, align="C", ln=True
        )  # TODO: substituir por new_x e new_y

        self.set_font("Helvetica", "", 8)
        for linha in pagina.linhas:
            cor_preenchimento = (245, 200, 200) if linha.destacar else (255, 255, 255)
            self.set_fill_color(*cor_preenchimento)
            preenchido = True
            nome = _truncar_para_largura(self, _para_latin1(linha.nome), col_nome)
            self.cell(col_nome, 6, nome, border=1, fill=preenchido)
            x_inicio = self.get_x()
            y_inicio = self.get_y()
            for _status in linha.statuses:
                self.cell(col_sessao, 6, "", border=1, fill=preenchido)
            self.cell(col_extra, 6, str(linha.faltas), border=1, fill=preenchido, align="C")
            self.cell(
                col_extra,
                6,
                _para_latin1(f"{linha.percentual:.1f}%"),
                border=1,
                fill=preenchido,
                align="C",
                ln=True,
            )  # TODO: substituir por new_x e new_y

            raio = min(col_sessao, 6) * 0.28
            for i, status in enumerate(linha.statuses):
                cx = x_inicio + col_sessao * i + col_sessao / 2
                cy = y_inicio + 3
                self.set_fill_color(*CORES_STATUS[status])
                self.ellipse(cx - raio, cy - raio, raio * 2, raio * 2, style="F")

        self._legenda()
        self._nota_justificativas(pagina.justificativas)

    def _legenda(self):
        self.ln(4)
        self.set_font("Helvetica", "B", 8)
        legendas = [("PR", "Presente"), ("AU", "Falta"), ("AT", "Atraso"), ("JU", "Justificada")]
        for codigo, rotulo in legendas:
            self.set_fill_color(*CORES_STATUS[codigo])
            self.ellipse(self.get_x() + 1, self.get_y() + 1, 3, 3, style="F")
            self.set_x(self.get_x() + 5)
            self.cell(30, 5, _para_latin1(rotulo))

    def _nota_justificativas(self, justificativas: list[tuple[str, date, str]]):
        if not justificativas:
            return
        self.ln(4)
        self.set_font("Helvetica", "I", 8)
        self.cell(
            0, 5, _para_latin1("* Justificativas ao final do documento."), ln=True
        )  # TODO: substituir por new_x e new_y

    def pagina_justificativas(self, turma_nome: str, justificativas: list[tuple[str, date, str]]):
        if not justificativas:
            return
        self._turma = turma_nome
        self._subtitulo = "Justificativas"
        self.add_page()

        indentacao = MARGEM + 6
        por_data = agrupar_justificativas_por_data(justificativas)
        for data_sessao in sorted(por_data):
            itens = por_data[data_sessao]
            self.set_left_margin(MARGEM)
            self.set_x(MARGEM)
            self.set_font("Helvetica", "B", 10)
            self.cell(0, 7, _para_latin1(data_sessao.strftime("%d/%m/%Y")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            self.set_left_margin(indentacao)
            for nome, texto in itens:
                self.set_x(indentacao)
                self.set_font("Helvetica", "", 9)
                self.write(5, _para_latin1("- "))
                self.set_font("Helvetica", "B", 9)
                self.write(5, _para_latin1(nome))
                self.set_font("Helvetica", "", 9)
                self.write(5, _para_latin1(f": {texto}"))
                self.ln(6)
            self.set_left_margin(MARGEM)
            self.ln(2)

    def pagina_resumo(self, turma_nome: str, resumo: list[LinhaResumo]):
        self._turma = turma_nome
        self._subtitulo = "Resumo geral por aluno"
        self.add_page()

        colunas = [
            ("Aluno", 124),
            ("PR", 22),
            ("AT", 22),
            ("JU", 22),
            ("AU", 22),
            ("% JU", 28),
            ("% Faltas", 33),
        ]
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(210, 210, 210)
        for titulo, largura in colunas:
            self.cell(largura, 6, _para_latin1(titulo), border=1, fill=True, align="C")
        self.ln(6)

        self.set_font("Helvetica", "", 8)
        for linha in resumo:
            _, largura_nome = colunas[0]
            valores = [
                _truncar_para_largura(self, _para_latin1(linha.nome), largura_nome),
                _para_latin1(str(linha.pr)),
                _para_latin1(str(linha.at)),
                _para_latin1(str(linha.ju)),
                _para_latin1(str(linha.faltas)),
                _para_latin1(f"{linha.percentual_ju:.1f}%"),
                _para_latin1(f"{linha.percentual:.1f}%"),
            ]
            for (_, largura), valor in zip(colunas, valores, strict=True):
                self.cell(largura, 6, valor, border=1)
            self.ln(6)


def _gerar_pdf_turma(
    turma: Turma,
    caminho_saida: Path,
    caminho_logo: Path | None = None,
    caminho_assinatura: Path | None = None,
) -> None:
    pdf = AtaPDF()
    pdf.pagina_capa(turma.nome, caminho_logo, caminho_assinatura)
    pdf.pagina_resumo_turma(turma.nome, montar_resumo_mensal_turma(turma))
    paginas = montar_paginas_mensais(turma)
    for pagina in paginas:
        pdf.pagina_mensal(turma.nome, pagina)
    pdf.pagina_resumo(turma.nome, montar_resumo_geral(turma))
    pdf.pagina_justificativas(turma.nome, todas_justificativas(paginas))
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(caminho_saida))


def main(config: Config) -> None:
    """Gera uma ata de frequência (PDF) por turma a partir dos XLSX extraídos."""
    arquivos_xlsx = list(DIRETORIO_DOWNLOAD.glob("*.xlsx"))
    if not arquivos_xlsx:
        raise ErroConfiguracao(
            "Nenhum XLSX de frequência encontrado. Execute `frequencias compilar --passo extrair` antes."
        )

    erros = 0
    for arquivo in arquivos_xlsx:
        try:
            turma = carregar_turma(arquivo)
            nome_arquivo = _sanitizar_nome_arquivo(turma.nome) + ".pdf"
            caminho_saida = config.atas.caminho_saida / nome_arquivo
            _gerar_pdf_turma(
                turma,
                caminho_saida,
                caminho_logo=config.atas.caminho_logo,
                caminho_assinatura=config.atas.caminho_assinatura,
            )
            log.ok(f"{caminho_saida.name}")
        except Exception as e:
            log.erro(f"Falha ao gerar ata para {arquivo.stem}: {e}")
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
