import csv
import os
import re
import time
from bs4 import BeautifulSoup
from collections import defaultdict


def extract_participant_name(cell0):
    """Extrai o nome do participante de uma célula."""
    label = cell0.find("label")
    if label:
        m = re.search(r"Selecione '(.+)'", label.text.strip())
        if m:
            return m.group(1).strip().rstrip(".").strip()
    return ""


def split_trilha(trilha_str):
    """Divide a string de trilha em nome e número."""
    m = re.search(r"^(.+?)\s*-\s*Turma\s*(\d+)$", trilha_str.strip(), re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).strip().zfill(2)
    return trilha_str.strip(), ""


def get_approved_courses(session, config):
    """Obtém os cursos aprovados."""
    resp = session.get(
        f"{config.moodle.url_base}/course/index.php?categoryid={config.moodle.aprovados_category_id}"
    )
    soup = BeautifulSoup(resp.text, "html.parser")
    courses = {}
    for a in soup.find_all("a", href=True):
        text = a.text.strip() if a.text else ""
        href = a.get("href", "") or ""
        if href and "course/view.php" in href and text:
            m = re.search(r"id=(\d+)", str(href))
            if m and m.group(1) not in courses:
                courses[m.group(1)] = text
    return courses


def get_course_participants(session, config, course_id, course_name):
    """Obtém os participantes de um curso."""
    participants = []
    page = 0
    while True:
        url = f"{config.moodle.url_base}/user/index.php?id={course_id}&perpage=5000&page={page}"
        resp = session.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "participants"})
        if not table:
            break
        rows = table.find_all("tr")[1:]
        if not rows:
            break
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            nome = extract_participant_name(cells[0])
            email = cells[1].text.strip().lower()
            if "@" in email:
                participants.append(
                    {"nome": nome, "email": email, "trilha_raw": course_name}
                )
        if len(rows) < 5000:
            break
        page += 1
        time.sleep(0.3)
    return participants


def build_softskills_resultado(config, bootcamp_data):
    """Constrói o arquivo softskills_resultado.csv."""
    print("\nConstruindo softskills_resultado.csv...")
    rows_out = []

    for turma_num in sorted(bootcamp_data.keys()):
        turma_dir = os.path.join(config.moodle.output_directory, turma_num)
        students = {}
        act_notas = defaultdict(dict)

        for activity in config.moodle.activities:
            filename = activity["filename"]
            fpath = os.path.join(turma_dir, f"{filename}.csv")
            if not os.path.exists(fpath):
                continue
            with open(fpath, encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    email = row.get("Endereço de e-mail", "").strip().lower()
                    if not email:
                        continue
                    if email not in students:
                        nome = row.get("Nome", "").strip()
                        sobrenome = row.get("Sobrenome", "").strip()
                        students[email] = (
                            nome
                            if sobrenome in (".", "-", "")
                            else f"{nome} {sobrenome}".strip()
                        )
                    act_notas[email][activity["label"]] = row.get(
                        "Nota/10,00", ""
                    ).strip()

        geral_notas = {}
        av_path = os.path.join(turma_dir, "atividade_avaliativa_softskills.csv")
        if os.path.exists(av_path):
            with open(av_path, encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    email = row.get("Endereço de e-mail", "").strip().lower()
                    geral_notas[email] = row.get("Nota/100,00", "").strip()

        for email, nome in sorted(students.items(), key=lambda x: x[1]):
            row_out = {"Turma": turma_num, "Nome Completo": nome, "E-mail": email}
            for activity in config.moodle.activities:
                label = activity["label"]
                row_out[f"Nota {label}"] = act_notas[email].get(label, "")
            row_out["Nota Geral Soft Skills"] = geral_notas.get(email, "")
            rows_out.append(row_out)

    ss_fieldnames = (
        ["Turma", "Nome Completo", "E-mail"]
        + [f"Nota {activity['label']}" for activity in config.moodle.activities]
        + ["Nota Geral Soft Skills"]
    )
    ss_path = os.path.join(config.moodle.output_directory, "softskills_resultado.csv")
    with open(ss_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=ss_fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    softskills_lookup = {r["E-mail"]: r for r in rows_out}
    print(f"✓ {ss_path} — {len(rows_out)} alunos")

    sem_notas = [
        t
        for t in sorted(bootcamp_data.keys())
        if not any(
            r.get(f"Nota {activity['label']}", "")
            for r in rows_out
            if r["Turma"] == t
            for activity in config.moodle.activities
        )
    ]
    if sem_notas:
        print(f"⚠️  Turmas sem notas: {sem_notas} (alunos ainda não responderam)")

    return softskills_lookup


def build_aprovados_bootcamp(config, session, approved_courses, softskills_lookup):
    """Constrói o arquivo aprovados_bootcamp_fap2026.csv."""
    print("\nColetando aprovados...")
    approved = {}
    for cid, name in approved_courses.items():
        parts = get_course_participants(session, config, cid, name)
        new = 0
        for p in parts:
            if p["email"] not in approved:
                approved[p["email"]] = p
                new += 1
        print(f"  {name}: {len(parts)} participantes ({new} novos)")
        time.sleep(0.2)

    print("\nConstruindo aprovados_bootcamp_fap2026.csv...")
    ap_fieldnames = (
        [
            "Nome Completo",
            "E-mail",
            "Trilha",
            "Turma Trilha",
        ]
        + [f"Nota {activity['label']}" for activity in config.moodle.activities]
        + [
            "Nota Geral Soft Skills",
        ]
    )

    ap_rows = []
    for email, info in sorted(approved.items(), key=lambda x: x[1]["nome"]):
        trilha, turma_trilha = split_trilha(info["trilha_raw"])
        ss = softskills_lookup.get(email, {})
        row = {
            "Nome Completo": info["nome"] or ss.get("Nome Completo", ""),
            "E-mail": email,
            "Trilha": trilha,
            "Turma Trilha": turma_trilha,
        }
        for activity in config.moodle.activities:
            label = activity["label"]
            row[f"Nota {label}"] = ss.get(f"Nota {label}", "")
        row["Nota Geral Soft Skills"] = ss.get("Nota Geral Soft Skills", "")
        ap_rows.append(row)

    ap_path = os.path.join(os.path.dirname(__file__), "aprovados_bootcamp_fap2026.csv")
    with open(ap_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=ap_fieldnames)
        writer.writeheader()
        writer.writerows(ap_rows)

    sem_ss = sum(
        1 for r in ap_rows if not r[f"Nota {config.moodle.activities[0]['label']}"]
    )
    print(
        f"✓ {ap_path} — {len(ap_rows)} aprovados ({len(ap_rows) - sem_ss} com notas soft skills)"
    )

    return ap_path
