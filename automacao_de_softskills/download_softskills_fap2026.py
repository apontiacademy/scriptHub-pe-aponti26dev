import requests
import csv
import io
import os
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict
from dotenv import load_dotenv
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ── Config ────────────────────────────────────────────────────────────────────

load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env', override=True)

MOODLE_URL        = os.getenv('MOODLE_URL', 'https://moodle.aponti.org.br')
USERNAME          = os.getenv('USERNAME', '')
PASSWORD          = os.getenv('PASSWORD', '')
BOOTCAMP_CAT_ID   = os.getenv('BOOTCAMP_CAT_ID', '')
APROVADOS_CAT_ID  = os.getenv('APROVADOS_CAT_ID', '')
OUTPUT_DIR        = os.path.join(os.path.dirname(__file__), 'bootcamps')
APROVADOS_DIR     = os.path.join(os.path.dirname(__file__), 'aprovados')

CREDENTIALS_PATH  = os.getenv('GOOGLE_CREDENTIALS_PATH',
                               str(Path(__file__).resolve().parent.parent / 'credentials.json'))
DRIVE_FOLDER_ID   = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1zEXBzH4ovPHEMhRLE_QbUXk7wCow-1y0')

ACTIVITIES = [
    ('Gestão de Tempo',        'gestao_de_tempo'),
    ('Inteligência Emocional', 'inteligencia_emocional'),
    ('Trabalho em Equipe',     'trabalho_em_equipe'),
    ('Resolução de Problemas', 'resolucao_de_problemas'),
    ('Comunicação',            'comunicacao'),
    ('Liderança Pessoal',      'lideranca_pessoal'),
]

ACTIVITY_KEYWORDS = {
    'gestao_de_tempo':        ['gestão de tempo', 'gestao de tempo'],
    'inteligencia_emocional': ['inteligência emocional', 'inteligencia emocional'],
    'trabalho_em_equipe':     ['trabalho em equipe'],
    'resolucao_de_problemas': ['resolução de problemas', 'resolucao de problemas',
                               'resolução dos problemas', 'resolução problemas'],
    'comunicacao':            ['comunicação', 'comunicacao'],
    'lideranca_pessoal':      ['liderança pessoal', 'lideranca pessoal'],
}

SOFTSKILLS_KEYWORDS = ['soft skills', 'softskills', 'soft skill']

# ── Google Drive ──────────────────────────────────────────────────────────────

