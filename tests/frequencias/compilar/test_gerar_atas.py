from datetime import date
from pathlib import Path

import pytest

from scripthub.scripts.frequencias.compilar.config import AtasConfig, Config, MoodleConfig
from scripthub.scripts.frequencias.compilar.gerar_atas import (
    CINZA_SESSAO_REALOCADA,
    AtaPDF,
    PaginaMensal,
    _cor_celula_sessao,
    _gerar_pdf_turma,
    _sanitizar_nome_arquivo,
    _texto_cabecalho_sessao,
    _truncar_para_largura,
    agrupar_justificativas_por_data,
    main,
    montar_paginas_mensais,
    montar_resumo_geral,
    montar_resumo_mensal_turma,
    todas_justificativas,
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
    assert linha_junho.nivel_alerta == ""

    linha_julho = paginas[1].linhas[0]
    assert linha_julho.statuses == ["AU"]
    assert linha_julho.faltas == 1
    assert linha_julho.percentual == 100.0


def test_montar_paginas_mensais_marca_risco_com_3_ou_mais_faltas():
    sessoes = [_sessao(d, 6) for d in range(1, 4)]
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(s, "AU") for s in sessoes],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=sessoes)

    paginas = montar_paginas_mensais(turma)

    assert paginas[0].linhas[0].nivel_alerta == "risco"


def test_montar_paginas_mensais_marca_atencao_com_exatamente_2_faltas():
    sessoes = [_sessao(d, 6) for d in range(1, 3)]
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(s, "AU") for s in sessoes],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=sessoes)

    paginas = montar_paginas_mensais(turma)

    assert paginas[0].linhas[0].nivel_alerta == "atencao"


def test_montar_paginas_mensais_sem_alerta_com_1_falta():
    sessao = _sessao(1, 6)
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(sessao, "AU")],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=[sessao])

    paginas = montar_paginas_mensais(turma)

    assert paginas[0].linhas[0].nivel_alerta == ""


def test_montar_paginas_mensais_marca_nao_matriculado():
    sessao = _sessao(1, 6)
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(sessao, "JU", "Não matriculado no momento.")],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=[sessao])

    paginas = montar_paginas_mensais(turma)

    assert paginas[0].linhas[0].nao_matriculado == [True]


def test_montar_paginas_mensais_ju_comum_nao_e_nao_matriculado():
    sessao = _sessao(1, 6)
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(sessao, "JU", "Atestado médico")],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=[sessao])

    paginas = montar_paginas_mensais(turma)

    assert paginas[0].linhas[0].nao_matriculado == [False]


def test_montar_paginas_mensais_marca_sessao_realocada():
    s1, s2 = _sessao(1, 6), _sessao(2, 6)
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(s1, "AR"), RegistroSessao(s2, "PR")],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=[s1, s2])

    paginas = montar_paginas_mensais(turma)

    assert paginas[0].sessoes_realocadas == {s1.data}


def test_montar_resumo_geral_ar_conta_como_presenca():
    s1 = _sessao(1, 6)
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(s1, "AR")],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=[s1])

    resumo = montar_resumo_geral(turma)

    assert resumo[0].pr == 1
    assert resumo[0].faltas == 0


def test_montar_resumo_mensal_turma_ar_conta_como_presenca():
    s1 = _sessao(1, 6)
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[RegistroSessao(s1, "AR")],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=[s1])

    linhas = montar_resumo_mensal_turma(turma)

    assert linhas[0].percentual_pr == 100.0


def test_texto_cabecalho_sessao_realocada_recebe_sufixo():
    sessao = _sessao(19, 7)

    assert _texto_cabecalho_sessao(sessao, {sessao.data}) == "19/07**"


def test_texto_cabecalho_sessao_normal_sem_sufixo():
    sessao = _sessao(19, 7)

    assert _texto_cabecalho_sessao(sessao, set()) == "19/07"


def test_cor_celula_sessao_realocada_usa_cinza_intermediario():
    sessao = _sessao(19, 7)

    cor = _cor_celula_sessao(sessao, {sessao.data}, (255, 255, 255))

    assert cor == CINZA_SESSAO_REALOCADA
    assert cor != (255, 255, 255)
    assert cor != (210, 210, 210)


