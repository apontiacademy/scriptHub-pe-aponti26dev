from unittest.mock import MagicMock, patch

import gspread
import pytest
from bs4 import BeautifulSoup

from automacao_de_softskills.download_softskills_fap2026 import (
    download_csv,
    extract_participant_name,
    get_approved_courses,
    get_course_participants,
    upload_to_drive,
    get_quiz_ids,
    get_turmas,
    split_trilha,
)


# ── split_trilha ──────────────────────────────────────────────────────────────

def test_split_trilha_formato_valido():
    trilha, turma = split_trilha('Desenvolvimento Web - Turma 3')
    assert trilha == 'Desenvolvimento Web'
    assert turma == '03'


def test_split_trilha_numero_ja_com_dois_digitos():
    trilha, turma = split_trilha('Data Science - Turma 12')
    assert trilha == 'Data Science'
    assert turma == '12'


def test_split_trilha_sem_padrao_turma():
    trilha, turma = split_trilha('Trilha Sem Número')
    assert trilha == 'Trilha Sem Número'
    assert turma == ''


def test_split_trilha_case_insensitive():
    trilha, turma = split_trilha('Design UX - turma 5')
    assert trilha == 'Design UX'
    assert turma == '05'


def test_split_trilha_espacos_extras():
    trilha, turma = split_trilha('  Backend  -  Turma 2  ')
    assert trilha == 'Backend'
    assert turma == '02'


# ── extract_participant_name ──────────────────────────────────────────────────

def _make_cell(html):
    return BeautifulSoup(html, 'html.parser')


def test_extract_participant_name_formato_valido():
    cell = _make_cell("<td><label>Selecione 'João Silva'</label></td>")
    assert extract_participant_name(cell) == 'João Silva'


def test_extract_participant_name_remove_ponto_final():
    cell = _make_cell("<td><label>Selecione 'Maria Souza.'</label></td>")
    assert extract_participant_name(cell) == 'Maria Souza'


def test_extract_participant_name_sem_label():
    cell = _make_cell("<td>Sem label aqui</td>")
    assert extract_participant_name(cell) == ''


def test_extract_participant_name_label_sem_padrao():
    cell = _make_cell("<td><label>Texto qualquer sem aspas</label></td>")
    assert extract_participant_name(cell) == ''


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
    turmas = get_turmas(session)

    assert '01' in turmas
    assert '02' in turmas
    assert turmas['01'] == '/course/view.php?id=10'
    assert turmas['02'] == '/course/view.php?id=20'


def test_get_turmas_ignora_links_sem_padrao():
    html = """
    <html><body>
      <a href="/course/view.php?id=5">Outro Curso</a>
      <a href="/course/view.php?id=10">BootCamp Turma 3</a>
    </body></html>
    """
    session = _mock_session_get(html)
    turmas = get_turmas(session)

    assert len(turmas) == 1
    assert '03' in turmas


def test_get_turmas_sem_duplicatas():
    html = """
    <html><body>
      <a href="/course/view.php?id=10">BootCamp Turma 1</a>
      <a href="/course/view.php?id=99">BootCamp Turma 1</a>
    </body></html>
    """
    session = _mock_session_get(html)
    turmas = get_turmas(session)

    assert len(turmas) == 1
    assert turmas['01'] == '/course/view.php?id=10'


def test_get_turmas_vazio():
    session = _mock_session_get('<html><body></body></html>')
    assert get_turmas(session) == {}


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
    ids = get_quiz_ids(session, '/course/view.php?id=10')

    assert ids['activities']['gestao_de_tempo'] == '1'
    assert ids['activities']['inteligencia_emocional'] == '2'
    assert ids['activities']['trabalho_em_equipe'] == '3'
    assert ids['activities']['resolucao_de_problemas'] == '4'
    assert ids['activities']['comunicacao'] == '5'
    assert ids['activities']['lideranca_pessoal'] == '6'


def test_get_quiz_ids_encontra_avaliativa():
    html = """
    <html><body>
      <a href="/mod/quiz/view.php?id=99">Atividade Avaliativa Soft Skills</a>
    </body></html>
    """
    session = _mock_session_get(html)
    ids = get_quiz_ids(session, '/course/view.php?id=10')

    assert ids['avaliativa'] == '99'


