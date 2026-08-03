import openpyxl

from scripthub.scripts.frequencias.compilar.parser_frequencias import carregar_turma


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


def test_carregar_turma_com_coluna_cpf_extra(tmp_path):
    """O export do Moodle passou a incluir uma coluna 'CPF' entre o e-mail e a
    primeira sessão, deslocando as colunas de sessão em uma posição."""
    linhas = [
        ["Curso", "Turma X"],
        ["Grupo", "Todos os participantes"],
        [],
        [
            "Sobrenome",
            "Nome",
            "ID do Estudante",
            "Identificação de usuário",
            "Endereço de e-mail",
            "CPF",
            "8/06/2026 09:00 Todos os estudantes",
            None,
            "Sessões realizadas",
        ],
        [
            ".",
            "Aluno Um",
            "1",
            "aluno1",
            "a1@example.com",
            "000.000.000-00",
            "PR (0/0)",
            None,
            1,
        ],
    ]
    caminho = _escrever_xlsx(tmp_path, "Turma X.xlsx", linhas)

    turma = carregar_turma(caminho)

    assert len(turma.sessoes) == 1
    assert turma.sessoes[0].coluna_status == 6
    assert len(turma.alunos) == 1
    assert [r.status for r in turma.alunos[0].registros] == ["PR"]


def test_carregar_turma_interrogacao_vira_au(tmp_path, mocker):
    linhas = [
        ["Curso", "Turma X"],
        ["Grupo", "Todos os participantes"],
        [],
        _cabecalho(["8/06/2026"]),
        [".", "Aluno Um", "1", "aluno1", "a1@example.com", "?", None, 1, 0, 0, 0, 1, "0 / 0", "0,0"],
    ]
    caminho = _escrever_xlsx(tmp_path, "Turma X.xlsx", linhas)
    mock_log = mocker.patch("scripthub.scripts.frequencias.compilar.parser_frequencias.log")

    turma = carregar_turma(caminho)

    assert turma.alunos[0].registros[0].status == "AU"
    mock_log.aviso.assert_not_called()


def test_carregar_turma_status_desconhecido_loga_aviso_e_vira_au(tmp_path, mocker):
    linhas = [
        ["Curso", "Turma X"],
        ["Grupo", "Todos os participantes"],
        [],
        _cabecalho(["8/06/2026"]),
        [".", "Aluno Um", "1", "aluno1", "a1@example.com", "XX (0/0)", None, 1, 0, 0, 0, 1, "0 / 0", "0,0"],
    ]
    caminho = _escrever_xlsx(tmp_path, "Turma X.xlsx", linhas)
    mock_log = mocker.patch("scripthub.scripts.frequencias.compilar.parser_frequencias.log")

    turma = carregar_turma(caminho)

    assert turma.alunos[0].registros[0].status == "AU"
    mock_log.aviso.assert_called_once()
    assert "XX (0/0)" in mock_log.aviso.call_args[0][0]


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


def test_carregar_turma_matricula_tardia_dia_sem_zero_a_esquerda(tmp_path, mocker):
    linhas = [
        ["Curso", "Turma X"],
        ["Grupo", "Todos os participantes"],
        [],
        _cabecalho(["3/07/2026", "5/07/2026"]),
        [
            ".",
            "Tardio",
            "1",
            "tardio",
            "t@example.com",
            "Inscrição de usuários inicia 8.07.2026",
            None,
            "←",
            None,
            0,
            0,
            0,
            1,
            1,
            "0 / 0",
            "0,0",
        ],
    ]
    caminho = _escrever_xlsx(tmp_path, "Turma X.xlsx", linhas)
    mock_log = mocker.patch("scripthub.scripts.frequencias.compilar.parser_frequencias.log")

    turma = carregar_turma(caminho)

    aluno = turma.alunos[0]
    assert [r.status for r in aluno.registros] == ["JU", "JU"]
    assert aluno.registros[0].comentario == "Não matriculado no momento."
    assert aluno.registros[1].comentario == "Não matriculado no momento."
    mock_log.aviso.assert_not_called()


def test_carregar_turma_celulas_vazias_nao_geram_nan(tmp_path):
    """Células vazias do Excel (NaN em pandas) não devem virar string 'nan'."""
    linhas = [
        ["Curso", "Turma X"],
        ["Grupo", "Todos os participantes"],
        [],
        _cabecalho(["8/06/2026"]),
        [
            ".",
            "Aluno Com Blanks",
            None,  # id_estudante vazio
            None,  # identificacao_usuario vazio
            None,  # email vazio
            "PR (0/0)",
            "Autoregistrado",
            1,
            0,
            0,
            0,
            1,
            "0 / 0",
            "0,0",
        ],
    ]
    caminho = _escrever_xlsx(tmp_path, "Turma X.xlsx", linhas)

    turma = carregar_turma(caminho)

    aluno = turma.alunos[0]
    assert aluno.id_estudante == ""
    assert aluno.identificacao_usuario == ""
    assert aluno.email == ""