def test_cor_celula_sessao_normal_usa_cor_da_linha():
    sessao = _sessao(19, 7)

    assert _cor_celula_sessao(sessao, set(), (245, 200, 200)) == (245, 200, 200)


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
    assert linha.percentual_ju == 0.0


def test_montar_resumo_geral_calcula_percentual_de_justificadas():
    s1, s2, s3, s4 = _sessao(1, 6), _sessao(2, 6), _sessao(3, 6), _sessao(4, 6)
    aluno = Aluno(
        nome="Fulano",
        id_estudante="1",
        identificacao_usuario="fulano",
        email="f@example.com",
        registros=[
            RegistroSessao(s1, "PR"),
            RegistroSessao(s2, "JU", "Atestado"),
            RegistroSessao(s3, "JU", "Atestado"),
            RegistroSessao(s4, "AU"),
        ],
    )
    turma = Turma(nome="Turma X", alunos=[aluno], sessoes=[s1, s2, s3, s4])

    resumo = montar_resumo_geral(turma)

    assert resumo[0].ju == 2
    assert resumo[0].percentual_ju == pytest.approx(50.0)


def test_montar_resumo_mensal_turma_agrega_percentuais_por_mes():
    s1, s2, s3 = _sessao(1, 6), _sessao(2, 6), _sessao(3, 7)
    alunos = [
        Aluno(
            nome="Fulano",
            id_estudante="1",
            identificacao_usuario="fulano",
            email="f@example.com",
            registros=[
                RegistroSessao(s1, "PR"),
                RegistroSessao(s2, "AU"),
                RegistroSessao(s3, "AT"),
            ],
        ),
        Aluno(
            nome="Ciclano",
            id_estudante="2",
            identificacao_usuario="ciclano",
            email="c@example.com",
            registros=[
                RegistroSessao(s1, "PR"),
                RegistroSessao(s2, "JU", "Atestado"),
                RegistroSessao(s3, "PR"),
            ],
        ),
    ]
    turma = Turma(nome="Turma X", alunos=alunos, sessoes=[s1, s2, s3])

    linhas = montar_resumo_mensal_turma(turma)

    assert len(linhas) == 2
    junho = linhas[0]
    assert (junho.mes, junho.ano) == ("Junho", 2026)
    assert junho.percentual_pr == pytest.approx(50.0)
    assert junho.percentual_au == pytest.approx(25.0)
    assert junho.percentual_ju == pytest.approx(25.0)
    assert junho.percentual_at == pytest.approx(0.0)

    julho = linhas[1]
    assert (julho.mes, julho.ano) == ("Julho", 2026)
    assert julho.percentual_pr == pytest.approx(50.0)
    assert julho.percentual_at == pytest.approx(50.0)


def test_montar_resumo_mensal_turma_vazio_sem_sessoes():
    turma = Turma(nome="Turma X", alunos=[], sessoes=[])

    assert montar_resumo_mensal_turma(turma) == []


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


def test_todas_justificativas_concatena_na_ordem_dos_meses():
    pagina_junho = PaginaMensal(
        mes="Junho",
        ano=2026,
        sessoes=[],
        justificativas=[("Fulano", date(2026, 6, 10), "Atestado médico")],
    )
    pagina_julho = PaginaMensal(
        mes="Julho",
        ano=2026,
        sessoes=[],
        justificativas=[("Ciclano", date(2026, 7, 3), "Não matriculado no momento.")],
    )

    resultado = todas_justificativas([pagina_junho, pagina_julho])

    assert resultado == [
        ("Fulano", date(2026, 6, 10), "Atestado médico"),
        ("Ciclano", date(2026, 7, 3), "Não matriculado no momento."),
    ]


def test_todas_justificativas_vazio_quando_nenhum_mes_tem_justificativa():
    pagina = PaginaMensal(mes="Junho", ano=2026, sessoes=[])

    assert todas_justificativas([pagina]) == []


def test_truncar_para_largura_texto_menor_que_largura_nao_trunca():
    pdf = AtaPDF()
    pdf.set_font("Helvetica", "", 8)

    assert _truncar_para_largura(pdf, "Nome Curto", 50) == "Nome Curto"


