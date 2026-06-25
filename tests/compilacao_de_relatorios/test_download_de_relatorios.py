from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from scripthub.scripts.compilacao_de_relatorios.config import Config, MoodleConfig, PdfConfig
from scripthub.scripts.compilacao_de_relatorios.download_de_relatorios import (
    _caminho_relatorio,
    _todos_relatorios_existem,
    baixar_relatorio,
    main,
)

_PATCH = "scripthub.scripts.compilacao_de_relatorios.download_de_relatorios"

_HTML_FORM = """
<html><body>
<form action="/mod/quiz/report.php" method="post">
  <input type="hidden" name="sesskey" value="sk1">
  <input type="hidden" name="id" value="1">
  <input type="submit" name="download" value="Download">
</form>
</body></html>
"""


def _resp(text="", url="https://moodle.example.com/report"):
    r = MagicMock()
    r.text = text
    r.url = url
    return r


def _make_config(tmp_path):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            url_login="https://moodle.example.com/login/index.php",
            headless=True,
            caminho_download=tmp_path / "relatorios",
            meses={"Janeiro": ["https://moodle.example.com/jan1"]},
        ),
        pdf=PdfConfig(
            caminho_saida=tmp_path / "pdfs",
            csv_residentes=tmp_path / "residentes.csv",
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
    sessao = MagicMock()
    sessao.get.return_value = _resp(_HTML_FORM)

    baixar_relatorio(sessao, "https://moodle.example.com/r", tmp_path / "r.csv")

    sessao.get.assert_called_once_with("https://moodle.example.com/r")


def test_baixar_relatorio_inclui_sesskey_no_post(tmp_path):
    sessao = MagicMock()
    sessao.get.return_value = _resp(_HTML_FORM)

    baixar_relatorio(sessao, "https://moodle.example.com/r", tmp_path / "r.csv")

    _, kwargs = sessao.baixar.call_args
    assert kwargs["data"].get("sesskey") == "sk1"


# ── main ─────────────────────────────────────────────────────────────────────


def test_main_levanta_runtime_error_sem_meses(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.moodle.meses = {}
    mocker.patch(f"{_PATCH}.MoodleSessao")

    with pytest.raises(RuntimeError, match="[Mm]ês|[Mm]es"):
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
