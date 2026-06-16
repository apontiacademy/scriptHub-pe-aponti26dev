import csv
import re
import time

from bs4 import BeautifulSoup

from .config import Config

# ── Constants ─────────────────────────────────────────────────────────────────

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

# ── Auth ──────────────────────────────────────────────────────────────────────

def login(session, config: Config):
    page = session.get(f'{config.moodle.url}/login/index.php')
    soup = BeautifulSoup(page.text, 'html.parser')
    token = soup.find('input', {'name': 'logintoken'})['value']
    session.post(f'{config.moodle.url}/login/index.php', data={
        'username': config.moodle.usuario,
        'password': config.moodle.senha,
        'logintoken': token,
        'anchor': '',
    })
    print('✓ Login OK')

# ── Bootcamp helpers ──────────────────────────────────────────────────────────

def get_turmas(session, config: Config):
    resp = session.get(
        f'{config.moodle.url}/course/index.php?categoryid={config.moodle.bootcamp_cat_id}'
    )
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


def download_csv(session, quiz_id, config: Config):
    r = session.get(f'{config.moodle.url}/mod/quiz/report.php?id={quiz_id}&mode=overview')
    sk = BeautifulSoup(r.text, 'html.parser').find('input', {'name': 'sesskey'})
    if not sk:
        return None
    dl = session.post(f'{config.moodle.url}/mod/quiz/report.php', data={
        'sesskey': sk['value'], 'download': 'csv', 'id': quiz_id,
        'mode': 'overview', 'attempts': 'enrolled_with',
        'onlygraded': '', 'onlyregraded': '', 'slotmarks': '',
    })
    if dl.status_code == 200 and 'csv' in dl.headers.get('Content-Type', ''):
        return dl.content
    return None

# ── Aprovados helpers ─────────────────────────────────────────────────────────

def get_approved_courses(session, config: Config):
    resp = session.get(
        f'{config.moodle.url}/course/index.php?categoryid={config.moodle.aprovados_cat_id}'
    )
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


def get_course_participants(session, course_id, course_name, config: Config):
    participants = []
    page = 0
    while True:
        url = f'{config.moodle.url}/user/index.php?id={course_id}&perpage=5000&page={page}'
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

def bootcamp_ja_baixado(config: Config) -> bool:
    output_dir = config.output_dir
    if not output_dir.is_dir():
        return False
    return any(
        subdir.is_dir() and any(f.suffix == '.csv' for f in subdir.iterdir())
        for subdir in output_dir.iterdir()
        if subdir.is_dir()
    )


def turmas_do_disco(config: Config) -> list:
    output_dir = config.output_dir
    if not output_dir.is_dir():
        return []
    return sorted(
        d.name for d in output_dir.iterdir()
        if d.is_dir() and d.name.isdigit()
    )


def aprovados_ja_baixados(config: Config) -> bool:
    aprovados_dir = config.aprovados_dir
    if not aprovados_dir.is_dir():
        return False
    return any(f.suffix == '.csv' for f in aprovados_dir.iterdir())


def aprovados_do_disco(config: Config) -> dict:
    approved = {}
    for fpath in config.aprovados_dir.iterdir():
        if fpath.suffix != '.csv':
            continue
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
