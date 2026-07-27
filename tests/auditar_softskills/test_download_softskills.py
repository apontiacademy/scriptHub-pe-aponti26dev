import csv
from pathlib import Path
from unittest.mock import MagicMock

from bs4 import BeautifulSoup

from scripthub.scripts.auditar_softskills.config import Config, DriveConfig, MoodleConfig
from scripthub.scripts.auditar_softskills.download_softskills import (
    carregar_aprovados_do_backup,
    download_csv,
    extract_participant_name,
    get_approved_courses,
    get_course_participants,
    get_quiz_ids,
    get_turmas,
    split_trilha,
)


def _make_config(url="https://moodle.test", bootcamp_cat_id="136", aprovados_cat_id="140"):
    return Config(
        moodle=MoodleConfig(
            usuario="user",
            senha="pass",
            url=url,
            bootcamp_cat_id=bootcamp_cat_id,
            aprovados_cat_id=aprovados_cat_id,
        ),
        drive=DriveConfig(folder_id="folder-id", credentials_path=Path("creds.json")),
        output_dir=Path("/tmp/bootcamps"),
        aprovados_dir=Path("/tmp/aprovados"),
    )


# ── split_trilha ──────────────────────────────────────────────────────────────


def test_split_trilha_formato_valido():
    trilha, turma = split_trilha("Desenvolvimento Web - Turma 3")
    assert trilha == "Desenvolvimento Web"
    assert turma == "03"


def test_split_trilha_numero_ja_com_dois_digitos():
    trilha, turma = split_trilha("Data Science - Turma 12")
    assert trilha == "Data Science"
    assert turma == "12"


def test_split_trilha_sem_padrao_turma():
    trilha, turma = split_trilha("Trilha Sem Número")
    assert trilha == "Trilha Sem Número"
    assert turma == ""


def test_split_trilha_case_insensitive():
    trilha, turma = split_trilha("Design UX - turma 5")
    assert trilha == "Design UX"
    assert turma == "05"


def test_split_trilha_espacos_extras():
    trilha, turma = split_trilha("  Backend  -  Turma 2  ")
    assert trilha == "Backend"
    assert turma == "02"


# ── extract_participant_name ──────────────────────────────────────────────────


def _make_cell(html):
    return BeautifulSoup(html, "html.parser")


def test_extract_participant_name_formato_valido():
    cell = _make_cell("<td><label>Selecione 'João Silva'</label></td>")
    assert extract_participant_name(cell) == "João Silva"


def test_extract_participant_name_remove_ponto_final():
    cell = _make_cell("<td><label>Selecione 'Maria Souza.'</label></td>")
    assert extract_participant_name(cell) == "Maria Souza"


def test_extract_participant_name_sem_label():
    cell = _make_cell("<td>Sem label aqui</td>")
    assert extract_participant_name(cell) == ""


def test_extract_participant_name_label_sem_padrao():
    cell = _make_cell("<td><label>Texto qualquer sem aspas</label></td>")
    assert extract_participant_name(cell) == ""


# ── get_turmas ────────────────────────────────────────────────────────────────


def _mock_session_get(html):
    session = MagicMock()
    resp = MagicMock()
    resp.text = html
    session.get.return_value = resp
    return session


def test_get_turmas_encontra_turmas():
    html = """
    <html><body>
      <a href="/course/view.php?id=10">BootCamp Turma 1</a>
      <a href="/course/view.php?id=20">BootCamp Turma 2</a>
    </body></html>
    """
    session = _mock_session_get(html)
    turmas = get_turmas(session, config=_make_config(url="https://moodle.test"))

    assert "01" in turmas
    assert "02" in turmas
    assert turmas["01"] == "/course/view.php?id=10"
    assert turmas["02"] == "/course/view.php?id=20"


def test_get_turmas_ignora_links_sem_padrao():
    html = """
    <html><body>
      <a href="/course/view.php?id=5">Outro Curso</a>
      <a href="/course/view.php?id=10">BootCamp Turma 3</a>
    </body></html>
    """
    session = _mock_session_get(html)
    turmas = get_turmas(session, config=_make_config(url="https://moodle.test"))

    assert len(turmas) == 1
    assert "03" in turmas


