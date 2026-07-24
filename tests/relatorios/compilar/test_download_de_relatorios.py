from unittest.mock import MagicMock

import pytest

from scripthub.scripts.relatorios.compilar.config import Config, MoodleConfig, PdfConfig
from scripthub.scripts.relatorios.compilar.download_de_relatorios import (
    _caminho_relatorio,
    _todos_relatorios_existem,
    baixar_relatorio,
    main,
)
from scripthub.services.erros import ErroConfiguracao, ErroIntegracao

_PATCH = "scripthub.scripts.relatorios.compilar.download_de_relatorios"

_HTML_FORM = """
<html><body>
<form action="/mod/quiz/report.php" method="post">
  <input type="hidden" name="sesskey" value="sk1">
  <input type="hidden" name="id" value="1">
  <input type="submit" name="download" value="Download">
</form>
</body></html>
"""

# Estrutura real de mod/feedback/show_entries.php: o primeiro form da página
# (ex.: "Configurar modo de edição") não tem relação com exportação — o form
# correto é identificado pelo <select name="download">, com method="get".
_HTML_FEEDBACK_DOWNLOAD = """
<html><body>
<form action="/editmode.php" method="post">
  <input type="checkbox" name="setmode">
  <input type="hidden" name="sesskey" value="skedit">
  <input type="submit" value="Configurar modo">
</form>
<form action="/mod/feedback/show_entries.php" method="get">
  <input type="hidden" name="sesskey" value="sk789">
  <input type="hidden" name="id" value="8313">
  <select name="download">
    <option value="csv">CSV</option>
    <option value="excel">Excel</option>
  </select>
</form>
</body></html>
"""


def _resp(text="", url="https://moodle.example.com/report"):
    r = MagicMock()
    r.text = text
    r.url = url
    return r


def _make_sessao(html=_HTML_FORM, download_content_type="text/csv"):
    sessao = MagicMock()
    sessao.get.return_value = _resp(html)
    resp_download = MagicMock()
    resp_download.headers = {"Content-Type": download_content_type}
    sessao.baixar.return_value = resp_download
    return sessao


def _make_config(tmp_path):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            url_login="https://moodle.example.com/login/index.php",
            caminho_download=tmp_path / "relatorios",
            meses={"Janeiro": ["https://moodle.example.com/jan1"]},
        ),
        pdf=PdfConfig(
            caminho_saida=tmp_path / "pdfs",
        ),
    )


# ── utilidades ────────────────────────────────────────────────────────────────


def test_caminho_relatorio_gera_path_com_slug(tmp_path):
    p = _caminho_relatorio("Janeiro 2024", tmp_path, 1)

    assert p.parent == tmp_path
    assert "janeiro" in p.name.lower()
    assert p.suffix == ".csv"


def test_todos_relatorios_existem_true_quando_todos_presentes(tmp_path):
    f1 = tmp_path / "jan_1.csv"
    f1.write_text("data")
    caminhos = {"Janeiro": [f1]}

    assert _todos_relatorios_existem(caminhos) is True


def test_todos_relatorios_existem_false_quando_algum_falta(tmp_path):
    caminhos = {"Janeiro": [tmp_path / "inexistente.csv"]}

    assert _todos_relatorios_existem(caminhos) is False


def test_todos_relatorios_existem_false_para_vazio():
    assert _todos_relatorios_existem({}) is False


# ── baixar_relatorio ──────────────────────────────────────────────────────────


def test_baixar_relatorio_delega_para_sessao(tmp_path):
    sessao = _make_sessao()

    baixar_relatorio(sessao, "https://moodle.example.com/r", tmp_path / "r.csv")

    sessao.get.assert_called_once_with("https://moodle.example.com/r")


def test_baixar_relatorio_inclui_sesskey_no_post(tmp_path):
    sessao = _make_sessao()

    baixar_relatorio(sessao, "https://moodle.example.com/r", tmp_path / "r.csv")

    _, kwargs = sessao.baixar.call_args
    assert kwargs["data"].get("sesskey") == "sk1"


_HTML_FORM_GENERICO_METHOD_GET = """
<html><body>
<form action="/mod/quiz/report.php" method="get">
  <input type="hidden" name="sesskey" value="sk1">
  <input type="submit" name="download" value="Download">
</form>
</body></html>
"""


