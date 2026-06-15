import requests
import csv
import io
import os
import re
import time
from bs4 import BeautifulSoup
from collections import defaultdict

# ── Config ────────────────────────────────────────────────────────────────────

MOODLE_URL        = 'https://moodle.aponti.org.br'
USERNAME          = 'yourmail-bfd@aponti.org.br'
PASSWORD          = 'youpassword'
BOOTCAMP_CAT_ID   = 'xxxx'
APROVADOS_CAT_ID  = 'xxxx'
OUTPUT_DIR        = os.path.join(os.path.dirname(__file__), 'resultados_softskills')

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

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    login(session)

    # ── 1. Download bootcamp activity CSVs ────────────────────────────────────
    print('\nBuscando turmas do bootcamp...')
    turmas = get_turmas(session)
    print(f'  {len(turmas)} turmas: {sorted(turmas.keys())}')

    print('\nBaixando atividades...')
    for turma_num in sorted(turmas.keys()):
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

    for turma_num in sorted(turmas.keys()):
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

    sem_notas = [t for t in sorted(turmas.keys())
                 if not any(r.get(f'Nota {label}', '')
                            for r in rows_out if r['Turma'] == t
                            for label, _ in ACTIVITIES)]
    if sem_notas:
        print(f'⚠️  Turmas sem notas: {sem_notas} (alunos ainda não responderam)')

    # ── 3. Build aprovados_bootcamp_fap2026.csv ───────────────────────────────
    print('\nColetando aprovados (categoria 140)...')
    approved_courses = get_approved_courses(session)
    print(f'  {len(approved_courses)} cursos encontrados')

    approved = {}
    for cid, name in approved_courses.items():
        parts = get_course_participants(session, cid, name)
        new = 0
        for p in parts:
            if p['email'] not in approved:
                approved[p['email']] = p
                new += 1
        print(f'  {name}: {len(parts)} participantes ({new} novos)')
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
        ap_rows.append({
            'Nome Completo':                info['nome'] or ss.get('Nome Completo', ''),
            'E-mail':                       email,
            'Trilha':                       trilha,
            'Turma Trilha':                 turma_trilha,
            'Nota Gestão de Tempo':         ss.get('Nota Gestão de Tempo', ''),
            'Nota Inteligência Emocional':  ss.get('Nota Inteligência Emocional', ''),
            'Nota Trabalho em Equipe':      ss.get('Nota Trabalho em Equipe', ''),
            'Nota Resolução de Problemas':  ss.get('Nota Resolução de Problemas', ''),
            'Nota Comunicação':             ss.get('Nota Comunicação', ''),
            'Nota Liderança Pessoal':       ss.get('Nota Liderança Pessoal', ''),
            'Nota Geral Soft Skills':       ss.get('Nota Geral Soft Skills', ''),
        })

    ap_path = os.path.join(os.path.dirname(__file__), 'aprovados_bootcamp_fap2026.csv')
    with open(ap_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=ap_fieldnames)
        writer.writeheader()
        writer.writerows(ap_rows)

    sem_ss = sum(1 for r in ap_rows if not r['Nota Gestão de Tempo'])
    print(f'✓ {ap_path} — {len(ap_rows)} aprovados ({len(ap_rows)-sem_ss} com notas soft skills)')


if __name__ == '__main__':
    main()
