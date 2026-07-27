from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd

CORES_STATUS: dict[str, tuple[int, int, int]] = {
    "PR": (0, 170, 80),
    "AU": (220, 50, 50),
    "AT": (240, 200, 40),
    "JU": (80, 200, 220),
}

LIMITE_FALTAS_MES = 3

_LINHA_CABECALHO = 3
_PRIMEIRA_COLUNA_SESSAO = 5
_RE_DATA_SESSAO = re.compile(r"^(\d{1,2})/(\d{2})/(\d{4})")
_RE_STATUS = re.compile(r"^([A-Z]{2,3})\s*\(")
_RE_MATRICULA_TARDIA = re.compile(r"Inscrição de usuários inicia (\d{2})\.(\d{2})\.(\d{4})")
_TEXTO_SUSPENSAO = "Inscrições suspensas"
_JUSTIFICATIVA_MATRICULA_TARDIA = "Não matriculado no momento."
_STATUS_VALIDOS = frozenset(CORES_STATUS)


@dataclass(frozen=True)
class Sessao:
    data: date
    coluna_status: int
    coluna_comentario: int


@dataclass
class RegistroSessao:
    sessao: Sessao
    status: str
    comentario: str = ""


@dataclass
class Aluno:
    nome: str
    id_estudante: str
    identificacao_usuario: str
    email: str
    registros: list[RegistroSessao] = field(default_factory=list)


@dataclass
class Turma:
    nome: str
    alunos: list[Aluno]
    sessoes: list[Sessao]


def agrupar_sessoes_por_mes(sessoes: list[Sessao]) -> dict[tuple[int, int], list[Sessao]]:
    grupos: dict[tuple[int, int], list[Sessao]] = defaultdict(list)
    for sessao in sessoes:
        grupos[(sessao.data.year, sessao.data.month)].append(sessao)
    for chave in grupos:
        grupos[chave].sort(key=lambda s: s.data)
    return dict(sorted(grupos.items()))


def registros_do_periodo(aluno: Aluno, sessoes: list[Sessao]) -> list[RegistroSessao]:
    datas = {s.data for s in sessoes}
    return [r for r in aluno.registros if r.sessao.data in datas]


def contar_faltas(registros: list[RegistroSessao]) -> tuple[int, int]:
    faltas = sum(1 for r in registros if r.status == "AU")
    return faltas, len(registros)


def calcular_percentual(parte: int, total: int) -> float:
    return (parte / total * 100) if total else 0.0


def excedeu_limite_faltas_mes(aluno: Aluno, sessoes_mes: list[Sessao]) -> bool:
    faltas, _ = contar_faltas(registros_do_periodo(aluno, sessoes_mes))
    return faltas > LIMITE_FALTAS_MES


def justificativas_do_periodo(aluno: Aluno, sessoes: list[Sessao]) -> list[tuple[date, str]]:
    return [
        (r.sessao.data, r.comentario)
        for r in registros_do_periodo(aluno, sessoes)
        if r.status == "JU" and r.comentario.strip()
    ]


def _nome_completo(nome: str, sobrenome: str) -> str:
    partes = [p.strip() for p in (nome, sobrenome) if p and p.strip() not in ("", ".")]
    return re.sub(r"\s+", " ", " ".join(partes)).strip()


def _extrair_sessoes(linha_cabecalho: list) -> list[Sessao]:
    sessoes = []
    coluna = _PRIMEIRA_COLUNA_SESSAO
    while coluna < len(linha_cabecalho):
        valor = linha_cabecalho[coluna]
        if not isinstance(valor, str):
            break
        m = _RE_DATA_SESSAO.match(valor)
        if not m:
            break
        dia, mes, ano = (int(x) for x in m.groups())
        sessoes.append(Sessao(data=date(ano, mes, dia), coluna_status=coluna, coluna_comentario=coluna + 1))
        coluna += 2
    return sessoes


def _extrair_status(valor) -> str | None:
    if not isinstance(valor, str):
        return None
    m = _RE_STATUS.match(valor)
    if not m or m.group(1) not in _STATUS_VALIDOS:
        return None
    return m.group(1)


def _extrair_matricula_tardia(linha: list) -> date | None:
    for valor in linha:
        if isinstance(valor, str):
            m = _RE_MATRICULA_TARDIA.search(valor)
            if m:
                dia, mes, ano = (int(x) for x in m.groups())
                return date(ano, mes, dia)
    return None


def _linha_suspensa(linha: list) -> bool:
    return any(isinstance(v, str) and _TEXTO_SUSPENSAO in v for v in linha)


def carregar_turma(caminho_xlsx: Path) -> Turma:
    """Lê um XLSX de frequência exportado do Moodle (mod/attendance) e aplica
    as regras de negócio (status→cor, exclusão por suspensão, matrícula
    tardia, '?'→falta) — ver design doc para o detalhamento de cada regra."""
    df = pd.read_excel(caminho_xlsx, header=None)
    linha_cabecalho = df.iloc[_LINHA_CABECALHO].tolist()
    sessoes = _extrair_sessoes(linha_cabecalho)

    alunos: list[Aluno] = []
    for i in range(_LINHA_CABECALHO + 1, len(df)):
        linha = df.iloc[i].tolist()
        nome_bruto = linha[1] if isinstance(linha[1], str) else ""
        if not nome_bruto.strip():
            continue
        if _linha_suspensa(linha):
            continue

        matricula_tardia = _extrair_matricula_tardia(linha)
        registros = []
        for sessao in sessoes:
            if matricula_tardia is not None and sessao.data < matricula_tardia:
                registros.append(RegistroSessao(sessao, "JU", _JUSTIFICATIVA_MATRICULA_TARDIA))
                continue
            status = _extrair_status(linha[sessao.coluna_status]) or "AU"
            comentario_bruto = linha[sessao.coluna_comentario]
            comentario = comentario_bruto if isinstance(comentario_bruto, str) else ""
            registros.append(RegistroSessao(sessao, status, comentario))

        sobrenome_bruto = linha[0] if isinstance(linha[0], str) else ""
        alunos.append(
            Aluno(
                nome=_nome_completo(nome_bruto, sobrenome_bruto),
                id_estudante="" if pd.isna(linha[2]) else str(linha[2]),
                identificacao_usuario="" if pd.isna(linha[3]) else str(linha[3]),
                email="" if pd.isna(linha[4]) else str(linha[4]),
                registros=registros,
            )
        )

    alunos.sort(key=lambda a: a.nome)
    return Turma(nome=caminho_xlsx.stem, alunos=alunos, sessoes=sessoes)