def test_baixar_relatorio_form_generico_respeita_method_get_do_form(tmp_path):
    sessao = _make_sessao(html=_HTML_FORM_GENERICO_METHOD_GET)

    baixar_relatorio(sessao, "https://moodle.example.com/r", tmp_path / "r.csv")

    _, kwargs = sessao.baixar.call_args
    assert kwargs["method"] == "get"


def test_baixar_relatorio_form_feedback_ignora_form_irrelevante_e_usa_get(tmp_path):
    sessao = _make_sessao(html=_HTML_FEEDBACK_DOWNLOAD)

    baixar_relatorio(sessao, "https://moodle.example.com/r", tmp_path / "r.csv")

    args, kwargs = sessao.baixar.call_args
    assert "editmode.php" not in args[0]
    assert "show_entries.php" in args[0]
    assert kwargs["method"] == "get"


def test_baixar_relatorio_form_feedback_data_inclui_sesskey_id_e_download_csv(tmp_path):
    sessao = _make_sessao(html=_HTML_FEEDBACK_DOWNLOAD)

    baixar_relatorio(sessao, "https://moodle.example.com/r", tmp_path / "r.csv")

    _, kwargs = sessao.baixar.call_args
    assert kwargs["data"]["sesskey"] == "sk789"
    assert kwargs["data"]["id"] == "8313"
    assert kwargs["data"]["download"] == "csv"


def test_baixar_relatorio_levanta_erro_integracao_quando_resposta_nao_e_csv(tmp_path):
    sessao = _make_sessao(download_content_type="text/html")

    with pytest.raises(ErroIntegracao, match="[Cc][Ss][Vv]"):
        baixar_relatorio(sessao, "https://moodle.example.com/r", tmp_path / "r.csv")


def test_baixar_relatorio_apaga_arquivo_quando_validacao_csv_falha(tmp_path):
    sessao = _make_sessao(download_content_type="text/html")
    caminho_saida = tmp_path / "r.csv"
    caminho_saida.write_bytes(b"<html>lixo</html>")

    with pytest.raises(ErroIntegracao, match="[Cc][Ss][Vv]"):
        baixar_relatorio(sessao, "https://moodle.example.com/r", caminho_saida)

    assert not caminho_saida.exists()


_HTML_FEEDBACK_SEM_OPCAO_CSV = """
<html><body>
<form action="/mod/feedback/show_entries.php" method="get">
  <input type="hidden" name="sesskey" value="sk789">
  <input type="hidden" name="id" value="8313">
  <select name="download">
    <option value="excel">Excel</option>
    <option value="pdf">PDF</option>
  </select>
</form>
</body></html>
"""


def test_baixar_relatorio_levanta_erro_quando_select_nao_oferece_csv(tmp_path):
    sessao = _make_sessao(html=_HTML_FEEDBACK_SEM_OPCAO_CSV)

    with pytest.raises(ErroIntegracao, match="[Cc][Ss][Vv]"):
        baixar_relatorio(sessao, "https://moodle.example.com/r", tmp_path / "r.csv")


# ── main ─────────────────────────────────────────────────────────────────────


def test_main_levanta_runtime_error_sem_meses(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.moodle.meses = {}
    mocker.patch(f"{_PATCH}.MoodleSessao")

    with pytest.raises(ErroConfiguracao, match="[Mm]ês|[Mm]es"):
        main(config)


def test_main_chama_baixar_para_cada_url(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.moodle.meses = {
        "Janeiro": ["https://moodle.example.com/j1", "https://moodle.example.com/j2"],
        "Fevereiro": ["https://moodle.example.com/f1"],
    }
    mock_sessao_cls = mocker.patch(f"{_PATCH}.MoodleSessao")
    mock_sessao = mock_sessao_cls.return_value
    mock_baixar = mocker.patch(f"{_PATCH}.baixar_relatorio")
    mocker.patch(f"{_PATCH}._todos_relatorios_existem", return_value=False)

    main(config)

    mock_sessao.login.assert_called_once()
    assert mock_baixar.call_count == 3


def test_main_pula_download_quando_todos_existem(tmp_path, mocker):
    config = _make_config(tmp_path)
    mocker.patch(f"{_PATCH}.MoodleSessao")
    mock_baixar = mocker.patch(f"{_PATCH}.baixar_relatorio")
    mocker.patch(f"{_PATCH}._todos_relatorios_existem", return_value=True)
    mocker.patch(f"{_PATCH}._perguntar_baixar_novamente", return_value=False)

    main(config)

    mock_baixar.assert_not_called()