def test_truncar_para_largura_texto_maior_adiciona_reticencias():
    pdf = AtaPDF()
    pdf.set_font("Helvetica", "", 8)
    nome_longo = "Nome Extremamente Longo Que Nao Caberia De Jeito Nenhum Nessa Coluna Estreita"

    resultado = _truncar_para_largura(pdf, nome_longo, 20)

    assert resultado != nome_longo
    assert resultado.endswith("...")
    assert pdf.get_string_width(resultado) <= 20


def test_agrupar_justificativas_por_data_agrupa_mesma_data():
    justificativas = [
        ("Fulano", date(2026, 7, 1), "Atestado médico"),
        ("Ciclano", date(2026, 7, 1), "Consulta médica"),
        ("Fulano", date(2026, 7, 15), "Não matriculado no momento."),
    ]

    agrupado = agrupar_justificativas_por_data(justificativas)

    assert list(agrupado.keys()) == [date(2026, 7, 1), date(2026, 7, 15)]
    assert agrupado[date(2026, 7, 1)] == [("Fulano", "Atestado médico"), ("Ciclano", "Consulta médica")]
    assert agrupado[date(2026, 7, 15)] == [("Fulano", "Não matriculado no momento.")]


def test_agrupar_justificativas_por_data_vazio():
    assert agrupar_justificativas_por_data([]) == {}


def test_pagina_justificativas_adiciona_pagina_quando_ha_justificativas():
    pdf = AtaPDF()
    pdf.pagina_resumo("Turma X", [])
    assert pdf.page_no() == 1

    pdf.pagina_justificativas("Turma X", [("Fulano", date(2026, 6, 1), "Atestado médico")])

    assert pdf.page_no() == 2


def test_pagina_justificativas_nao_adiciona_pagina_quando_vazia():
    pdf = AtaPDF()
    pdf.pagina_resumo("Turma X", [])
    assert pdf.page_no() == 1

    pdf.pagina_justificativas("Turma X", [])

    assert pdf.page_no() == 1


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


def test_legenda_bolinha_e_texto_ficam_na_mesma_pagina_mesmo_perto_do_rodape(mocker):
    """Reproduz o bug: self.ellipse() não participa do quebra-página automático do
    fpdf2 (só self.cell() participa), então a bolinha do 1º item da legenda podia
    ficar numa página e seu texto (+ o resto da legenda) na página seguinte."""
    pdf = AtaPDF()
    pdf._turma = "Turma X"
    pdf._subtitulo = "Junho/2026"
    pdf.add_page()
    pdf.set_y(pdf.page_break_trigger - 2)  # sobra menos que a altura da legenda (5mm)

    paginas_das_bolinhas = []
    ellipse_original = AtaPDF.ellipse

    def ellipse_espiao(self, *args, **kwargs):
        paginas_das_bolinhas.append(self.page_no())
        return ellipse_original(self, *args, **kwargs)

    mocker.patch.object(AtaPDF, "ellipse", ellipse_espiao)

    pdf._legenda()

    # 4 status (PR/AU/AT/JU) + 1 marcação de "não matriculado"
    assert paginas_das_bolinhas == [pdf.page_no()] * 5


def test_bolinha_nao_matriculado_desenha_circulo_branco_com_borda_e_barra_diagonal(mocker):
    pdf = AtaPDF()
    pdf.add_page()
    ellipse_spy = mocker.spy(AtaPDF, "ellipse")
    line_spy = mocker.spy(AtaPDF, "line")

    pdf._bolinha_nao_matriculado(50, 50, 2)

    ellipse_spy.assert_called_once()
    assert ellipse_spy.call_args.kwargs.get("style") == "FD"
    line_spy.assert_called_once()


def _textos_de_cell(spy):
    textos = []
    for chamada in spy.call_args_list:
        if len(chamada.args) > 3:
            textos.append(chamada.args[3])
        elif "text" in chamada.kwargs:
            textos.append(chamada.kwargs["text"])
    return textos


def test_legenda_inclui_nao_matriculado(mocker):
    pdf = AtaPDF()
    pdf.add_page()
    spy = mocker.spy(AtaPDF, "cell")

    pdf._legenda()

    assert "Não matriculado" in _textos_de_cell(spy)


