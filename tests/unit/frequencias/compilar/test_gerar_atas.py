from datetime import date

import pytest

from scripthub.scripts.frequencias.compilar.gerar_atas import (
    AtaPDF,
    PaginaMensal,
    _sanitizar_nome_arquivo,
    _truncar_para_largura,
    agrupar_justificativas_por_data,
    montar_paginas_mensais,
    montar_resumo_geral,
    montar_resumo_mensal_turma,
    todas_justificativas,
)
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

    assert paginas_das_bolinhas == [pdf.page_no()] * 4


def test_pagina_capa_adiciona_pagina_sem_imagens():
    pdf = AtaPDF()

    pdf.pagina_capa("Turma X", None, None)

    assert pdf.page_no() == 1


def test_pagina_capa_ignora_caminhos_inexistentes(tmp_path):
    pdf = AtaPDF()

    pdf.pagina_capa("Turma X", tmp_path / "logo.png", tmp_path / "assinatura.png")

    assert pdf.page_no() == 1
    assert pdf.output()


def test_pagina_capa_nao_desenha_cabecalho_padrao():
    pdf = AtaPDF()

    pdf.pagina_capa("Turma X", None, None)
    pdf.pagina_mensal("Turma X", PaginaMensal(mes="Junho", ano=2026, sessoes=[]))

    assert pdf.page_no() == 2


def test_pagina_resumo_turma_adiciona_pagina():
    pdf = AtaPDF()

    pdf.pagina_resumo_turma("Turma X", [])

    assert pdf.page_no() == 1
