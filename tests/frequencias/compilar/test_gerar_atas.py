from datetime import date

import pytest

from scripthub.scripts.frequencias.compilar.config import AtasConfig, Config, MoodleConfig
from scripthub.scripts.frequencias.compilar.gerar_atas import (
    _gerar_pdf_turma,
    _sanitizar_nome_arquivo,
    main,
    montar_paginas_mensais,
    montar_resumo_geral,
)
from scripthub.scripts.frequencias.compilar.parser_frequencias import Aluno, RegistroSessao, Sessao, Turma
from scripthub.services.erros import ErroConfiguracao, FalhaParcial

_PATCH = "scripthub.scripts.frequencias.compilar.gerar_atas"


def _sessao(dia, mes, ano=2026, col=5):
    return Sessao(data=date(ano, mes, dia), coluna_status=col, coluna_comentario=col + 1)


def _make_config(tmp_path):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            url_login="https://moodle.example.com/login/index.php",
            urls_frequencias={"Turma A": "https://moodle.example.com/freq?id=1"},
        ),
        atas=AtasConfig(caminho_saida=tmp_path / "atas"),
    )


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


def test_montar_paginas_mensais_coleta_justificativas_de_matricula_tardia():
    sessao = _sessao(10, 6)
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(sessao, "JU", "Não matriculado no momento.")],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=[sessao])

    paginas = montar_paginas_mensais(turma)

    assert paginas[0].justificativas == [("Fulano", sessao.data, "Não matriculado no momento.")]


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ('Turma: A/B\\C*D?E"F<G>H|I', "Turma ABCDEFGHI"),
        ("  Turma Normal  ", "Turma Normal"),
        ("Turma Sem Caracteres Especiais", "Turma Sem Caracteres Especiais"),
    ],
)
def test_sanitizar_nome_arquivo_remove_caracteres_invalidos(entrada, esperado):
    assert _sanitizar_nome_arquivo(entrada) == esperado


def test_gerar_pdf_turma_com_justificativas_de_matricula_tardia_nao_falha(tmp_path):
    """Reproduz a regressão crítica: em dash + multi_cell consecutivo derrubavam a
    geração de PDF para qualquer turma com aluno de matrícula tardia (JU + comentário)."""
    sessao1 = _sessao(1, 6)
    sessao2 = _sessao(8, 6)
    alunos = [
        Aluno(
            nome=f"Aluno {i}",
            id_estudante=str(i),
            identificacao_usuario=f"aluno{i}",
            email=f"aluno{i}@example.com",
            registros=[
                RegistroSessao(sessao1, "JU", "Não matriculado no momento."),
                RegistroSessao(sessao2, "PR"),
            ],
        )
        for i in range(2)
    ]
    turma = Turma(nome="Turma Late — Enrollment", alunos=alunos, sessoes=[sessao1, sessao2])
    caminho = tmp_path / "test.pdf"

    _gerar_pdf_turma(turma, caminho)

    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_main_sem_xlsx_levanta_erro_configuracao(tmp_path, mocker):
    config = _make_config(tmp_path)
    diretorio = tmp_path / "dados" / "frequencias"
    diretorio.mkdir(parents=True)
    mocker.patch(f"{_PATCH}.DIRETORIO_DOWNLOAD", diretorio)

    with pytest.raises(ErroConfiguracao):
        main(config)


def test_main_conta_falhas_por_turma_e_levanta_falha_parcial(tmp_path, mocker):
    config = _make_config(tmp_path)
    diretorio = tmp_path / "dados" / "frequencias"
    diretorio.mkdir(parents=True)
    (diretorio / "turma_a.xlsx").touch()
    (diretorio / "turma_b.xlsx").touch()
    mocker.patch(f"{_PATCH}.DIRETORIO_DOWNLOAD", diretorio)
    mocker.patch(
        f"{_PATCH}.carregar_turma",
        side_effect=[
            RuntimeError("XLSX malformado"),
            Turma(nome="Turma B", alunos=[], sessoes=[]),
        ],
    )
    mock_gerar = mocker.patch(f"{_PATCH}._gerar_pdf_turma")

    with pytest.raises(FalhaParcial):
        main(config)

    assert mock_gerar.call_count == 1


def test_main_sucesso_gera_todas_as_atas(tmp_path, mocker):
    config = _make_config(tmp_path)
    diretorio = tmp_path / "dados" / "frequencias"
    diretorio.mkdir(parents=True)
    (diretorio / "turma_a.xlsx").touch()
    (diretorio / "turma_b.xlsx").touch()
    mocker.patch(f"{_PATCH}.DIRETORIO_DOWNLOAD", diretorio)
    mocker.patch(
        f"{_PATCH}.carregar_turma",
        side_effect=lambda caminho: Turma(nome=caminho.stem, alunos=[], sessoes=[]),
    )
    mock_gerar = mocker.patch(f"{_PATCH}._gerar_pdf_turma")

    main(config)

    assert mock_gerar.call_count == 2
