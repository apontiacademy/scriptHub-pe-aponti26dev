from unittest.mock import MagicMock

import pytest

from scripthub.scripts.auditar_frequencias.config import Config, GsheetsConfig, MoodleConfig
from scripthub.scripts.auditar_frequencias.exportar_frequencias import exportar_frequencia, main

_PATCH = "scripthub.scripts.auditar_frequencias.exportar_frequencias"

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
    # O checkbox "Incluir observações" (includeremarks) deve ser marcado
    assert data.get("includeremarks") == "1"


def test_exportar_frequencia_inclui_checkbox_marcado_por_padrao_no_moodle(tmp_path):
    """Checkboxes com o atributo `checked` "bare" (sem valor, ex.: `checked`
    em vez de `checked="checked"`) devem ser detectados como marcados. O
    BeautifulSoup representa esse atributo como string vazia (falsy), então
    `if inp.get("checked")` nunca funciona — é preciso usar `has_attr`."""
    sessao = _make_sessao()

    exportar_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]
    assert data.get("includeallsessions") == "1"
    assert data.get("ident[id]") == "1"
    assert data.get("ident[username]") == "1"
    assert data.get("ident[email]") == "1"


def test_exportar_frequencia_seleciona_primeira_opcao_do_select_sem_selected(tmp_path):
    sessao = _make_sessao()

    exportar_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]
    # Nenhuma <option> do select "group" tem `selected` -> deve usar a primeira
    assert data.get("group") == "0"


def test_exportar_frequencia_ignora_forms_decorativos_da_pagina(tmp_path):
    """A página do Moodle tem outros <form> (editmode.php, busca do blog) além
    do mform real de export — o código deve escolher o mform, não o primeiro
    form cuja action não seja /login/."""
    sessao = _make_sessao()

    exportar_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    url_baixar = sessao.baixar.call_args[0][0]
    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]

    assert "attendance/export.php" in url_baixar
    assert "editmode.php" not in url_baixar
    assert data.get("sesskey") == "sk123"
    assert "pageurl" not in data


def test_exportar_frequencia_ignora_select_multiple(tmp_path):
    sessao = _make_sessao()

    exportar_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]
    # Select multiple (ex.: lista de usuários) não deve ter valor selecionado por padrão
    assert "users[]" not in data


def test_exportar_frequencia_forca_format_excel(tmp_path):
    sessao = _make_sessao()

    exportar_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]
    assert data.get("format") == "excel"


def test_exportar_frequencia_forca_format_excel_mesmo_se_nao_for_a_primeira_opcao(tmp_path):
    sessao = _make_sessao(html=_HTML_FORM_FORMAT_NAO_EXCEL_PRIMEIRO)

    exportar_frequencia(sessao, "https://moodle.example.com/freq?id=1", "Turma A", tmp_path)

    _, kwargs = sessao.baixar.call_args
    data = kwargs["data"]
    assert data.get("format") == "excel"


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


def test_exportar_frequencia_conteudo_salvo_invalido_levanta_runtime_error(tmp_path):
    sessao = _make_sessao()
    sessao.baixar.side_effect = _grava_arquivo(b"<!DOCTYPE html><html>pagina de exportacao</html>")

    with pytest.raises(RuntimeError, match="[Ee]xcel|[Vv]álido"):
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
