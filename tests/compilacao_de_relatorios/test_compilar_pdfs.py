import pytest

from scripthub.scripts.compilacao_de_relatorios.compilar_pdfs import (
    _para_latin1,
    normalizar_nome,
    parsear_grupos,
    sanitizar_caminho,
)


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("Joao Silva", "joao silva"),
        ("  Maria  Souza  ", "maria souza"),
        ("CARLOS ALBERTO", "carlos alberto"),
        (123, ""),
        (None, ""),
    ],
)
def test_normalizar_nome(entrada, esperado):
    assert normalizar_nome(entrada) == esperado


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("SP: Empresa X - 12.345.678/0001-99", ("SP", "Empresa X", "12.345.678/0001-99")),
        ("RJ: Empresa Y", ("RJ", "Empresa Y", "")),
        ("Sem dois pontos", ("Sem dois pontos", "", "")),
        ("MG: Estado", ("MG", "Estado", "")),
        (None, ("", "", "")),
        (42, ("", "", "")),
    ],
)
def test_parsear_grupos(entrada, esperado):
    assert parsear_grupos(entrada) == esperado


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("arquivo<nome>invalido", "arquivonomeinvalido"),
        ("normal.txt", "normal.txt"),
        ('test:file*name?"<>|', "testfilename"),
        ("  espacos  ", "espacos"),
    ],
)
def test_sanitizar_caminho(entrada, esperado):
    assert sanitizar_caminho(entrada) == esperado


@pytest.mark.parametrize(
    "entrada,esperado_contem",
    [
        ("texto com — em dash", " - "),
        ("texto com – en dash", "-"),
        ("texto com … reticencias", "..."),
        ("texto com • bullet", "-"),
    ],
)
def test_para_latin1_substitui_caracteres_especiais(entrada, esperado_contem):
    resultado = _para_latin1(entrada)

    assert esperado_contem in resultado


def test_para_latin1_texto_simples_inalterado():
    assert _para_latin1("texto simples") == "texto simples"


def test_para_latin1_resultado_e_valido_latin1():
    texto = "texto com — e outros chars"

    resultado = _para_latin1(texto)

    resultado.encode("latin-1")