def upload_to_drive(file_path: str, folder_id: str) -> None:
    scopes = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets',
    ]
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=scopes
    )
    drive_service = build('drive', 'v3', credentials=creds)

    # Verifica se a pasta está acessível (suporta Shared Drives)
    try:
        folder_info = drive_service.files().get(
            fileId=folder_id, fields='id,name', supportsAllDrives=True
        ).execute()
        print(f'  • Pasta acessível: {folder_info["name"]}')
    except Exception as e:
        print(f'  ❌ Pasta não acessível (verifique o compartilhamento): {e}')
        return

    sheet_name = Path(file_path).stem  # nome sem extensão

    existing = drive_service.files().list(
        q=(
            f"name='{sheet_name}' and '{folder_id}' in parents"
            " and trashed=false"
            " and mimeType='application/vnd.google-apps.spreadsheet'"
        ),
        fields='files(id)',
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute().get('files', [])

    if existing:
        sheet_id = existing[0]['id']
        print(f'  • Planilha existente encontrada.')
    else:
        sheet_id = drive_service.files().create(
            body={
                'name': sheet_name,
                'parents': [folder_id],
                'mimeType': 'application/vnd.google-apps.spreadsheet',
            },
            fields='id',
            supportsAllDrives=True,
        ).execute()['id']
        print(f'  • Nova planilha criada no Drive.')

    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)

    try:
        ws = sh.worksheet('Dados')
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title='Dados', rows=10000, cols=20)

    def _parse(value):
        try:
            return float(value.replace(',', '.'))
        except (ValueError, AttributeError):
            return value

    with open(file_path, encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        num_cols = {i for i, col in enumerate(header) if col.startswith('Nota') or col == 'Turma Trilha'}
        data = [
            [_parse(cell) if i in num_cols else cell for i, cell in enumerate(row)]
            for row in reader
        ]

    ws.clear()
    ws.update([header] + data)

    # Aplica formato 0.00 nas colunas numéricas
    num_col_letters = [
        chr(ord('A') + i) for i in sorted(num_cols)
    ]
    for col_letter in num_col_letters:
        ws.format(
            f'{col_letter}2:{col_letter}{len(data) + 1}',
            {'numberFormat': {'type': 'NUMBER', 'pattern': '0.00'}},
        )

    print(f'  ✔ Aba "Dados" atualizada com {len(data)} linhas.')


# ── Auth ──────────────────────────────────────────────────────────────────────

def login(session):
    page = session.get(f'{MOODLE_URL}/login/index.php')
    soup = BeautifulSoup(page.text, 'html.parser')
    token = soup.find('input', {'name': 'logintoken'})['value']
    session.post(f'{MOODLE_URL}/login/index.php', data={
        'username': USERNAME, 'password': PASSWORD,
        'logintoken': token, 'anchor': '',
    })
    print('✓ Login OK')

# ── Bootcamp helpers ──────────────────────────────────────────────────────────

def get_turmas(session):
    resp = session.get(f'{MOODLE_URL}/course/index.php?categoryid={BOOTCAMP_CAT_ID}')
    soup = BeautifulSoup(resp.text, 'html.parser')
    turmas = {}
    for a in soup.find_all('a', href=True):
        text = a.text.strip()
        href = a.get('href', '')
        if 'BootCamp Turma' in text and 'course/view.php' in href:
            m = re.search(r'Turma\s+(\d+)', text)
            if m:
                num = m.group(1).zfill(2)
                if num not in turmas:
                    turmas[num] = href
    return turmas


def get_quiz_ids(session, course_url):
    resp = session.get(course_url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    ids = {'activities': {}, 'avaliativa': None}
    seen = set()

    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        text = re.sub(r'\s+', ' ', a.text.strip()).lower()
        m = re.search(r'mod/quiz/view\.php\?id=(\d+)', href)
        if not m:
            continue
        qid = m.group(1)
        if qid in seen:
            continue

        for key, keywords in ACTIVITY_KEYWORDS.items():
            if key not in ids['activities'] and any(kw in text for kw in keywords):
                ids['activities'][key] = qid
                seen.add(qid)
                break
        else:
            if ids['avaliativa'] is None and any(kw in text for kw in SOFTSKILLS_KEYWORDS):
                if 'software' not in text and 'letramento' not in text:
                    ids['avaliativa'] = qid
                    seen.add(qid)

    return ids


def download_csv(session, quiz_id):
    r = session.get(f'{MOODLE_URL}/mod/quiz/report.php?id={quiz_id}&mode=overview')
    sk = BeautifulSoup(r.text, 'html.parser').find('input', {'name': 'sesskey'})
    if not sk:
        return None
    dl = session.post(f'{MOODLE_URL}/mod/quiz/report.php', data={
        'sesskey': sk['value'], 'download': 'csv', 'id': quiz_id,
        'mode': 'overview', 'attempts': 'enrolled_with',
        'onlygraded': '', 'onlyregraded': '', 'slotmarks': '',
    })
    if dl.status_code == 200 and 'csv' in dl.headers.get('Content-Type', ''):
        return dl.content
    return None

# ── Aprovados helpers ─────────────────────────────────────────────────────────

def get_approved_courses(session):
    resp = session.get(f'{MOODLE_URL}/course/index.php?categoryid={APROVADOS_CAT_ID}')
    soup = BeautifulSoup(resp.text, 'html.parser')
    courses = {}
    for a in soup.find_all('a', href=True):
        text = a.text.strip()
        href = a.get('href', '')
        if 'course/view.php' in href and text:
            m = re.search(r'id=(\d+)', href)
            if m and m.group(1) not in courses:
                courses[m.group(1)] = text
    return courses


def extract_participant_name(cell0):
    label = cell0.find('label')
    if label:
        m = re.search(r"Selecione '(.+)'", label.text.strip())
        if m:
            return m.group(1).strip().rstrip('.').strip()
    return ''


def split_trilha(trilha_str):
    m = re.search(r'^(.+?)\s*-\s*Turma\s*(\d+)$', trilha_str.strip(), re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).strip().zfill(2)
    return trilha_str.strip(), ''


def get_course_participants(session, course_id, course_name):
    participants = []
    page = 0
    while True:
        url = f'{MOODLE_URL}/user/index.php?id={course_id}&perpage=5000&page={page}'
        resp = session.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', {'id': 'participants'})
        if not table:
            break
        rows = table.find_all('tr')[1:]
        if not rows:
            break
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 2:
                continue
            nome  = extract_participant_name(cells[0])
            email = cells[1].text.strip().lower()
            if '@' in email:
                participants.append({'nome': nome, 'email': email, 'trilha_raw': course_name})
        if len(rows) < 5000:
            break
        page += 1
        time.sleep(0.3)
    return participants

# ── Cache helpers ─────────────────────────────────────────────────────────────

def _bootcamp_ja_baixado() -> bool:
    if not os.path.isdir(OUTPUT_DIR):
        return False
    return any(
        os.path.isdir(os.path.join(OUTPUT_DIR, d)) and
        any(f.endswith('.csv') for f in os.listdir(os.path.join(OUTPUT_DIR, d)))
        for d in os.listdir(OUTPUT_DIR)
        if os.path.isdir(os.path.join(OUTPUT_DIR, d))
    )


def _turmas_do_disco() -> list[str]:
    if not os.path.isdir(OUTPUT_DIR):
        return []
    return sorted(
        d for d in os.listdir(OUTPUT_DIR)
        if os.path.isdir(os.path.join(OUTPUT_DIR, d)) and d.isdigit()
    )


def _aprovados_ja_baixados() -> bool:
    if not os.path.isdir(APROVADOS_DIR):
        return False
    return any(f.endswith('.csv') for f in os.listdir(APROVADOS_DIR))


def _aprovados_do_disco() -> dict:
    approved = {}
    for fname in os.listdir(APROVADOS_DIR):
        if not fname.endswith('.csv'):
            continue
        fpath = os.path.join(APROVADOS_DIR, fname)
        with open(fpath, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                email = row.get('email', '').strip().lower()
                if email and email not in approved:
                    approved[email] = {
                        'nome': row.get('nome', ''),
                        'email': email,
                        'trilha_raw': row.get('trilha_raw', ''),
                    }
    return approved


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    session = None

    # ── 1. Download bootcamp activity CSVs ────────────────────────────────────
    if _bootcamp_ja_baixado():
        print('\n[CACHE] Dados do bootcamp já existem em disco — pulando download.')
        turmas_nums = _turmas_do_disco()
        print(f'  {len(turmas_nums)} turmas encontradas: {turmas_nums}')
    else:
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        login(session)

        print('\nBuscando turmas do bootcamp...')
        turmas = get_turmas(session)
        turmas_nums = sorted(turmas.keys())
        print(f'  {len(turmas_nums)} turmas: {turmas_nums}')

        print('\nBaixando atividades...')
        for turma_num in turmas_nums:
            turma_dir = os.path.join(OUTPUT_DIR, turma_num)
            os.makedirs(turma_dir, exist_ok=True)
            quiz_ids = get_quiz_ids(session, turmas[turma_num])
            print(f'  Turma {turma_num}:')

            for label, fname in ACTIVITIES:
                qid = quiz_ids['activities'].get(fname)
                if not qid:
                    print(f'    [NOT FOUND] {label}')
                    continue
                content = download_csv(session, qid)
                if content:
                    with open(os.path.join(turma_dir, f'{fname}.csv'), 'wb') as f:
                        f.write(content)
                    rows = list(csv.DictReader(io.StringIO(content.decode('utf-8-sig'))))
                    has_nota = 'Nota/10,00' in (list(rows[0].keys()) if rows else [])
                    print(f'    [OK] {label} — {len(rows)} alunos | nota={"sim" if has_nota else "não"}')
                else:
                    print(f'    [ERROR] {label}')
                time.sleep(0.2)

            qid = quiz_ids['avaliativa']
            if qid:
                content = download_csv(session, qid)
                if content:
                    with open(os.path.join(turma_dir, 'atividade_avaliativa_softskills.csv'), 'wb') as f:
                        f.write(content)
                    rows = list(csv.DictReader(io.StringIO(content.decode('utf-8-sig'))))
                    print(f'    [OK] Atividade Avaliativa SS — {len(rows)} alunos')
                else:
                    print(f'    [ERROR] Atividade Avaliativa SS')
            else:
                print(f'    [NOT FOUND] Atividade Avaliativa SS')
            time.sleep(0.2)

    # ── 2. Build softskills_resultado.csv ─────────────────────────────────────
    print('\nConstruindo softskills_resultado.csv...')
    rows_out = []

    for turma_num in turmas_nums:
        turma_dir = os.path.join(OUTPUT_DIR, turma_num)
        students = {}
        act_notas = defaultdict(dict)

        for label, fname in ACTIVITIES:
            fpath = os.path.join(turma_dir, f'{fname}.csv')
            if not os.path.exists(fpath):
                continue
            with open(fpath, encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    email = row.get('Endereço de e-mail', '').strip().lower()
                    if not email:
                        continue
                    if email not in students:
                        nome      = row.get('Nome', '').strip()
                        sobrenome = row.get('Sobrenome', '').strip()
                        students[email] = nome if sobrenome in ('.', '-', '') else f'{nome} {sobrenome}'.strip()
                    act_notas[email][label] = row.get('Nota/10,00', '').strip()

        geral_notas = {}
        av_path = os.path.join(turma_dir, 'atividade_avaliativa_softskills.csv')
        if os.path.exists(av_path):
            with open(av_path, encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    email = row.get('Endereço de e-mail', '').strip().lower()
                    geral_notas[email] = row.get('Nota/100,00', '').strip()

        for email, nome in sorted(students.items(), key=lambda x: x[1]):
            row_out = {'Turma': turma_num, 'Nome Completo': nome, 'E-mail': email}
            for label, _ in ACTIVITIES:
                row_out[f'Nota {label}'] = act_notas[email].get(label, '')
            row_out['Nota Geral Soft Skills'] = geral_notas.get(email, '')
            rows_out.append(row_out)

    ss_fieldnames = (
        ['Turma', 'Nome Completo', 'E-mail'] +
        [f'Nota {label}' for label, _ in ACTIVITIES] +
        ['Nota Geral Soft Skills']
    )
    ss_path = os.path.join(OUTPUT_DIR, 'softskills_resultado.csv')
    with open(ss_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=ss_fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    softskills_lookup = {r['E-mail']: r for r in rows_out}
    print(f'✓ {ss_path} — {len(rows_out)} alunos')

    sem_notas = [t for t in turmas_nums
                 if not any(r.get(f'Nota {label}', '')
                            for r in rows_out if r['Turma'] == t
                            for label, _ in ACTIVITIES)]
    if sem_notas:
        print(f'⚠️  Turmas sem notas: {sem_notas} (alunos ainda não responderam)')

    # ── 3. Build aprovados_bootcamp_fap2026.csv ───────────────────────────────
    if _aprovados_ja_baixados():
        print('\n[CACHE] Dados dos aprovados já existem em disco — pulando download.')
        approved = _aprovados_do_disco()
        print(f'  {len(approved)} aprovados carregados do disco.')
    else:
        if session is None:
            session = requests.Session()
            session.headers.update({'User-Agent': 'Mozilla/5.0'})
            login(session)

        print('\nColetando aprovados...')
        approved_courses = get_approved_courses(session)
        print(f'  {len(approved_courses)} cursos encontrados')

        os.makedirs(APROVADOS_DIR, exist_ok=True)
        ap_part_fieldnames = ['nome', 'email', 'trilha_raw']

        approved = {}
        for cid, name in approved_courses.items():
            parts = get_course_participants(session, cid, name)
            new = 0
            for p in parts:
                if p['email'] not in approved:
                    approved[p['email']] = p
                    new += 1
            print(f'  {name}: {len(parts)} participantes ({new} novos)')

            safe_name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
            ap_course_path = os.path.join(APROVADOS_DIR, f'{safe_name}.csv')
            with open(ap_course_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=ap_part_fieldnames)
                writer.writeheader()
                writer.writerows(parts)

            time.sleep(0.2)

    print(f'\nConstruindo aprovados_bootcamp_fap2026.csv...')
    ap_fieldnames = [
        'Nome Completo', 'E-mail', 'Trilha', 'Turma Trilha',
        'Nota Gestão de Tempo', 'Nota Inteligência Emocional',
        'Nota Trabalho em Equipe', 'Nota Resolução de Problemas',
        'Nota Comunicação', 'Nota Liderança Pessoal',
        'Nota Geral Soft Skills',
    ]

    ap_rows = []
    for email, info in sorted(approved.items(), key=lambda x: x[1]['nome']):
        trilha, turma_trilha = split_trilha(info['trilha_raw'])
        ss = softskills_lookup.get(email, {})
        def nota(campo):
            return ss.get(campo, '') or '0'

        ap_rows.append({
            'Nome Completo':                info['nome'] or ss.get('Nome Completo', ''),
            'E-mail':                       email,
            'Trilha':                       trilha,
            'Turma Trilha':                 turma_trilha,
            'Nota Gestão de Tempo':         nota('Nota Gestão de Tempo'),
            'Nota Inteligência Emocional':  nota('Nota Inteligência Emocional'),
            'Nota Trabalho em Equipe':      nota('Nota Trabalho em Equipe'),
            'Nota Resolução de Problemas':  nota('Nota Resolução de Problemas'),
            'Nota Comunicação':             nota('Nota Comunicação'),
            'Nota Liderança Pessoal':       nota('Nota Liderança Pessoal'),
            'Nota Geral Soft Skills':       nota('Nota Geral Soft Skills'),
        })

    ap_path = os.path.join(os.path.dirname(__file__), 'aprovados_bootcamp_fap2026.csv')
    with open(ap_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=ap_fieldnames)
        writer.writeheader()
        writer.writerows(ap_rows)

    sem_ss = sum(1 for r in ap_rows if not r['Nota Gestão de Tempo'])
    print(f'✓ {ap_path} — {len(ap_rows)} aprovados ({len(ap_rows)-sem_ss} com notas soft skills)')

    print('\nEnviando para o Google Drive...')
    upload_to_drive(ap_path, DRIVE_FOLDER_ID)


if __name__ == '__main__':
    main()