def test_get_quiz_ids_ignora_software_e_letramento():
    html = """
    <html><body>
      <a href="/mod/quiz/view.php?id=10">Soft Skills de Software</a>
      <a href="/mod/quiz/view.php?id=11">Letramento em Soft Skills</a>
    </body></html>
    """
    session = _mock_session_get(html)
    ids = get_quiz_ids(session, '/course/view.php?id=10')

    assert ids['avaliativa'] is None


def test_get_quiz_ids_sem_quizzes():
    session = _mock_session_get('<html><body><a href="/outro">link</a></body></html>')
    ids = get_quiz_ids(session, '/course/view.php?id=10')

    assert ids['activities'] == {}
    assert ids['avaliativa'] is None


def test_get_quiz_ids_nao_duplica_mesmo_id():
    html = """
    <html><body>
      <a href="/mod/quiz/view.php?id=1">Gestão de Tempo</a>
      <a href="/mod/quiz/view.php?id=1">Gestão de Tempo (cópia)</a>
    </body></html>
    """
    session = _mock_session_get(html)
    ids = get_quiz_ids(session, '/course/view.php?id=10')

    assert ids['activities']['gestao_de_tempo'] == '1'
    assert len(ids['activities']) == 1


# ── download_csv ──────────────────────────────────────────────────────────────

def test_download_csv_retorna_conteudo():
    session = MagicMock()

    get_resp = MagicMock()
    get_resp.text = '<html><input name="sesskey" value="abc123"/></html>'
    session.get.return_value = get_resp

    post_resp = MagicMock()
    post_resp.status_code = 200
    post_resp.headers = {'Content-Type': 'text/csv'}
    post_resp.content = b'Nome,Nota\nJoao,8.5'
    session.post.return_value = post_resp

    result = download_csv(session, '42')

    assert result == b'Nome,Nota\nJoao,8.5'


def test_download_csv_sem_sesskey_retorna_none():
    session = MagicMock()
    get_resp = MagicMock()
    get_resp.text = '<html><p>Sem sesskey aqui</p></html>'
    session.get.return_value = get_resp

    result = download_csv(session, '42')

    assert result is None
    session.post.assert_not_called()


def test_download_csv_post_sem_csv_retorna_none():
    session = MagicMock()

    get_resp = MagicMock()
    get_resp.text = '<html><input name="sesskey" value="abc123"/></html>'
    session.get.return_value = get_resp

    post_resp = MagicMock()
    post_resp.status_code = 200
    post_resp.headers = {'Content-Type': 'text/html'}
    session.post.return_value = post_resp

    result = download_csv(session, '42')

    assert result is None


def test_download_csv_post_status_erro_retorna_none():
    session = MagicMock()

    get_resp = MagicMock()
    get_resp.text = '<html><input name="sesskey" value="abc123"/></html>'
    session.get.return_value = get_resp

    post_resp = MagicMock()
    post_resp.status_code = 403
    post_resp.headers = {'Content-Type': 'text/csv'}
    session.post.return_value = post_resp

    result = download_csv(session, '42')

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
    courses = get_approved_courses(session)

    assert '5' in courses
    assert courses['5'] == 'Trilha Backend - Turma 1'
    assert '8' in courses
    assert courses['8'] == 'Trilha Frontend - Turma 2'


def test_get_approved_courses_sem_duplicatas():
    html = """
    <html><body>
      <a href="/course/view.php?id=5">Trilha Backend</a>
      <a href="/course/view.php?id=5">Trilha Backend (repetido)</a>
    </body></html>
    """
    session = _mock_session_get(html)
    courses = get_approved_courses(session)

    assert len(courses) == 1
    assert courses['5'] == 'Trilha Backend'


def test_get_approved_courses_ignora_links_sem_course_view():
    html = """
    <html><body>
      <a href="/admin/index.php">Admin</a>
      <a href="/course/view.php?id=3">Trilha Válida</a>
    </body></html>
    """
    session = _mock_session_get(html)
    courses = get_approved_courses(session)

    assert len(courses) == 1
    assert '3' in courses


# ── get_course_participants ───────────────────────────────────────────────────

