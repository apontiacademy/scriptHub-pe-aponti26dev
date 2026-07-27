from unittest.mock import MagicMock

import pytest

from scripthub.services.erros import ErroIntegracao
from scripthub.services.moodle.attendance import extrair_frequencia

_FORM_EDITMODE_DECOY = """
<form action="https://moodle.example.com/editmode.php" method="post" class="editmode-switch-form">
  <input type="hidden" name="sesskey" value="sk-editmode-decoy">
  <input type="hidden" name="pageurl" value="https://moodle.example.com/mod/attendance/export.php?id=456">
  <input type="hidden" name="context" value="1">
</form>
"""

_FORM_BLOG_SEARCH_DECOY = """
<form action="https://moodle.example.com/blog/index.php" method="get" class="mform simplesearchform">
  <input type="text" name="search" value="">
</form>
"""

_HTML_FORM = f"""
<html><body>
{_FORM_EDITMODE_DECOY}
{_FORM_BLOG_SEARCH_DECOY}
<form action="/mod/attendance/export.php" method="post" id="mform1_abc123" class="mform">
  <input type="hidden" name="sesskey" value="sk123">
  <input type="hidden" name="id" value="456">
  <select name="group" id="id_group">
    <option value="0">Todos os participantes</option>
    <option value="2320">Turma 1</option>
  </select>
  <select name="format" id="id_format">
    <option value="excel">Download no formato Excel</option>
    <option value="ooo">Download no formato OpenOffice</option>
    <option value="text">Download no formato de texto</option>
  </select>
  <select name="users[]" id="id_users" multiple>
    <option value="10">Aluno 1</option>
    <option value="20">Aluno 2</option>
  </select>
  <input type="checkbox" id="id_includeremarks" name="includeremarks" value="1">
  <label for="id_includeremarks">Incluir observações</label>
  <input type="checkbox" id="id_includeallsessions" name="includeallsessions" value="1" checked>
  <input type="checkbox" id="id_ident_id" name="ident[id]" value="1" checked>
  <input type="checkbox" id="id_ident_username" name="ident[username]" value="1" checked>
  <input type="checkbox" id="id_ident_email" name="ident[email]" value="1" checked>
  <input type="submit" value="OK">
</form>
</body></html>
"""

_HTML_FORM_FORMAT_NAO_EXCEL_PRIMEIRO = """
<html><body>
<form action="/mod/attendance/export.php" method="post" id="mform1_def456" class="mform">
  <input type="hidden" name="sesskey" value="sk123">
  <select name="format" id="id_format">
    <option value="ooo">Download no formato OpenOffice</option>
    <option value="excel">Download no formato Excel</option>
  </select>
  <input type="submit" value="OK">
</form>
</body></html>
"""

_HTML_SEM_FORM = "<html><body><p>sem formulário</p></body></html>"

_XLSX_VALIDO = b"PK\x03\x04conteudo-xlsx-fake"


def _resp(text="", url="https://moodle.example.com/mod/attendance/view.php"):
    r = MagicMock()
    r.text = text
    r.url = url
    return r


def _grava_arquivo(conteudo: bytes):
    def _side_effect(url, destino, **kwargs):
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)

    return _side_effect


def _make_sessao(html=_HTML_FORM, url="https://moodle.example.com/mod/attendance/view.php"):
    sessao = MagicMock()
    sessao.get.return_value = _resp(html, url)
    sessao.baixar.side_effect = _grava_arquivo(_XLSX_VALIDO)
    return sessao


def test_extrair_frequencia_faz_get_na_url(tmp_path):
    sessao = _make_sessao()

    extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    sessao.get.assert_called_once_with("https://moodle.example.com/freq?id=1")


def test_extrair_frequencia_inclui_campos_ocultos_no_post(tmp_path):
    sessao = _make_sessao()

    extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]
    assert data.get("sesskey") == "sk123"
    assert data.get("id") == "456"


def test_extrair_frequencia_marca_checkbox_observa(tmp_path):
    sessao = _make_sessao()

    extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    assert kwargs["data"].get("includeremarks") == "1"


def test_extrair_frequencia_inclui_checkbox_marcado_por_padrao_no_moodle(tmp_path):
    sessao = _make_sessao()

    extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]
    assert data.get("includeallsessions") == "1"
    assert data.get("ident[id]") == "1"
    assert data.get("ident[username]") == "1"
    assert data.get("ident[email]") == "1"


def test_extrair_frequencia_seleciona_primeira_opcao_do_select_sem_selected(tmp_path):
    sessao = _make_sessao()

    extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    assert kwargs["data"].get("group") == "0"


def test_extrair_frequencia_ignora_forms_decorativos_da_pagina(tmp_path):
    sessao = _make_sessao()

    extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    url_baixar = sessao.baixar.call_args[0][0]
    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]

    assert "attendance/export.php" in url_baixar
    assert "editmode.php" not in url_baixar
    assert data.get("sesskey") == "sk123"
    assert "pageurl" not in data


def test_extrair_frequencia_ignora_select_multiple(tmp_path):
    sessao = _make_sessao()

    extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    assert "users[]" not in kwargs["data"]


def test_extrair_frequencia_forca_format_excel(tmp_path):
    sessao = _make_sessao()

    extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    assert kwargs["data"].get("format") == "excel"


def test_extrair_frequencia_forca_format_excel_mesmo_se_nao_for_a_primeira_opcao(tmp_path):
    sessao = _make_sessao(html=_HTML_FORM_FORMAT_NAO_EXCEL_PRIMEIRO)

    extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    assert kwargs["data"].get("format") == "excel"


def test_extrair_frequencia_salva_com_nome_da_turma(tmp_path):
    sessao = _make_sessao()

    extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma XYZ", tmp_path)

    destino = sessao.baixar.call_args[0][1]
    assert destino.name == "Turma XYZ.xlsx"


def test_extrair_frequencia_posta_para_action_do_form(tmp_path):
    sessao = _make_sessao()

    extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    assert "attendance/export.php" in sessao.baixar.call_args[0][0]


def test_extrair_frequencia_sem_form_levanta_erro_integracao(tmp_path):
    sessao = _make_sessao(html=_HTML_SEM_FORM)

    with pytest.raises(ErroIntegracao, match="[Ff]ormul"):
        extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)


def test_extrair_frequencia_conteudo_salvo_invalido_levanta_erro_integracao(tmp_path):
    sessao = _make_sessao()
    sessao.baixar.side_effect = _grava_arquivo(b"<!DOCTYPE html><html>pagina de exportacao</html>")

    with pytest.raises(ErroIntegracao, match="[Ee]xcel|[Vv]álido"):
        extrair_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)
