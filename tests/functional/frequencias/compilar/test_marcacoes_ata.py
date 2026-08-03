"""Step definitions dos critérios de aceite da issue #133 (ver o .feature
correspondente em tests/features/frequencias/compilar/marcacoes_ata.feature).

Constrói Turma/Aluno/RegistroSessao diretamente em memória — a mecânica de
parsing do XLSX (regex de status, matrícula tardia etc.) tem sua própria
cobertura em tests/unit e tests/integration/frequencias/compilar; aqui o
foco é a regra de negócio observável a partir de montar_paginas_mensais /
montar_resumo_geral.
"""

from datetime import date

from pytest_bdd import given, parsers, scenarios, then, when

from scripthub.scripts.frequencias.compilar.gerar_atas import (
    LinhaAluno,
    PaginaMensal,
    montar_paginas_mensais,
    montar_resumo_geral,
)
from scripthub.scripts.frequencias.compilar.parser_frequencias import Aluno, RegistroSessao, Sessao, Turma

scenarios("frequencias/compilar/marcacoes_ata.feature")


def _sessao(dia: int, mes: int, ano: int = 2026, col: int = 5) -> Sessao:
    return Sessao(data=date(ano, mes, dia), coluna_status=col, coluna_comentario=col + 1)


def _aluno(contexto: dict, nome: str) -> Aluno:
    if nome not in contexto["alunos"]:
        contexto["alunos"][nome] = Aluno(
            nome=nome,
            id_estudante=nome,
            identificacao_usuario=nome.lower(),
            email=f"{nome.lower()}@example.com",
            registros=[],
        )
    return contexto["alunos"][nome]


def _linha(contexto: dict, nome: str) -> LinhaAluno:
    pagina: PaginaMensal = contexto["paginas"][0]
    return next(linha for linha in pagina.linhas if linha.nome == nome)


# --- Cenário: matrícula tardia distinta de justificativa comum -------------


@given(
    "um aluno com matrícula tardia numa sessão anterior à data de início da matrícula",
    target_fixture="contexto",
)
def dado_matricula_tardia():
    contexto = {"alunos": {}, "sessoes": []}
    sessao = _sessao(1, 6)
    aluno = _aluno(contexto, "Fulano")
    aluno.registros.append(RegistroSessao(sessao, "JU", "Não matriculado no momento."))
    contexto["sessoes"].append(sessao)
    return contexto


@given("uma justificativa comum numa sessão posterior à matrícula")
def dado_justificativa_comum(contexto):
    sessao = _sessao(10, 6)
    aluno = _aluno(contexto, "Fulano")
    aluno.registros.append(RegistroSessao(sessao, "JU", "Atestado médico"))
    contexto["sessoes"].append(sessao)


@then(parsers.parse('a célula da sessão de matrícula tardia é marcada como "{marcacao}"'))
def entao_matricula_tardia_marcada(contexto, marcacao):
    assert marcacao == "não matriculado"
    assert _linha(contexto, "Fulano").nao_matriculado[0] is True


@then(parsers.parse('a célula da sessão com justificativa comum não é marcada como "{marcacao}"'))
def entao_justificativa_comum_nao_marcada(contexto, marcacao):
    assert marcacao == "não matriculado"
    assert _linha(contexto, "Fulano").nao_matriculado[1] is False


@then("a lista de justificativas da página contém apenas a justificativa comum")
def entao_apenas_justificativa_comum_na_lista(contexto):
    pagina: PaginaMensal = contexto["paginas"][0]
    assert pagina.justificativas == [("Fulano", date(2026, 6, 10), "Atestado médico")]


# --- Cenário: sessão com AR marcada como realocada --------------------------


@given(parsers.parse('uma sessão em que um aluno tem status "{status}"'), target_fixture="contexto")
def dado_sessao_com_status(status):
    contexto = {"alunos": {}, "sessoes": []}
    sessao = _sessao(19, 7)
    aluno = _aluno(contexto, "Realocado")
    aluno.registros.append(RegistroSessao(sessao, status))
    contexto["sessoes"].append(sessao)
    contexto["sessao_comum"] = sessao
    return contexto