def test_get_turmas_sem_duplicatas():
    html = """
    <html><body>
      <a href="/course/view.php?id=10">BootCamp Turma 1</a>
      <a href="/course/view.php?id=99">BootCamp Turma 1</a>
    </body></html>
    """
    session = _mock_session_get(html)
    turmas = get_turmas(session, config=_make_config(url="https://moodle.test"))

    assert len(turmas) == 1
    assert turmas["01"] == "/course/view.php?id=10"


def test_get_turmas_vazio():
    session = _mock_session_get("<html><body></body></html>")
    assert get_turmas(session, config=_make_config(url="https://moodle.test")) == {}


# ── get_quiz_ids ──────────────────────────────────────────────────────────────


def test_get_quiz_ids_encontra_atividades():
    html = """
    <html><body>
      <a href="/mod/quiz/view.php?id=1">Gestão de Tempo</a>
      <a href="/mod/quiz/view.php?id=2">Inteligência Emocional</a>
      <a href="/mod/quiz/view.php?id=3">Trabalho em Equipe</a>
      <a href="/mod/quiz/view.php?id=4">Resolução de Problemas</a>
      <a href="/mod/quiz/view.php?id=5">Comunicação</a>
      <a href="/mod/quiz/view.php?id=6">Liderança Pessoal</a>
    </body></html>
    """
    session = _mock_session_get(html)
    ids = get_quiz_ids(session, "/course/view.php?id=10")

    assert ids["activities"]["gestao_de_tempo"] == "1"
    assert ids["activities"]["inteligencia_emocional"] == "2"
    assert ids["activities"]["trabalho_em_equipe"] == "3"
    assert ids["activities"]["resolucao_de_problemas"] == "4"
    assert ids["activities"]["comunicacao"] == "5"
    assert ids["activities"]["lideranca_pessoal"] == "6"


def test_get_quiz_ids_encontra_avaliativa():
    html = """
    <html><body>
      <a href="/mod/quiz/view.php?id=99">Atividade Avaliativa Soft Skills</a>
    </body></html>
    """
    session = _mock_session_get(html)
    ids = get_quiz_ids(session, "/course/view.php?id=10")

    assert ids["avaliativa"] == "99"


def test_get_quiz_ids_ignora_software_e_letramento():
    html = """
    <html><body>
      <a href="/mod/quiz/view.php?id=10">Soft Skills de Software</a>
      <a href="/mod/quiz/view.php?id=11">Letramento em Soft Skills</a>
    </body></html>
    """
    session = _mock_session_get(html)
    ids = get_quiz_ids(session, "/course/view.php?id=10")

    assert ids["avaliativa"] is None


def test_get_quiz_ids_sem_quizzes():
    session = _mock_session_get('<html><body><a href="/outro">link</a></body></html>')
    ids = get_quiz_ids(session, "/course/view.php?id=10")

    assert ids["activities"] == {}
    assert ids["avaliativa"] is None


def test_get_quiz_ids_nao_duplica_mesmo_id():
    html = """
    <html><body>
      <a href="/mod/quiz/view.php?id=1">Gestão de Tempo</a>
      <a href="/mod/quiz/view.php?id=1">Gestão de Tempo (cópia)</a>
    </body></html>
    """
    session = _mock_session_get(html)
    ids = get_quiz_ids(session, "/course/view.php?id=10")

    assert ids["activities"]["gestao_de_tempo"] == "1"
    assert len(ids["activities"]) == 1


def test_get_quiz_ids_debug_false_nao_loga(mocker):
    mock_log = mocker.patch("scripthub.scripts.auditar_softskills.download_softskills.log")
    session = _mock_session_get('<html><body><a href="/outro">link</a></body></html>')

    get_quiz_ids(session, "/course/view.php?id=10", debug=False)

    mock_log.aviso.assert_not_called()


