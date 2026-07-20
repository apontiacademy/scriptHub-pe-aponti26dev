from unittest.mock import MagicMock

import pytest

from scripthub.scripts.auditar_relatorios.config import Config, GsheetsConfig, MoodleConfig
from scripthub.scripts.auditar_relatorios.download_de_relatorios import baixar_relatorio, main
from scripthub.services.erros import ErroConfiguracao, ErroIntegracao

_PATCH = "scripthub.scripts.auditar_relatorios.download_de_relatorios"

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


def _make_config(tmp_path):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            caminho_download_relatorio=tmp_path / "relatorios",
            csv_residentes=tmp_path / "residentes.csv",
            csv_saida_analise=tmp_path / "resultado.csv",
            url_login="https://moodle.example.com/login/index.php",
            urls_relatorios=["https://moodle.example.com/report?id=1"],
            exportar_analise_relatorio=False,
        ),
        gsheets=GsheetsConfig(
            id_planilha="planilha-id",
            nome_aba="Resultados",
            caminho_backup_local=tmp_path / "backups",
            caminho_json_credenciais=tmp_path / "creds.json",
        ),
    )


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


_HTML_FORM_GENERICO_METHOD_GET = """
<html><body>
<form action="/mod/quiz/report.php" method="get">
  <input type="hidden" name="sesskey" value="sk1">
  <input type="hidden" name="id" value="1">
  <input type="submit" name="download" value="Download">
</form>
</body></html>
"""


def test_baixar_relatorio_form_generico_respeita_method_get_do_form(tmp_path):
    sessao = _make_sessao(html=_HTML_FORM_GENERICO_METHOD_GET)

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    _, kwargs = sessao.baixar.call_args
    assert kwargs["method"] == "get"


def test_baixar_relatorio_via_link_direto(tmp_path):
    sessao = _make_sessao(html=_HTML_LINK_DOWNLOAD)

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    url_baixar = sessao.baixar.call_args[0][0]
    assert "download=csv" in url_baixar


def test_baixar_relatorio_sem_form_nem_link_levanta_erro_integracao(tmp_path):
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


def test_baixar_relatorio_form_feedback_inclui_apenas_primeiro_submit(tmp_path):
    sessao = _make_sessao(html=_HTML_FEEDBACK_DOIS_SUBMITS)

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    _, kwargs = sessao.baixar.call_args
    assert kwargs["data"].get("submitbutton") == "Exportar"
    assert "cancel" not in kwargs["data"]


def test_baixar_relatorio_ignora_select_download_em_form_de_login(tmp_path):
    sessao = _make_sessao(html=_HTML_FEEDBACK_SELECT_EM_FORM_LOGIN)

    with pytest.raises(ErroIntegracao, match="[Dd]ownload"):
        baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")


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


def test_baixar_relatorio_form_feedback_coleta_outros_selects(tmp_path):
    sessao = _make_sessao(html=_HTML_FEEDBACK_COM_GROUP)

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    _, kwargs = sessao.baixar.call_args
    assert kwargs["data"]["group"] == "42"


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
        baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")


def test_baixar_relatorio_levanta_erro_integracao_quando_resposta_nao_e_csv(tmp_path):
    sessao = _make_sessao(download_content_type="text/html")

    with pytest.raises(ErroIntegracao, match="[Cc][Ss][Vv]"):
        baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")


def test_baixar_relatorio_apaga_arquivo_quando_validacao_csv_falha(tmp_path):
    sessao = _make_sessao(download_content_type="text/html")
    caminho_saida = tmp_path / "r.csv"
    caminho_saida.write_bytes(b"<html>lixo</html>")  # simula gravacao ja feita por MoodleSessao.baixar()

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


# ── main ─────────────────────────────────────────────────────────────────────


def test_main_levanta_runtime_error_sem_urls(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.moodle.urls_relatorios = []
    mocker.patch(f"{_PATCH}.MoodleSessao")

    with pytest.raises(ErroConfiguracao, match="[Uu][Rr][Ll]"):
        main(config)


def test_main_chama_login_e_baixar_para_cada_url(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.moodle.urls_relatorios = [
        "https://moodle.example.com/r1",
        "https://moodle.example.com/r2",
    ]
    mock_sessao_cls = mocker.patch(f"{_PATCH}.MoodleSessao")
    mock_sessao = mock_sessao_cls.return_value
    mock_baixar = mocker.patch(f"{_PATCH}.baixar_relatorio")

    main(config)

    mock_sessao.login.assert_called_once()
    assert mock_baixar.call_count == 2


def test_main_cria_diretorio_de_download(tmp_path, mocker):
    config = _make_config(tmp_path)
    mocker.patch(f"{_PATCH}.MoodleSessao")
    mocker.patch(f"{_PATCH}.baixar_relatorio")

    main(config)

    assert config.moodle.caminho_download_relatorio.exists()
