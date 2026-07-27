from unittest.mock import MagicMock

import pytest

from scripthub.services.erros import ErroIntegracao
from scripthub.services.moodle.download import _campos_de_form, baixar_relatorio


_HTML_FORM_DOWNLOAD = """
<html><body>
<form action="/mod/quiz/report.php" method="post">
  <input type="hidden" name="sesskey" value="sk789">
  <input type="hidden" name="id" value="123">
  <input type="hidden" name="mode" value="overview">
  <input type="submit" name="download" value="Download">
</form>
</body></html>
"""

_HTML_LINK_DOWNLOAD = """
<html><body>
  <a href="/mod/quiz/report.php?id=1&download=csv&sesskey=sk1">Download</a>
</body></html>
"""

_HTML_SEM_DOWNLOAD = "<html><body><p>sem botão</p></body></html>"

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

_HTML_FEEDBACK_DOIS_SUBMITS = """
<html><body>
<form action="/mod/feedback/show_entries.php" method="get">
  <input type="hidden" name="sesskey" value="sk789">
  <input type="hidden" name="id" value="8313">
  <input type="submit" name="submitbutton" value="Exportar">
  <input type="submit" name="cancel" value="Cancelar">
  <select name="download">
    <option value="csv">CSV</option>
  </select>
</form>
</body></html>
"""

_HTML_FEEDBACK_SELECT_EM_FORM_LOGIN = """
<html><body>
<form action="/login/index.php" method="get">
  <select name="download">
    <option value="csv">CSV</option>
  </select>
</form>
</body></html>
"""

_HTML_FEEDBACK_COM_GROUP = """
<html><body>
<form action="/mod/feedback/show_entries.php" method="get">
  <input type="hidden" name="sesskey" value="sk789">
  <input type="hidden" name="id" value="8313">
  <select name="group">
    <option value="0">Todos os grupos</option>
    <option value="42" selected>Turma 42</option>
  </select>
  <select name="download">
    <option value="csv">CSV</option>
    <option value="excel">Excel</option>
  </select>
</form>
</body></html>
"""

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


def _resp(text="", url="https://moodle.example.com/mod/quiz/report.php"):
    r = MagicMock()
    r.text = text
    r.url = url
    return r


def _make_sessao(html=_HTML_FORM_DOWNLOAD, download_content_type="text/csv"):
    sessao = MagicMock()
    sessao.get.return_value = _resp(html)
    resp_download = MagicMock()
    resp_download.headers = {"Content-Type": download_content_type}
    sessao.baixar.return_value = resp_download
    return sessao


# ── baixar_relatorio ──────────────────────────────────────────────────────────


def test_baixar_relatorio_faz_get_na_url(tmp_path):
    sessao = _make_sessao()

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    sessao.get.assert_called_once_with("https://moodle.example.com/report?id=1")


def test_baixar_relatorio_form_inclui_campos_ocultos(tmp_path):
    sessao = _make_sessao()

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]
    assert data.get("sesskey") == "sk789"
    assert data.get("id") == "123"
    assert data.get("mode") == "overview"


def test_baixar_relatorio_form_inclui_submit_download(tmp_path):
    sessao = _make_sessao()

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]
    assert data.get("download") == "Download"


def test_baixar_relatorio_via_link_direto(tmp_path):
    """Tests line 88-92: direct-link download path."""
    sessao = _make_sessao(html=_HTML_LINK_DOWNLOAD)

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    url_baixar = sessao.baixar.call_args[0][0]
    assert "download=csv" in url_baixar


def test_baixar_relatorio_sem_form_nem_link_levanta_erro_integracao(tmp_path):
    """Tests line 137: error when no form/link found."""
    sessao = _make_sessao(html=_HTML_SEM_DOWNLOAD)

    with pytest.raises(ErroIntegracao, match="[Dd]ownload"):
        baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")


def test_baixar_relatorio_form_feedback_ignora_form_irrelevante_e_usa_get(tmp_path):
    sessao = _make_sessao(html=_HTML_FEEDBACK_DOWNLOAD)

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    args, kwargs = sessao.baixar.call_args
    assert "editmode.php" not in args[0]
    assert "show_entries.php" in args[0]
    assert kwargs["method"] == "get"


def test_baixar_relatorio_form_feedback_data_inclui_sesskey_id_e_download_csv(tmp_path):
    sessao = _make_sessao(html=_HTML_FEEDBACK_DOWNLOAD)

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    _, kwargs = sessao.baixar.call_args
    assert kwargs["data"]["sesskey"] == "sk789"
    assert kwargs["data"]["id"] == "8313"
    assert kwargs["data"]["download"] == "csv"


def test_baixar_relatorio_form_feedback_inclui_apenas_primeiro_submit(tmp_path):
    """Tests multiple-submit-button handling (only first one included)."""
    sessao = _make_sessao(html=_HTML_FEEDBACK_DOIS_SUBMITS)

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    _, kwargs = sessao.baixar.call_args
    assert kwargs["data"].get("submitbutton") == "Exportar"
    assert "cancel" not in kwargs["data"]