def _make_participants_html(rows, include_table=True):
    if not include_table:
        return '<html><body><p>sem tabela</p></body></html>'
    trs = ''.join(
        f"<tr><td><label>Selecione '{nome}'</label></td><td>{email}</td></tr>"
        for nome, email in rows
    )
    return f'<html><body><table id="participants"><tr><th>Nome</th><th>Email</th></tr>{trs}</table></body></html>'


def test_get_course_participants_retorna_participantes():
    html = _make_participants_html([
        ('João Silva', 'joao@example.com'),
        ('Maria Souza', 'maria@example.com'),
    ])
    session = _mock_session_get(html)
    parts = get_course_participants(session, '5', 'Trilha Backend - Turma 1')

    assert len(parts) == 2
    assert parts[0]['nome'] == 'João Silva'
    assert parts[0]['email'] == 'joao@example.com'
    assert parts[0]['trilha_raw'] == 'Trilha Backend - Turma 1'


def test_get_course_participants_sem_tabela_retorna_vazio():
    html = _make_participants_html([], include_table=False)
    session = _mock_session_get(html)
    parts = get_course_participants(session, '5', 'Trilha Backend')

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
    parts = get_course_participants(session, '5', 'Trilha X')

    assert len(parts) == 1
    assert parts[0]['email'] == 'maria@ok.com'


def test_get_course_participants_email_normalizado_para_minusculo():
    html = _make_participants_html([('Ana Lima', 'ANA@EXAMPLE.COM')])
    session = _mock_session_get(html)
    parts = get_course_participants(session, '5', 'Trilha Y')

    assert parts[0]['email'] == 'ana@example.com'


# ── upload_to_drive ───────────────────────────────────────────────────────────

def _make_drive_service(existing_files=None):
    service = MagicMock()
    files = service.files.return_value
    files.list.return_value.execute.return_value = {'files': existing_files or []}
    files.create.return_value.execute.return_value = {'id': 'novo-id-123'}
    return service


def _make_sheets_mock(worksheet_exists=True):
    """Retorna mocks de gspread (gc, spreadsheet, worksheet)."""
    ws = MagicMock()
    sh = MagicMock()

    if worksheet_exists:
        sh.worksheet.return_value = ws
    else:
        sh.worksheet.side_effect = gspread.WorksheetNotFound
        sh.add_worksheet.return_value = ws

    gc = MagicMock()
    gc.open_by_key.return_value = sh
    return gc, sh, ws


@patch('automacao_de_softskills.download_softskills_fap2026.gspread.authorize')
@patch('automacao_de_softskills.download_softskills_fap2026.build')
@patch('automacao_de_softskills.download_softskills_fap2026.service_account.Credentials.from_service_account_file')
def test_upload_to_drive_cria_planilha_quando_nao_existe(mock_creds, mock_build, mock_authorize, tmp_path):
    csv_file = tmp_path / 'aprovados_bootcamp_fap2026.csv'
    csv_file.write_text('Nome,Email\nJoão,joao@example.com')

    service = _make_drive_service(existing_files=[])
    mock_build.return_value = service
    gc, sh, ws = _make_sheets_mock()
    mock_authorize.return_value = gc

    upload_to_drive(str(csv_file), 'pasta-id-123')

    service.files.return_value.create.assert_called_once()
    call_kwargs = service.files.return_value.create.call_args
    assert call_kwargs.kwargs['body']['name'] == 'aprovados_bootcamp_fap2026'
    assert call_kwargs.kwargs['body']['parents'] == ['pasta-id-123']
    assert call_kwargs.kwargs['body']['mimeType'] == 'application/vnd.google-apps.spreadsheet'


@patch('automacao_de_softskills.download_softskills_fap2026.gspread.authorize')
@patch('automacao_de_softskills.download_softskills_fap2026.build')
@patch('automacao_de_softskills.download_softskills_fap2026.service_account.Credentials.from_service_account_file')
def test_upload_to_drive_reutiliza_planilha_existente(mock_creds, mock_build, mock_authorize, tmp_path):
    csv_file = tmp_path / 'aprovados_bootcamp_fap2026.csv'
    csv_file.write_text('Nome,Email\nJoão,joao@example.com')

    service = _make_drive_service(existing_files=[{'id': 'planilha-existente-456'}])
    mock_build.return_value = service
    gc, sh, ws = _make_sheets_mock()
    mock_authorize.return_value = gc

    upload_to_drive(str(csv_file), 'pasta-id-123')

    service.files.return_value.create.assert_not_called()
    gc.open_by_key.assert_called_once_with('planilha-existente-456')


