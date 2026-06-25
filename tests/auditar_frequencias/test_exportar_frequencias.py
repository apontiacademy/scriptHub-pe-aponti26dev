from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripthub.scripts.auditar_frequencias.config import Config, GsheetsConfig, MoodleConfig
from scripthub.scripts.auditar_frequencias.exportar_frequencias import exportar_frequencia, main

_PATCH = "scripthub.scripts.auditar_frequencias.exportar_frequencias"

_HTML_FORM = """
<html><body>
<form action="/mod/attendance/export.php" method="post">
  <input type="hidden" name="sesskey" value="sk123">
  <input type="hidden" name="id" value="456">
  <input type="checkbox" id="id_col_observa" name="column[2]" value="1">
  <label for="id_col_observa">Observa</label>
  <input type="submit" value="OK">
</form>
</body></html>
"""

_HTML_SEM_FORM = "<html><body><p>sem formulário</p></body></html>"


def _resp(text="", url="https://moodle.example.com/mod/attendance/view.php"):
    r = MagicMock()
    r.text = text
    r.url = url
    return r


def _make_sessao(html=_HTML_FORM, url="https://moodle.example.com/mod/attendance/view.php"):
    sessao = MagicMock()
    sessao.get.return_value = _resp(html, url)
    return sessao


def _make_config(tmp_path):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            url_login="https://moodle.example.com/login/index.php",
            urls_frequencias={"Turma A": "https://moodle.example.com/freq?id=1"},
            caminho_exportacao=tmp_path / "exportacao",
        ),
        gsheets=GsheetsConfig(
            id_planilha="planilha-id",
            caminho_json_credenciais=tmp_path / "creds.json",
        ),
    )


# ── exportar_frequencia ───────────────────────────────────────────────────────


def test_exportar_frequencia_faz_get_na_url(tmp_path):
    sessao = _make_sessao()

    exportar_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    sessao.get.assert_called_once_with("https://moodle.example.com/freq?id=1")


def test_exportar_frequencia_inclui_campos_ocultos_no_post(tmp_path):
    sessao = _make_sessao()

    exportar_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]
    assert data.get("sesskey") == "sk123"
    assert data.get("id") == "456"


def test_exportar_frequencia_marca_checkbox_observa(tmp_path):
    sessao = _make_sessao()

    exportar_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]
    # The "Observa" checkbox field must be present
    assert "column[2]" in data
    assert data["column[2]"] == "1"


def test_exportar_frequencia_salva_com_nome_da_turma(tmp_path):
    sessao = _make_sessao()

    exportar_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma XYZ", tmp_path)

    destino = sessao.baixar.call_args[0][1]
    assert destino.name == "Turma XYZ.xlsx"


def test_exportar_frequencia_posta_para_action_do_form(tmp_path):
    sessao = _make_sessao()

    exportar_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    url_baixar = sessao.baixar.call_args[0][0]
    assert "attendance/export.php" in url_baixar


def test_exportar_frequencia_sem_form_levanta_runtime_error(tmp_path):
    sessao = _make_sessao(html=_HTML_SEM_FORM)

    with pytest.raises(RuntimeError, match="[Ff]ormul"):
        exportar_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)


# ── main ─────────────────────────────────────────────────────────────────────


def test_main_cria_diretorio_de_exportacao(tmp_path, mocker):
    config = _make_config(tmp_path)
    mock_sessao_cls = mocker.patch(f"{_PATCH}.MoodleSessao")
    mock_sessao = mock_sessao_cls.return_value
    mock_sessao.get.return_value = _resp(_HTML_FORM)
    mocker.patch(f"{_PATCH}.exportar_frequencia")

    main(config)

    assert config.moodle.caminho_exportacao.exists()


def test_main_levanta_runtime_error_sem_urls(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.moodle.urls_frequencias = {}
    mocker.patch(f"{_PATCH}.MoodleSessao")

    with pytest.raises(RuntimeError, match="[Uu][Rr][Ll]"):
        main(config)


def test_main_chama_login_e_exportar_para_cada_turma(tmp_path, mocker):
    config = _make_config(tmp_path)
    config.moodle.urls_frequencias = {
        "Turma A": "https://moodle.example.com/f1",
        "Turma B": "https://moodle.example.com/f2",
    }
    mock_sessao_cls = mocker.patch(f"{_PATCH}.MoodleSessao")
    mock_sessao = mock_sessao_cls.return_value
    mock_exportar = mocker.patch(f"{_PATCH}.exportar_frequencia")

    main(config)

    mock_sessao.login.assert_called_once()
    assert mock_exportar.call_count == 2