def test_nota_sessao_realocada_aparece_quando_houve_realocacao(mocker):
    pdf = AtaPDF()
    pdf.pagina_resumo("Turma X", [])
    spy = mocker.spy(AtaPDF, "cell")

    pdf._nota_sessao_realocada(True)

    textos = _textos_de_cell(spy)
    assert any("Aula realocada" in (t or "") for t in textos)


def test_nota_sessao_realocada_nao_aparece_sem_realocacao(mocker):
    pdf = AtaPDF()
    pdf.pagina_resumo("Turma X", [])
    spy = mocker.spy(AtaPDF, "cell")

    pdf._nota_sessao_realocada(False)

    spy.assert_not_called()


def test_pagina_mensal_marca_cabecalho_de_sessao_realocada(mocker):
    sessao = _sessao(19, 7)
    pagina = PaginaMensal(mes="Julho", ano=2026, sessoes=[sessao], sessoes_realocadas={sessao.data})
    pdf = AtaPDF()
    spy = mocker.spy(AtaPDF, "cell")

    pdf.pagina_mensal("Turma X", pagina)

    assert "19/07**" in _textos_de_cell(spy)


def test_gerar_pdf_turma_com_sessao_realocada_e_nao_matriculado_nao_falha(tmp_path):
    sessao1 = _sessao(1, 6)
    sessao2 = _sessao(8, 6)
    alunos = [
        Aluno(
            nome="Aluno Tardio",
            id_estudante="1",
            identificacao_usuario="tardio",
            email="tardio@example.com",
            registros=[
                RegistroSessao(sessao1, "JU", "Não matriculado no momento."),
                RegistroSessao(sessao2, "AR"),
            ],
        ),
        Aluno(
            nome="Aluno Atrasado",
            id_estudante="2",
            identificacao_usuario="atrasado",
            email="atrasado@example.com",
            registros=[
                RegistroSessao(sessao1, "AU"),
                RegistroSessao(sessao2, "AT"),
            ],
        ),
    ]
    turma = Turma(nome="Turma Y", alunos=alunos, sessoes=[sessao1, sessao2])
    caminho = tmp_path / "test.pdf"

    _gerar_pdf_turma(turma, caminho)

    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_pagina_capa_adiciona_pagina_sem_imagens():
    pdf = AtaPDF()

    pdf.pagina_capa("Turma X", None, None)

    assert pdf.page_no() == 1


def test_pagina_capa_ignora_caminhos_inexistentes(tmp_path):
    pdf = AtaPDF()

    pdf.pagina_capa("Turma X", tmp_path / "logo.png", tmp_path / "assinatura.png")

    assert pdf.page_no() == 1
    assert pdf.output()


def test_pagina_capa_com_logo_e_assinatura_validas(tmp_path):
    logo = _imagem_valida(tmp_path / "logo.png")
    assinatura = _imagem_valida(tmp_path / "assinatura.png", tamanho=(300, 40))
    pdf = AtaPDF()

    pdf.pagina_capa("Turma X", logo, assinatura)

    assert pdf.page_no() == 1
    assert pdf.output()


def test_pagina_capa_nao_desenha_cabecalho_padrao():
    pdf = AtaPDF()

    pdf.pagina_capa("Turma X", None, None)
    pdf.pagina_mensal("Turma X", PaginaMensal(mes="Junho", ano=2026, sessoes=[]))

    assert pdf.page_no() == 2


def test_gerar_pdf_turma_inclui_capa_como_primeira_pagina(tmp_path, mocker):
    turma = _turma_um_aluno_dois_meses()
    caminho = tmp_path / "test.pdf"
    spy = mocker.spy(AtaPDF, "pagina_capa")

    _gerar_pdf_turma(turma, caminho, caminho_logo=None, caminho_assinatura=None)

    spy.assert_called_once_with(mocker.ANY, turma.nome, None, None)


def test_pagina_resumo_turma_adiciona_pagina():
    pdf = AtaPDF()

    pdf.pagina_resumo_turma("Turma X", [])

    assert pdf.page_no() == 1


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
