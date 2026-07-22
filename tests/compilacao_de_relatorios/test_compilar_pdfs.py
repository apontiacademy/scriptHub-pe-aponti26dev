import pytest

from scripthub.scripts.compilacao_de_relatorios.compilar_pdfs import (
    DadosAluno,
    _carregar_relatorios,
    _para_latin1,
    main,
    normalizar_nome,
    parsear_grupos,
    sanitizar_caminho,
)
from scripthub.scripts.compilacao_de_relatorios.config import Config, MoodleConfig, PdfConfig
from scripthub.services.erros import FalhaParcial

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
        ),
    )


def test_main_levanta_runtime_error_informando_gerados_e_falhas(tmp_path, mocker):
    aluno_ok = DadosAluno(nome="Aluno Ok", email="a@a.com", estado="SP", empresa="Empresa", cnpj="123")
    aluno_falha = DadosAluno(nome="Aluno Falha", email="b@b.com", estado="SP", empresa="Empresa", cnpj="456")
    mocker.patch(
        f"{_PATCH}._carregar_relatorios",
        return_value={"aluno ok": aluno_ok, "aluno falha": aluno_falha},
    )
    mocker.patch(f"{_PATCH}._gerar_pdf", side_effect=[None, Exception("falha ao gerar")])

    with pytest.raises(
        FalhaParcial,
        match=r"1 PDF\(s\) falharam ao gerar de 2 aluno\(s\)\. 1 gerado\(s\) com sucesso\.",
    ):
        main(_make_config(tmp_path))


def test_main_falha_individual_de_pdf_loga_erro_nao_aviso(tmp_path, mocker):
    aluno_ok = DadosAluno(nome="Aluno Ok", email="a@a.com", estado="SP", empresa="Empresa", cnpj="123")
    aluno_falha = DadosAluno(nome="Aluno Falha", email="b@b.com", estado="SP", empresa="Empresa", cnpj="456")
    mocker.patch(
        f"{_PATCH}._carregar_relatorios",
        return_value={"aluno ok": aluno_ok, "aluno falha": aluno_falha},
    )
    mocker.patch(f"{_PATCH}._gerar_pdf", side_effect=[None, Exception("falha ao gerar")])
    mock_log = mocker.patch(f"{_PATCH}.log")

    with pytest.raises(FalhaParcial):
        main(_make_config(tmp_path))

    mock_log.erro.assert_any_call("Falha ao gerar PDF para Aluno Falha: falha ao gerar")
    mock_log.aviso.assert_not_called()


def test_main_caminho_sucesso_loga_resumo_agregado_de_pdfs_gerados(tmp_path, mocker):
    aluno = DadosAluno(nome="Aluno Teste", email="a@a.com", estado="SP", empresa="Empresa", cnpj="123")
    mocker.patch(f"{_PATCH}._carregar_relatorios", return_value={"aluno teste": aluno})
    mocker.patch(f"{_PATCH}._gerar_pdf")
    mock_log = mocker.patch(f"{_PATCH}.log")

    main(_make_config(tmp_path))

    mock_log.ok.assert_any_call("1 PDF(s) gerado(s) com sucesso.")


def test_carregar_relatorios_csv_corrompido_loga_aviso_e_continua(tmp_path, mocker):
    caminho_download = tmp_path / "relatorios"
    caminho_download.mkdir()
    caminho_csv = caminho_download / "janeiro_1.csv"
    caminho_csv.write_text("conteudo", encoding="utf-8")
    mocker.patch(f"{_PATCH}.pd.read_csv", side_effect=Exception("csv corrompido"))
    mock_log = mocker.patch(f"{_PATCH}.log")

    resultado = _carregar_relatorios({"Janeiro": ["url1"]}, caminho_download)

    assert resultado == {}
    mock_log.aviso.assert_any_call(f"Falha ao ler {caminho_csv}: csv corrompido")
    mock_log.erro.assert_not_called()


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
        ("texto com ‘aspa simples esquerda", "'"),
        ("texto com ’aspa simples direita", "'"),
        ("texto com “aspa dupla esquerda", '"'),
        ("texto com ”aspa dupla direita", '"'),
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
