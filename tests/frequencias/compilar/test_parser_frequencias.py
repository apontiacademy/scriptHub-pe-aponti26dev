from datetime import date

import openpyxl

from scripthub.scripts.frequencias.compilar.parser_frequencias import (
    LIMITE_FALTAS_MES,
    Aluno,
    RegistroSessao,
    Sessao,
    _nome_completo,
    agrupar_sessoes_por_mes,
    carregar_turma,
    contar_faltas,
    excedeu_limite_faltas_mes,
    justificativas_do_periodo,
    percentual_faltas,
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
    assert percentual_faltas(2, 8) == 25.0
    assert percentual_faltas(0, 0) == 0.0


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


def _escrever_xlsx(tmp_path, nome_arquivo, linhas):
    """linhas: lista de listas de valores de célula, uma por linha da planilha (0-indexed)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    for linha in linhas:
        ws.append(linha)
    caminho = tmp_path / nome_arquivo
    wb.save(caminho)
    return caminho


def _cabecalho(datas):
    """Monta a linha de cabeçalho real: 5 colunas fixas + par (data, None) por sessão."""
    linha = ["Sobrenome", "Nome", "ID do Estudante", "Identificação de usuário", "Endereço de e-mail"]
    for d in datas:
        linha += [f"{d} 09:00 Todos os estudantes", None]
    linha += ["PR", "AU", "AT", "JU", "Sessões realizadas", "Pontos", "Porcentagem"]
    return linha


def test_nome_completo_concatena_e_normaliza():
    assert _nome_completo("Divanildo Ferreira dos Santos", ".") == "Divanildo Ferreira dos Santos"
    assert _nome_completo("Cauan", "Abraão Rodrigues de Azevedo") == "Cauan Abraão Rodrigues de Azevedo"
    assert _nome_completo("  Ana   Paula  ", "Silva") == "Ana Paula Silva"


def test_carregar_turma_status_basico(tmp_path):
    linhas = [
        ["Curso", "Turma X"],
        ["Grupo", "Todos os participantes"],
        [],
        _cabecalho(["8/06/2026", "10/06/2026"]),
        [
            ".",
            "Aluno Um",
            "1",
            "aluno1",
            "a1@example.com",
            "PR (0/0)",
            "Autoregistrado",
            "AU (0/0)",
            None,
            1,
            1,
            0,
            0,
            2,
            "0 / 0",
            "0,0",
        ],
    ]
    caminho = _escrever_xlsx(tmp_path, "Turma X.xlsx", linhas)

    turma = carregar_turma(caminho)

    assert turma.nome == "Turma X"
    assert len(turma.sessoes) == 2
    assert len(turma.alunos) == 1
    aluno = turma.alunos[0]
    assert aluno.nome == "Aluno Um"
    assert [r.status for r in aluno.registros] == ["PR", "AU"]


def test_carregar_turma_interrogacao_vira_au(tmp_path):
    linhas = [
        ["Curso", "Turma X"],
        ["Grupo", "Todos os participantes"],
        [],
        _cabecalho(["8/06/2026"]),
        [".", "Aluno Um", "1", "aluno1", "a1@example.com", "?", None, 1, 0, 0, 0, 1, "0 / 0", "0,0"],
    ]
    caminho = _escrever_xlsx(tmp_path, "Turma X.xlsx", linhas)

    turma = carregar_turma(caminho)

    assert turma.alunos[0].registros[0].status == "AU"


def test_carregar_turma_aluno_suspenso_e_excluido(tmp_path):
    linhas = [
        ["Curso", "Turma X"],
        ["Grupo", "Todos os participantes"],
        [],
        _cabecalho(["8/06/2026", "10/06/2026"]),
        [
            ".",
            "Suspenso",
            "1",
            "susp",
            "s@example.com",
            "AU (0/0)",
            None,
            "Inscrições suspensas",
            None,
            1,
            0,
            0,
            0,
            1,
            "0 / 0",
            "0,0",
        ],
        [
            ".",
            "Normal",
            "2",
            "normal",
            "n@example.com",
            "PR (0/0)",
            None,
            "PR (0/0)",
            None,
            2,
            0,
            0,
            0,
            2,
            "0 / 0",
            "0,0",
        ],
    ]
    caminho = _escrever_xlsx(tmp_path, "Turma X.xlsx", linhas)

    turma = carregar_turma(caminho)

    nomes = [a.nome for a in turma.alunos]
    assert "Suspenso" not in nomes
    assert "Normal" in nomes


def test_carregar_turma_matricula_tardia_justifica_por_data(tmp_path):
    linhas = [
        ["Curso", "Turma X"],
        ["Grupo", "Todos os participantes"],
        [],
        _cabecalho(["8/06/2026", "15/06/2026"]),
        [
            ".",
            "Tardio",
            "1",
            "tardio",
            "t@example.com",
            "Inscrição de usuários inicia 10.06.2026",
            None,
            "PR (0/0)",
            "Autoregistrado",
            1,
            0,
            0,
            1,
            2,
            "0 / 0",
            "0,0",
        ],
    ]
    caminho = _escrever_xlsx(tmp_path, "Turma X.xlsx", linhas)

    turma = carregar_turma(caminho)

    aluno = turma.alunos[0]
    # Sessão de 8/06 é anterior à matrícula (10/06) -> justificada com texto fixo
    assert aluno.registros[0].status == "JU"
    assert aluno.registros[0].comentario == "Não matriculado no momento."
    # Sessão de 15/06 é posterior -> status real preservado
    assert aluno.registros[1].status == "PR"
