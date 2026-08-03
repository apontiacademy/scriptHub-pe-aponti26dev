from datetime import date

import pytest

from scripthub.scripts.frequencias.compilar.parser_frequencias import (
    LIMITE_ATENCAO_FALTAS_MES,
    LIMITE_FALTAS_MES,
    Aluno,
    RegistroSessao,
    Sessao,
    Turma,
    _nome_completo,
    agrupar_sessoes_por_mes,
    calcular_percentual,
    contar_faltas,
    eh_nao_matriculado,
    em_atencao_faltas_mes,
    excedeu_limite_faltas_mes,
    justificativas_do_periodo,
    registros_do_periodo,
    sessoes_realocadas,
    status_para_contagem,
)


def _sessao(dia, mes, ano=2026, col=5):
    return Sessao(data=date(ano, mes, dia), coluna_status=col, coluna_comentario=col + 1)


def test_agrupar_sessoes_por_mes():
    s1, s2, s3 = _sessao(8, 6), _sessao(10, 6), _sessao(3, 7)

    grupos = agrupar_sessoes_por_mes([s3, s1, s2])

    assert list(grupos.keys()) == [(2026, 6), (2026, 7)]
    assert grupos[(2026, 6)] == [s1, s2]
    assert grupos[(2026, 7)] == [s3]


def test_contar_faltas_conta_so_au():
    registros = [
        RegistroSessao(_sessao(1, 6), "PR"),
        RegistroSessao(_sessao(2, 6), "AU"),
        RegistroSessao(_sessao(3, 6), "AT"),
        RegistroSessao(_sessao(4, 6), "JU"),
        RegistroSessao(_sessao(5, 6), "AU"),
    ]

    faltas, total = contar_faltas(registros)

    assert faltas == 2
    assert total == 5


def test_percentual_faltas():
    assert calcular_percentual(2, 8) == 25.0
    assert calcular_percentual(0, 0) == 0.0


def test_registros_do_periodo_filtra_por_sessoes():
    s_junho = _sessao(8, 6)
    s_julho = _sessao(3, 7)
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(s_junho, "PR"), RegistroSessao(s_julho, "AU")],
    )

    registros = registros_do_periodo(aluno, [s_junho])

    assert len(registros) == 1
    assert registros[0].sessao == s_junho


def test_excedeu_limite_faltas_mes_abaixo_do_limite_nao_destaca():
    assert excedeu_limite_faltas_mes(LIMITE_FALTAS_MES - 1) is False


def test_excedeu_limite_faltas_mes_no_limite_ja_destaca():
    assert excedeu_limite_faltas_mes(LIMITE_FALTAS_MES) is True


def test_excedeu_limite_faltas_mes_acima_do_limite_destaca():
    assert excedeu_limite_faltas_mes(LIMITE_FALTAS_MES + 1) is True


def test_em_atencao_faltas_mes_com_2_faltas_fica_em_atencao():
    assert em_atencao_faltas_mes(LIMITE_ATENCAO_FALTAS_MES) is True


def test_em_atencao_faltas_mes_com_1_falta_nao_fica_em_atencao():
    assert em_atencao_faltas_mes(LIMITE_ATENCAO_FALTAS_MES - 1) is False


def test_em_atencao_faltas_mes_com_3_faltas_nao_fica_em_atencao():
    assert em_atencao_faltas_mes(LIMITE_FALTAS_MES) is False


@pytest.mark.parametrize(
    "status,esperado",
    [("AR", "PR"), ("PR", "PR"), ("AU", "AU"), ("AT", "AT"), ("JU", "JU")],
)
def test_status_para_contagem(status, esperado):
    assert status_para_contagem(status) == esperado


def test_eh_nao_matriculado_true_para_ju_com_comentario_de_matricula_tardia():
    registro = RegistroSessao(_sessao(1, 6), "JU", "Não matriculado no momento.")

    assert eh_nao_matriculado(registro) is True


def test_eh_nao_matriculado_false_para_ju_comum():
    registro = RegistroSessao(_sessao(1, 6), "JU", "Atestado médico")

    assert eh_nao_matriculado(registro) is False


def test_eh_nao_matriculado_false_para_outros_status():
    registro = RegistroSessao(_sessao(1, 6), "AU", "")

    assert eh_nao_matriculado(registro) is False


def test_sessoes_realocadas_identifica_sessao_com_status_ar():
    s1, s2 = _sessao(1, 6), _sessao(2, 6)
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(s1, "AR"), RegistroSessao(s2, "PR")],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=[s1, s2])

    assert sessoes_realocadas(turma) == {s1.data}


def test_sessoes_realocadas_um_unico_ar_basta_para_marcar_a_sessao():
    s1 = _sessao(1, 6)
    alunos = [
        Aluno(
            nome="A",
            id_estudante="1",
            identificacao_usuario="a",
            email="a@example.com",
            registros=[RegistroSessao(s1, "AT")],
        ),
        Aluno(
            nome="B",
            id_estudante="2",
            identificacao_usuario="b",
            email="b@example.com",
            registros=[RegistroSessao(s1, "AR")],
        ),
    ]
    turma = Turma(nome="Turma X", alunos=alunos, sessoes=[s1])

    assert sessoes_realocadas(turma) == {s1.data}


def test_sessoes_realocadas_vazio_quando_nenhum_ar():
    s1 = _sessao(1, 6)
    aluno = Aluno(
        nome="A",
        id_estudante="1",
        identificacao_usuario="a",
        email="a@example.com",
        registros=[RegistroSessao(s1, "PR")],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=[s1])

    assert sessoes_realocadas(turma) == set()


def test_justificativas_do_periodo_so_ju_com_comentario():
    sessoes = [_sessao(1, 6), _sessao(2, 6), _sessao(3, 6)]
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[
            RegistroSessao(sessoes[0], "JU", "Atestado médico"),
            RegistroSessao(sessoes[1], "PR", "Autoregistrado"),
            RegistroSessao(sessoes[2], "JU", ""),
        ],
    )

    justificativas = justificativas_do_periodo(aluno, sessoes)

    assert justificativas == [(sessoes[0].data, "Atestado médico")]


def test_justificativas_do_periodo_exclui_nao_matriculado():
    sessoes = [_sessao(1, 6), _sessao(2, 6)]
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[
            RegistroSessao(sessoes[0], "JU", "Não matriculado no momento."),
            RegistroSessao(sessoes[1], "JU", "Atestado médico"),
        ],
    )

    justificativas = justificativas_do_periodo(aluno, sessoes)

    assert justificativas == [(sessoes[1].data, "Atestado médico")]


def test_nome_completo_concatena_e_normaliza():
    assert _nome_completo("Divanildo Ferreira dos Santos", ".") == "Divanildo Ferreira dos Santos"
    assert _nome_completo("Cauan", "Abraão Rodrigues de Azevedo") == "Cauan Abraão Rodrigues de Azevedo"
    assert _nome_completo("  Ana   Paula  ", "Silva") == "Ana Paula Silva"