def test_get_quiz_ids_debug_true_com_atividades_nao_loga(mocker):
    mock_log = mocker.patch("scripthub.scripts.auditar_softskills.download_softskills.log")
    html = '<html><body><a href="/mod/quiz/view.php?id=1">Gestão de Tempo</a></body></html>'
    session = _mock_session_get(html)

    get_quiz_ids(session, "/course/view.php?id=10", debug=True)

    mock_log.aviso.assert_not_called()


def test_get_quiz_ids_debug_true_sem_atividades_loga_links_quiz(mocker):
    mock_log = mocker.patch("scripthub.scripts.auditar_softskills.download_softskills.log")
    html = (
        '<html><head><title>Curso X</title></head><body><a href="/mod/quiz/view.php?id=99">Outro Quiz</a></body></html>'
    )
    session = _mock_session_get(html)

    get_quiz_ids(session, "/course/view.php?id=10", debug=True)

    mensagens = [call.args[0] for call in mock_log.aviso.call_args_list]
    assert any("Links quiz" in m for m in mensagens)
    assert any("/mod/quiz/view.php?id=99" in m for m in mensagens)


def test_get_quiz_ids_debug_true_loga_sub_cursos(mocker):
    mock_log = mocker.patch("scripthub.scripts.auditar_softskills.download_softskills.log")
    html = '<html><body><a href="/course/view.php?id=5">Sub-curso</a></body></html>'
    session = _mock_session_get(html)

    get_quiz_ids(session, "/course/view.php?id=10", debug=True)

    mensagens = [call.args[0] for call in mock_log.aviso.call_args_list]
    assert any("Sub-cursos na página" in m for m in mensagens)
    assert any("/course/view.php?id=5" in m for m in mensagens)


def test_get_quiz_ids_debug_true_sem_titulo_nao_lanca_excecao(mocker):
    mock_log = mocker.patch("scripthub.scripts.auditar_softskills.download_softskills.log")
    html = '<html><body><a href="/mod/quiz/view.php?id=99">Outro Quiz</a></body></html>'
    session = _mock_session_get(html)

    get_quiz_ids(session, "/course/view.php?id=10", debug=True)

    mensagens = [call.args[0] for call in mock_log.aviso.call_args_list]
    assert any("(sem título)" in m for m in mensagens)


def test_get_quiz_ids_debug_true_fallback_primeiros_hrefs(mocker):
    mock_log = mocker.patch("scripthub.scripts.auditar_softskills.download_softskills.log")
    html = '<html><body><a href="/outro/link">Nada relevante</a></body></html>'
    session = _mock_session_get(html)

    get_quiz_ids(session, "/course/view.php?id=10", debug=True)

    mensagens = [call.args[0] for call in mock_log.aviso.call_args_list]
    assert any("Primeiros 15 hrefs" in m for m in mensagens)
    assert any("/outro/link" in m for m in mensagens)


# ── download_csv ──────────────────────────────────────────────────────────────


def test_download_csv_retorna_conteudo():
    session = MagicMock()

    get_resp = MagicMock()
    get_resp.text = '<html><input name="sesskey" value="abc123"/></html>'
    session.get.return_value = get_resp

    post_resp = MagicMock()
    post_resp.status_code = 200
    post_resp.headers = {"Content-Type": "text/csv"}
    post_resp.content = b"Nome,Nota\nJoao,8.5"
    session.post.return_value = post_resp

    result = download_csv(session, "42", config=_make_config())

    assert result == b"Nome,Nota\nJoao,8.5"


def test_download_csv_sem_sesskey_retorna_none():
    session = MagicMock()
    get_resp = MagicMock()
    get_resp.text = "<html><p>Sem sesskey aqui</p></html>"
    session.get.return_value = get_resp

    result = download_csv(session, "42", config=_make_config())

    assert result is None
    session.post.assert_not_called()


def test_download_csv_post_sem_csv_retorna_none():
    session = MagicMock()

    get_resp = MagicMock()
    get_resp.text = '<html><input name="sesskey" value="abc123"/></html>'
    session.get.return_value = get_resp

    post_resp = MagicMock()
    post_resp.status_code = 200
    post_resp.headers = {"Content-Type": "text/html"}
    session.post.return_value = post_resp

    result = download_csv(session, "42", config=_make_config())

    assert result is None