@given(parsers.parse('outro aluno tem status "{status}" na mesma sessão'))
def dado_outro_aluno_com_status(contexto, status):
    aluno = _aluno(contexto, "Atrasado")
    aluno.registros.append(RegistroSessao(contexto["sessao_comum"], status))


@then("a sessão é marcada como realocada")
def entao_sessao_realocada(contexto):
    pagina: PaginaMensal = contexto["paginas"][0]
    assert pagina.sessoes_realocadas == {contexto["sessao_comum"].data}


@then(parsers.parse('o aluno com status "{status}" mantém esse status na mesma sessão'))
def entao_status_individual_mantido(contexto, status):
    assert _linha(contexto, "Atrasado").statuses == [status]


# --- Cenário: AR conta como presença no cálculo de faltas -------------------


@given(
    parsers.parse('um aluno com status "{status_ar}" numa sessão e status "{status_au}" em outra'),
    target_fixture="contexto",
)
def dado_aluno_ar_e_au(status_ar, status_au):
    contexto = {"alunos": {}, "sessoes": []}
    sessao_ar, sessao_au = _sessao(1, 6), _sessao(8, 6)
    aluno = _aluno(contexto, "Fulano")
    aluno.registros.append(RegistroSessao(sessao_ar, status_ar))
    aluno.registros.append(RegistroSessao(sessao_au, status_au))
    contexto["sessoes"] = [sessao_ar, sessao_au]
    return contexto


@when("o percentual e a contagem de faltas do aluno são calculados")
def quando_faltas_calculadas(contexto):
    turma = Turma(nome="Turma X", alunos=list(contexto["alunos"].values()), sessoes=contexto["sessoes"])
    contexto["paginas"] = montar_paginas_mensais(turma)
    contexto["resumo"] = montar_resumo_geral(turma)


@then('apenas a sessão com status "AU" conta como falta')
def entao_apenas_au_conta_como_falta(contexto):
    linha = _linha(contexto, "Fulano")
    assert linha.faltas == 1
    assert linha.percentual == 50.0


@then('a sessão com status "AR" conta como presença no resumo geral')
def entao_ar_conta_como_presenca_no_resumo(contexto):
    assert contexto["resumo"][0].pr == 1


# --- Cenários: limiares de falta (risco / atenção / sem destaque) ----------


@given(parsers.parse("um aluno com {n:d} falta(s) no mês"), target_fixture="contexto")
def dado_aluno_com_n_faltas(n):
    contexto = {"alunos": {}, "sessoes": []}
    aluno = _aluno(contexto, "Fulano")
    if n == 0:
        sessao = _sessao(1, 6)
        aluno.registros.append(RegistroSessao(sessao, "PR"))
        contexto["sessoes"].append(sessao)
    else:
        for dia in range(1, n + 1):
            sessao = _sessao(dia, 6)
            aluno.registros.append(RegistroSessao(sessao, "AU"))
            contexto["sessoes"].append(sessao)
    return contexto


@then(parsers.parse('a linha desse aluno é destacada com o nível "{nivel}"'))
def entao_linha_destacada_com_nivel(contexto, nivel):
    assert _linha(contexto, "Fulano").nivel_alerta == nivel


@then(parsers.parse('a linha desse aluno não é destacada com o nível "{nivel}"'))
def entao_linha_nao_destacada_com_nivel(contexto, nivel):
    assert _linha(contexto, "Fulano").nivel_alerta != nivel


@then("a linha desse aluno não recebe nenhum nível de destaque")
def entao_linha_sem_destaque(contexto):
    assert _linha(contexto, "Fulano").nivel_alerta == ""


# --- Passo comum: gerar a ata mensal ----------------------------------------


@when("a ata mensal é gerada")
def quando_ata_gerada(contexto):
    turma = Turma(nome="Turma X", alunos=list(contexto["alunos"].values()), sessoes=contexto["sessoes"])
    contexto["paginas"] = montar_paginas_mensais(turma)
