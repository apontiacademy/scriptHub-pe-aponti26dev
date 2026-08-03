from unittest.mock import MagicMock

import pytest

from scripthub.scripts.relatorios.compilar.config import Config, MoodleConfig, PdfConfig
from scripthub.scripts.relatorios.compilar.download_de_relatorios import (
    _todos_relatorios_existem,
    baixar_relatorio,
    main,
)
from scripthub.services.erros import ErroIntegracao

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


def test_todos_relatorios_existem_true_quando_todos_presentes(tmp_path):
    f1 = tmp_path / "jan_1.csv"
    f1.write_text("data")
    caminhos = {"Janeiro": [f1]}

    assert _todos_relatorios_existem(caminhos) is True


def test_baixar_relatorio_apaga_arquivo_quando_validacao_csv_falha(tmp_path):
    sessao = _make_sessao(download_content_type="text/html")
    caminho_saida = tmp_path / "r.csv"
    caminho_saida.write_bytes(b"<html>lixo</html>")

    with pytest.raises(ErroIntegracao, match="[Cc][Ss][Vv]"):
        baixar_relatorio(sessao, "https://moodle.example.com/r", caminho_saida)

    assert not caminho_saida.exists()


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