def test_download_csv_post_status_erro_retorna_none():
    session = MagicMock()

    get_resp = MagicMock()
    get_resp.text = '<html><input name="sesskey" value="abc123"/></html>'
    session.get.return_value = get_resp

    post_resp = MagicMock()
    post_resp.status_code = 403
    post_resp.headers = {"Content-Type": "text/csv"}
    session.post.return_value = post_resp

    result = download_csv(session, "42", config=_make_config())

    assert result is None


# ── get_approved_courses ──────────────────────────────────────────────────────


def test_get_approved_courses_retorna_cursos():
    html = """
    <html><body>
      <a href="/course/view.php?id=5">Trilha Backend - Turma 1</a>
      <a href="/course/view.php?id=8">Trilha Frontend - Turma 2</a>
    </body></html>
    """
    session = _mock_session_get(html)
    courses = get_approved_courses(session, config=_make_config())

    assert "5" in courses
    assert courses["5"] == "Trilha Backend - Turma 1"
    assert "8" in courses
    assert courses["8"] == "Trilha Frontend - Turma 2"


def test_get_approved_courses_sem_duplicatas():
    html = """
    <html><body>
      <a href="/course/view.php?id=5">Trilha Backend</a>
      <a href="/course/view.php?id=5">Trilha Backend (repetido)</a>
    </body></html>
    """
    session = _mock_session_get(html)
    courses = get_approved_courses(session, config=_make_config())

    assert len(courses) == 1
    assert courses["5"] == "Trilha Backend"


def test_get_approved_courses_ignora_links_sem_course_view():
    html = """
    <html><body>
      <a href="/admin/index.php">Admin</a>
      <a href="/course/view.php?id=3">Trilha Válida</a>
    </body></html>
    """
    session = _mock_session_get(html)
    courses = get_approved_courses(session, config=_make_config())

    assert len(courses) == 1
    assert "3" in courses


# ── get_course_participants ───────────────────────────────────────────────────


def _make_participants_html(rows, include_table=True):
    if not include_table:
        return "<html><body><p>sem tabela</p></body></html>"
    trs = "".join(f"<tr><td><label>Selecione '{nome}'</label></td><td>{email}</td></tr>" for nome, email in rows)
    return f'<html><body><table id="participants"><tr><th>Nome</th><th>Email</th></tr>{trs}</table></body></html>'


def test_get_course_participants_retorna_participantes():
    html = _make_participants_html(
        [
            ("João Silva", "joao@example.com"),
            ("Maria Souza", "maria@example.com"),
        ]
    )
    session = _mock_session_get(html)
    parts = get_course_participants(session, "5", "Trilha Backend - Turma 1", config=_make_config())

    assert len(parts) == 2
    assert parts[0]["nome"] == "João Silva"
    assert parts[0]["email"] == "joao@example.com"
    assert parts[0]["trilha_raw"] == "Trilha Backend - Turma 1"


def test_get_course_participants_sem_tabela_retorna_vazio():
    html = _make_participants_html([], include_table=False)
    session = _mock_session_get(html)
    parts = get_course_participants(session, "5", "Trilha Backend", config=_make_config())

    assert parts == []


def test_get_course_participants_ignora_linha_sem_email():
    html = """
    <html><body>
      <table id="participants">
        <tr><th>Nome</th><th>Email</th></tr>
        <tr><td><label>Selecione 'João'</label></td><td>sem-arroba</td></tr>
        <tr><td><label>Selecione 'Maria'</label></td><td>maria@ok.com</td></tr>
      </table>
    </body></html>
    """
    session = _mock_session_get(html)
    parts = get_course_participants(session, "5", "Trilha X", config=_make_config())

    assert len(parts) == 1
    assert parts[0]["email"] == "maria@ok.com"


def test_get_course_participants_email_normalizado_para_minusculo():
    html = _make_participants_html([("Ana Lima", "ANA@EXAMPLE.COM")])
    session = _mock_session_get(html)
    parts = get_course_participants(session, "5", "Trilha Y", config=_make_config())

    assert parts[0]["email"] == "ana@example.com"