def test_baixar_relatorio_ignora_select_download_em_form_de_login(tmp_path):
    """Tests ignoring <select name=\"download\"> inside login forms."""
    sessao = _make_sessao(html=_HTML_FEEDBACK_SELECT_EM_FORM_LOGIN)

    with pytest.raises(ErroIntegracao, match="[Dd]ownload"):
        baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")


def test_baixar_relatorio_form_feedback_coleta_outros_selects(tmp_path):
    """Tests collecting other select fields like 'group'."""
    sessao = _make_sessao(html=_HTML_FEEDBACK_COM_GROUP)

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    _, kwargs = sessao.baixar.call_args
    assert kwargs["data"]["group"] == "42"


def test_baixar_relatorio_levanta_erro_quando_select_nao_oferece_csv(tmp_path):
    sessao = _make_sessao(html=_HTML_FEEDBACK_SEM_OPCAO_CSV)

    with pytest.raises(ErroIntegracao, match="[Cc][Ss][Vv]"):
        baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")


def test_baixar_relatorio_levanta_erro_integracao_quando_resposta_nao_e_csv(tmp_path):
    sessao = _make_sessao(download_content_type="text/html")

    with pytest.raises(ErroIntegracao, match="[Cc][Ss][Vv]"):
        baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")


def test_baixar_relatorio_apaga_arquivo_quando_validacao_csv_falha(tmp_path):
    sessao = _make_sessao(download_content_type="text/html")
    caminho_saida = tmp_path / "r.csv"
    caminho_saida.write_bytes(b"<html>lixo</html>")

    with pytest.raises(ErroIntegracao, match="[Cc][Ss][Vv]"):
        baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", caminho_saida)

    assert not caminho_saida.exists()


def test_baixar_relatorio_form_feedback_apaga_arquivo_quando_validacao_csv_falha(tmp_path):
    sessao = _make_sessao(html=_HTML_FEEDBACK_DOWNLOAD, download_content_type="text/html")
    caminho_saida = tmp_path / "r.csv"
    caminho_saida.write_bytes(b"<html>lixo</html>")

    with pytest.raises(ErroIntegracao, match="[Cc][Ss][Vv]"):
        baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", caminho_saida)

    assert not caminho_saida.exists()


# ── _campos_de_form ───────────────────────────────────────────────────────────


def test_campos_de_form_coleta_inputs_ocultos():
    """Tests line 55: continue when input has no name."""
    html = """
    <form>
      <input type="hidden" name="sesskey" value="sk1">
      <input type="hidden" value="no-name">
      <input type="text" name="user" value="john">
    </form>
    """
    soup = __import__("bs4").BeautifulSoup(html, "html.parser")
    form = soup.find("form")

    data = _campos_de_form(form)

    assert data["sesskey"] == "sk1"
    assert data["user"] == "john"
    assert "no-name" not in data


def test_campos_de_form_coleta_primeiro_submit_apenas():
    """Tests that only the first submit button is included."""
    html = """
    <form>
      <input type="hidden" name="id" value="1">
      <input type="submit" name="submit1" value="Save">
      <input type="submit" name="submit2" value="Cancel">
    </form>
    """
    soup = __import__("bs4").BeautifulSoup(html, "html.parser")
    form = soup.find("form")

    data = _campos_de_form(form)

    assert data["submit1"] == "Save"
    assert "submit2" not in data


def test_campos_de_form_ignora_button_type():
    """Tests that type='button' inputs are not included."""
    html = """
    <form>
      <input type="hidden" name="id" value="1">
      <input type="button" name="btn" value="Click">
      <input type="submit" name="submit" value="Send">
    </form>
    """
    soup = __import__("bs4").BeautifulSoup(html, "html.parser")
    form = soup.find("form")

    data = _campos_de_form(form)

    assert "btn" not in data
    assert data["submit"] == "Send"


def test_campos_de_form_coleta_selects():
    """Tests line 66: continue when select has no name."""
    html = """
    <form>
      <select name="group">
        <option value="1">Group A</option>
        <option value="2" selected>Group B</option>
      </select>
      <select>
        <option value="no-name">No name select</option>
      </select>
      <input type="hidden" name="id" value="1">
    </form>
    """
    soup = __import__("bs4").BeautifulSoup(html, "html.parser")
    form = soup.find("form")

    data = _campos_de_form(form)

    assert data["group"] == "2"
    assert data["id"] == "1"
    # Unnamed select should not appear in data


def test_campos_de_form_select_usa_primeira_opcao_se_nenhuma_marcada():
    """Tests that first option is used if none marked as selected."""
    html = """
    <form>
      <select name="lang">
        <option value="pt">Português</option>
        <option value="en">English</option>
      </select>
    </form>
    """
    soup = __import__("bs4").BeautifulSoup(html, "html.parser")
    form = soup.find("form")

    data = _campos_de_form(form)

    assert data["lang"] == "pt"
