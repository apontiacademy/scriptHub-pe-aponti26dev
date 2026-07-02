import pytest

from scripthub.scripts.compilacao_de_relatorios.compilar_pdfs import (
    DadosAluno,
    _para_latin1,
    main,
    normalizar_nome,
    parsear_grupos,
    sanitizar_caminho,
)
from scripthub.scripts.compilacao_de_relatorios.config import Config, MoodleConfig, PdfConfig

_PATCH = "scripthub.scripts.compilacao_de_relatorios.compilar_pdfs"


def _make_config(tmp_path):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            url_login="https://example.com/login",
            meses={"Janeiro": ["https://example.com/r1"]},
            caminho_download=tmp_path / "relatorios",
        ),
        pdf=PdfConfig(
            caminho_saida=tmp_path / "pdfs",
            csv_residentes=tmp_path / "residentes.csv",
        ),
    )


def test_main_levanta_runtime_error_quando_ha_pdfs_com_erro(tmp_path, mocker):
    aluno = DadosAluno(nome="Aluno Teste", email="a@a.com", estado="SP", empresa="Empresa", cnpj="123")
    mocker.patch(f"{_PATCH}._carregar_relatorios", return_value={"aluno teste": aluno})
    mocker.patch(f"{_PATCH}._carregar_cpfs", return_value={})
    mocker.patch(f"{_PATCH}._gerar_pdf", side_effect=Exception("falha ao gerar"))

    with pytest.raises(RuntimeError, match="PDF"):
        main(_make_config(tmp_path))


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
