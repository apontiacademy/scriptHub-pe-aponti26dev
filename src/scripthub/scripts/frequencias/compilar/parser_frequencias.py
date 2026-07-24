from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

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


def percentual_faltas(faltas: int, total: int) -> float:
    return (faltas / total * 100) if total else 0.0


def excedeu_limite_faltas_mes(aluno: Aluno, sessoes_mes: list[Sessao]) -> bool:
    faltas, _ = contar_faltas(registros_do_periodo(aluno, sessoes_mes))
    return faltas > LIMITE_FALTAS_MES


def justificativas_do_periodo(aluno: Aluno, sessoes: list[Sessao]) -> list[tuple[date, str]]:
    return [
        (r.sessao.data, r.comentario)
        for r in registros_do_periodo(aluno, sessoes)
        if r.status == "JU" and r.comentario.strip()
    ]
