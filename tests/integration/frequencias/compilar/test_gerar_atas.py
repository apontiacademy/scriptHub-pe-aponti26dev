from datetime import date
from pathlib import Path

import pytest

from scripthub.scripts.frequencias.compilar.config import AtasConfig, Config, MoodleConfig
from scripthub.scripts.frequencias.compilar.gerar_atas import (
    AtaPDF,
    _gerar_pdf_turma,
    main,
    montar_resumo_mensal_turma,
)
from scripthub.scripts.frequencias.compilar.parser_frequencias import Aluno, RegistroSessao, Sessao, Turma
from scripthub.services.erros import ErroConfiguracao, FalhaParcial

_PATCH = "scripthub.scripts.frequencias.compilar.gerar_atas"


def _sessao(dia, mes, ano=2026, col=5):
    return Sessao(data=date(ano, mes, dia), coluna_status=col, coluna_comentario=col + 1)


def _make_config(tmp_path, caminho_logo=None, caminho_assinatura=None):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            url_login="https://moodle.example.com/login/index.php",
            urls_frequencias={"Turma A": "https://moodle.example.com/freq?id=1"},
        ),
        atas=AtasConfig(
            caminho_saida=tmp_path / "atas",
            caminho_logo=caminho_logo,
            caminho_assinatura=caminho_assinatura,
        ),
        diretorio_download=tmp_path / "dados" / "frequencias",
    )


def _imagem_valida(caminho: Path, tamanho=(120, 60)):
    from PIL import Image

    Image.new("RGB", tamanho, color=(255, 0, 0)).save(caminho)
    return caminho


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

    with pytest.raises(ErroConfiguracao):
        main(config)


def test_main_conta_falhas_por_turma_e_levanta_falha_parcial(tmp_path, mocker):
    config = _make_config(tmp_path)
    diretorio = tmp_path / "dados" / "frequencias"
    diretorio.mkdir(parents=True)
    (diretorio / "turma_a.xlsx").touch()
    (diretorio / "turma_b.xlsx").touch()
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


def test_gerar_pdf_turma_com_justificativas_em_meses_diferentes_gera_pagina_unica_no_final(tmp_path):
    s1, s2 = _sessao(10, 6), _sessao(3, 7)
    aluno = Aluno(
        nome="Fulano de Tal",
        id_estudante="42",
        identificacao_usuario="fulano",
        email="fulano@example.com",
        registros=[
            RegistroSessao(s1, "JU", "Atestado médico"),
            RegistroSessao(s2, "JU", "Consulta médica"),
        ],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=[s1, s2])
    caminho = tmp_path / "test.pdf"

    _gerar_pdf_turma(turma, caminho)

    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_pagina_capa_com_logo_e_assinatura_validas(tmp_path):
    logo = _imagem_valida(tmp_path / "logo.png")
    assinatura = _imagem_valida(tmp_path / "assinatura.png", tamanho=(300, 40))
    pdf = AtaPDF()

    pdf.pagina_capa("Turma X", logo, assinatura)

    assert pdf.page_no() == 1
    assert pdf.output()


def test_gerar_pdf_turma_inclui_capa_como_primeira_pagina(tmp_path, mocker):
    turma = _turma_um_aluno_dois_meses()
    caminho = tmp_path / "test.pdf"
    spy = mocker.spy(AtaPDF, "pagina_capa")

    _gerar_pdf_turma(turma, caminho, caminho_logo=None, caminho_assinatura=None)

    spy.assert_called_once_with(mocker.ANY, turma.nome, None, None)


def test_gerar_pdf_turma_passa_resumo_mensal_para_pagina_resumo_turma(tmp_path, mocker):
    turma = _turma_um_aluno_dois_meses()
    caminho = tmp_path / "test.pdf"
    spy = mocker.spy(AtaPDF, "pagina_resumo_turma")

    _gerar_pdf_turma(turma, caminho)

    spy.assert_called_once_with(mocker.ANY, turma.nome, montar_resumo_mensal_turma(turma))


def test_gerar_pdf_turma_ordem_das_paginas(tmp_path, mocker):
    turma = _turma_um_aluno_dois_meses()
    caminho = tmp_path / "test.pdf"
    ordem = []
    mocker.patch.object(AtaPDF, "pagina_capa", side_effect=lambda *a, **k: ordem.append("capa"))
    mocker.patch.object(AtaPDF, "pagina_resumo_turma", side_effect=lambda *a, **k: ordem.append("resumo_turma"))
    mocker.patch.object(AtaPDF, "pagina_mensal", side_effect=lambda *a, **k: ordem.append("mensal"))
    mocker.patch.object(AtaPDF, "pagina_resumo", side_effect=lambda *a, **k: ordem.append("resumo"))
    mocker.patch.object(AtaPDF, "pagina_justificativas", side_effect=lambda *a, **k: ordem.append("justificativas"))

    _gerar_pdf_turma(turma, caminho)

    assert ordem == ["capa", "resumo_turma", "mensal", "mensal", "resumo", "justificativas"]


def test_main_repassa_logo_e_assinatura_configurados(tmp_path, mocker):
    logo = _imagem_valida(tmp_path / "logo.png")
    assinatura = _imagem_valida(tmp_path / "assinatura.png")
    config = _make_config(tmp_path, caminho_logo=logo, caminho_assinatura=assinatura)
    diretorio = tmp_path / "dados" / "frequencias"
    diretorio.mkdir(parents=True)
    (diretorio / "turma_a.xlsx").touch()
    mocker.patch(
        f"{_PATCH}.carregar_turma",
        side_effect=lambda caminho: Turma(nome=caminho.stem, alunos=[], sessoes=[]),
    )
    mock_gerar = mocker.patch(f"{_PATCH}._gerar_pdf_turma")

    main(config)

    mock_gerar.assert_called_once_with(mocker.ANY, mocker.ANY, caminho_logo=logo, caminho_assinatura=assinatura)


def test_main_sucesso_gera_todas_as_atas(tmp_path, mocker):
    config = _make_config(tmp_path)
    diretorio = tmp_path / "dados" / "frequencias"
    diretorio.mkdir(parents=True)
    (diretorio / "turma_a.xlsx").touch()
    (diretorio / "turma_b.xlsx").touch()
    mocker.patch(
        f"{_PATCH}.carregar_turma",
        side_effect=lambda caminho: Turma(nome=caminho.stem, alunos=[], sessoes=[]),
    )
    mock_gerar = mocker.patch(f"{_PATCH}._gerar_pdf_turma")

    main(config)

    assert mock_gerar.call_count == 2
