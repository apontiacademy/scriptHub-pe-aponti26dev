from datetime import date

import pytest

from scripthub.scripts.frequencias.compilar.gerar_atas import montar_paginas_mensais, montar_resumo_geral
from scripthub.scripts.frequencias.compilar.parser_frequencias import Aluno, RegistroSessao, Sessao, Turma


def _sessao(dia, mes, ano=2026, col=5):
    return Sessao(data=date(ano, mes, dia), coluna_status=col, coluna_comentario=col + 1)


def _turma_um_aluno_dois_meses():
    s1, s2 = _sessao(8, 6), _sessao(3, 7)
    aluno = Aluno(
        nome="Fulano de Tal",
        id_estudante="42",
        identificacao_usuario="fulano",
        email="fulano@example.com",
        registros=[
            RegistroSessao(s1, "PR"),
            RegistroSessao(s2, "AU"),
        ],
    )
    return Turma(nome="Turma X", alunos=[aluno], sessoes=[s1, s2])


def test_montar_paginas_mensais_uma_pagina_por_mes():
    turma = _turma_um_aluno_dois_meses()

    paginas = montar_paginas_mensais(turma)

    assert len(paginas) == 2
    assert (paginas[0].ano, paginas[0].mes) == (2026, "Junho")
    assert (paginas[1].ano, paginas[1].mes) == (2026, "Julho")


def test_montar_paginas_mensais_linha_do_aluno():
    turma = _turma_um_aluno_dois_meses()

    paginas = montar_paginas_mensais(turma)

    linha_junho = paginas[0].linhas[0]
    assert linha_junho.nome == "Fulano de Tal"
    assert linha_junho.statuses == ["PR"]
    assert linha_junho.faltas == 0
    assert linha_junho.destacar is False

    linha_julho = paginas[1].linhas[0]
    assert linha_julho.statuses == ["AU"]
    assert linha_julho.faltas == 1
    assert linha_julho.percentual == 100.0


def test_montar_paginas_mensais_destaca_mais_de_3_faltas():
    sessoes = [_sessao(d, 6) for d in range(1, 6)]
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(s, "AU") for s in sessoes],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=sessoes)

    paginas = montar_paginas_mensais(turma)

    assert paginas[0].linhas[0].destacar is True


def test_montar_resumo_geral_agrega_periodo_inteiro():
    s1, s2, s3 = _sessao(1, 6), _sessao(2, 6), _sessao(3, 7)
    aluno = Aluno(
        nome="Fulano",
        id_estudante="42",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[
            RegistroSessao(s1, "PR"),
            RegistroSessao(s2, "AT"),
            RegistroSessao(s3, "AU"),
        ],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=[s1, s2, s3])

    resumo = montar_resumo_geral(turma)

    assert len(resumo) == 1
    linha = resumo[0]
    assert linha.nome == "Fulano"
    assert linha.id_estudante == "42"
    assert linha.pr == 1
    assert linha.at == 1
    assert linha.ju == 0
    assert linha.faltas == 1
    assert linha.percentual == pytest.approx(33.333, rel=1e-3)