# ── carregar_aprovados_do_backup ────────────────────────────────────────────────


def _write_backup_csv(path, rows):
    fieldnames = ["Nome Completo", "E-mail", "Trilha", "Turma Trilha"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_carregar_aprovados_do_backup_arquivo_inexistente_retorna_vazio(tmp_path):
    ap_path = tmp_path / "nao_existe.csv"
    assert carregar_aprovados_do_backup(ap_path) == {}


def test_carregar_aprovados_do_backup_linha_valida(tmp_path):
    ap_path = tmp_path / "aprovados.csv"
    _write_backup_csv(
        ap_path,
        [{"Nome Completo": "João Silva", "E-mail": "Joao@Example.com", "Trilha": "Backend", "Turma Trilha": "3"}],
    )

    approved = carregar_aprovados_do_backup(ap_path)

    assert "joao@example.com" in approved
    info = approved["joao@example.com"]
    assert info["nome"] == "João Silva"
    assert info["trilha_raw"] == "Backend - Turma 03"


def test_carregar_aprovados_do_backup_turma_trilha_numerica_com_zero_padding(tmp_path):
    ap_path = tmp_path / "aprovados.csv"
    _write_backup_csv(
        ap_path,
        [{"Nome Completo": "Ana", "E-mail": "ana@example.com", "Trilha": "Frontend", "Turma Trilha": "3.0"}],
    )

    approved = carregar_aprovados_do_backup(ap_path)

    assert approved["ana@example.com"]["trilha_raw"] == "Frontend - Turma 03"


def test_carregar_aprovados_do_backup_turma_trilha_nao_numerica_mantem_string(tmp_path):
    ap_path = tmp_path / "aprovados.csv"
    _write_backup_csv(
        ap_path,
        [{"Nome Completo": "Bia", "E-mail": "bia@example.com", "Trilha": "Dados", "Turma Trilha": "3A"}],
    )

    approved = carregar_aprovados_do_backup(ap_path)

    assert approved["bia@example.com"]["trilha_raw"] == "Dados - Turma 3A"


def test_carregar_aprovados_do_backup_sem_turma_trilha_nao_adiciona_sufixo(tmp_path):
    ap_path = tmp_path / "aprovados.csv"
    _write_backup_csv(
        ap_path,
        [{"Nome Completo": "Caio", "E-mail": "caio@example.com", "Trilha": "Backend", "Turma Trilha": ""}],
    )

    approved = carregar_aprovados_do_backup(ap_path)

    assert approved["caio@example.com"]["trilha_raw"] == "Backend"


def test_carregar_aprovados_do_backup_email_duplicado_mantem_primeiro(tmp_path):
    ap_path = tmp_path / "aprovados.csv"
    _write_backup_csv(
        ap_path,
        [
            {"Nome Completo": "Duda 1", "E-mail": "duda@example.com", "Trilha": "Backend", "Turma Trilha": "1"},
            {"Nome Completo": "Duda 2", "E-mail": "DUDA@example.com", "Trilha": "Frontend", "Turma Trilha": "2"},
        ],
    )

    approved = carregar_aprovados_do_backup(ap_path)

    assert len(approved) == 1
    assert approved["duda@example.com"]["nome"] == "Duda 1"


def test_carregar_aprovados_do_backup_turma_trilha_infinito_mantem_string(tmp_path):
    ap_path = tmp_path / "aprovados.csv"
    _write_backup_csv(
        ap_path,
        [{"Nome Completo": "Rui", "E-mail": "rui@example.com", "Trilha": "Backend", "Turma Trilha": "inf"}],
    )

    approved = carregar_aprovados_do_backup(ap_path)

    assert approved["rui@example.com"]["trilha_raw"] == "Backend - Turma inf"


def test_carregar_aprovados_do_backup_email_vazio_ignora_linha(tmp_path):
    ap_path = tmp_path / "aprovados.csv"
    _write_backup_csv(
        ap_path,
        [{"Nome Completo": "Sem Email", "E-mail": "", "Trilha": "Backend", "Turma Trilha": "1"}],
    )

    approved = carregar_aprovados_do_backup(ap_path)

    assert approved == {}