@patch('automacao_de_softskills.download_softskills_fap2026.gspread.authorize')
@patch('automacao_de_softskills.download_softskills_fap2026.build')
@patch('automacao_de_softskills.download_softskills_fap2026.service_account.Credentials.from_service_account_file')
def test_upload_to_drive_atualiza_apenas_aba_dados(mock_creds, mock_build, mock_authorize, tmp_path):
    csv_file = tmp_path / 'aprovados_bootcamp_fap2026.csv'
    csv_file.write_text('Nome,Email\nJoão,joao@example.com')

    mock_build.return_value = _make_drive_service(existing_files=[{'id': 'abc'}])
    gc, sh, ws = _make_sheets_mock(worksheet_exists=True)
    mock_authorize.return_value = gc

    upload_to_drive(str(csv_file), 'pasta-id-123')

    sh.worksheet.assert_called_once_with('Dados')
    ws.clear.assert_called_once()
    ws.update.assert_called_once()


@patch('automacao_de_softskills.download_softskills_fap2026.gspread.authorize')
@patch('automacao_de_softskills.download_softskills_fap2026.build')
@patch('automacao_de_softskills.download_softskills_fap2026.service_account.Credentials.from_service_account_file')
def test_upload_to_drive_cria_aba_dados_se_nao_existir(mock_creds, mock_build, mock_authorize, tmp_path):
    csv_file = tmp_path / 'aprovados_bootcamp_fap2026.csv'
    csv_file.write_text('Nome,Email\nJoão,joao@example.com')

    mock_build.return_value = _make_drive_service(existing_files=[{'id': 'abc'}])
    gc, sh, ws = _make_sheets_mock(worksheet_exists=False)
    mock_authorize.return_value = gc

    upload_to_drive(str(csv_file), 'pasta-id-123')

    sh.add_worksheet.assert_called_once_with(title='Dados', rows=10000, cols=20)
    ws.clear.assert_called_once()
    ws.update.assert_called_once()


@patch('automacao_de_softskills.download_softskills_fap2026.gspread.authorize')
@patch('automacao_de_softskills.download_softskills_fap2026.build')
@patch('automacao_de_softskills.download_softskills_fap2026.service_account.Credentials.from_service_account_file')
def test_upload_to_drive_nunca_deleta(mock_creds, mock_build, mock_authorize, tmp_path):
    csv_file = tmp_path / 'aprovados_bootcamp_fap2026.csv'
    csv_file.write_text('Nome,Email\nJoão,joao@example.com')

    service = _make_drive_service(existing_files=[{'id': 'abc'}])
    mock_build.return_value = service
    gc, sh, ws = _make_sheets_mock()
    mock_authorize.return_value = gc

    upload_to_drive(str(csv_file), 'pasta-id-123')

    service.files.return_value.delete.assert_not_called()
    sh.del_worksheet.assert_not_called()


@patch('automacao_de_softskills.download_softskills_fap2026.gspread.authorize')
@patch('automacao_de_softskills.download_softskills_fap2026.build')
@patch('automacao_de_softskills.download_softskills_fap2026.service_account.Credentials.from_service_account_file')
def test_upload_to_drive_autentica_com_scopes_corretos(mock_creds, mock_build, mock_authorize, tmp_path):
    csv_file = tmp_path / 'aprovados_bootcamp_fap2026.csv'
    csv_file.write_text('Nome,Email\nJoão,joao@example.com')

    mock_build.return_value = _make_drive_service()
    mock_authorize.return_value = _make_sheets_mock()[0]

    upload_to_drive(str(csv_file), 'pasta-id-123')

    _, kwargs = mock_creds.call_args
    assert 'https://www.googleapis.com/auth/drive.file' in kwargs['scopes']
    assert 'https://www.googleapis.com/auth/spreadsheets' in kwargs['scopes']
