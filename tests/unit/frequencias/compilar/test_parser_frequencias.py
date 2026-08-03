from datetime import date

from scripthub.scripts.frequencias.compilar.parser_frequencias import (
    LIMITE_FALTAS_MES,
    Aluno,
    RegistroSessao,
    Sessao,
    _nome_completo,
    agrupar_sessoes_por_mes,
    calcular_percentual,
    contar_faltas,
    excedeu_limite_faltas_mes,
    justificativas_do_periodo,
    registros_do_periodo,
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


def test_excedeu_limite_faltas_mes_no_limite_nao_destaca():
    sessoes_mes = [_sessao(d, 6) for d in range(1, LIMITE_FALTAS_MES + 1)]
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(s, "AU") for s in sessoes_mes],
    )

    assert excedeu_limite_faltas_mes(aluno, sessoes_mes) is False


def test_excedeu_limite_faltas_mes_acima_do_limite_destaca():
    sessoes_mes = [_sessao(d, 6) for d in range(1, LIMITE_FALTAS_MES + 2)]
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(s, "AU") for s in sessoes_mes],
    )

    assert excedeu_limite_faltas_mes(aluno, sessoes_mes) is True


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


def test_nome_completo_concatena_e_normaliza():
    assert _nome_completo("Divanildo Ferreira dos Santos", ".") == "Divanildo Ferreira dos Santos"
    assert _nome_completo("Cauan", "Abraão Rodrigues de Azevedo") == "Cauan Abraão Rodrigues de Azevedo"
    assert _nome_completo("  Ana   Paula  ", "Silva") == "Ana Paula Silva"
