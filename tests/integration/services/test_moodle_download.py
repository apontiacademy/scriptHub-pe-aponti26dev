from unittest.mock import MagicMock

import pytest

from scripthub.services.erros import ErroIntegracao
from scripthub.services.moodle.download import baixar_relatorio

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
