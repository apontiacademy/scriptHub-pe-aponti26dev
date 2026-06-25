from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripthub.scripts.auditar_relatorios.config import Config, GsheetsConfig, MoodleConfig
from scripthub.scripts.auditar_relatorios.download_de_relatorios import baixar_relatorio, main

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


def _resp(text="", url="https://moodle.example.com/mod/quiz/report.php"):
    r = MagicMock()
    r.text = text
    r.url = url
    return r


def _make_sessao(html=_HTML_FORM_DOWNLOAD):
    sessao = MagicMock()
    sessao.get.return_value = _resp(html)
    return sessao


def _make_config(tmp_path):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            caminho_download_relatorio=tmp_path / "relatorios",
            headless=True,
            csv_residentes=tmp_path / "residentes.csv",
            csv_saida_analise=tmp_path / "resultado.csv",
            url_login="https://moodle.example.com/login/index.php",
            urls_relatorios=["https://moodle.example.com/report?id=1"],
            exportar_analise_relatorio=False,
            caminho_exportacao_analise=None,
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


def test_baixar_relatorio_via_link_direto(tmp_path):
    sessao = _make_sessao(html=_HTML_LINK_DOWNLOAD)

    baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")

    url_baixar = sessao.baixar.call_args[0][0]
    assert "download=csv" in url_baixar


def test_baixar_relatorio_sem_form_nem_link_levanta_runtime_error(tmp_path):
    sessao = _make_sessao(html=_HTML_SEM_DOWNLOAD)

    with pytest.raises(RuntimeError, match="[Dd]ownload"):
        baixar_relatorio(sessao, "https://moodle.example.com/report?id=1", tmp_path / "r.csv")


# ── main ─────────────────────────────────────────────────────────────────────


def test_main_levanta_runtime_error_sem_urls(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.moodle.urls_relatorios = []
    mocker.patch(f"{_PATCH}.MoodleSessao")

    with pytest.raises(RuntimeError, match="[Uu][Rr][Ll]"):
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
