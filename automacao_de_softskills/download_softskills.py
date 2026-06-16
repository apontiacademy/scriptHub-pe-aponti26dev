import csv
import io
import os
import re
import time
from bs4 import BeautifulSoup


def login(session, config):
    """Realiza login no Moodle."""
    page = session.get(f"{config.moodle.url_base}/login/index.php")
    soup = BeautifulSoup(page.text, "html.parser")
    token_input = soup.find("input", {"name": "logintoken"})
    if token_input:
        token = token_input["value"]
        session.post(
            f"{config.moodle.url_base}/login/index.php",
            data={
                "username": config.moodle.usuario,
                "password": config.moodle.senha,
                "logintoken": token,
                "anchor": "",
            },
        )
        print("✓ Login OK")
    else:
        raise ValueError("Token de login não encontrado")


def get_turmas(session, config):
    """Obtém as turmas do bootcamp."""
    resp = session.get(
        f"{config.moodle.url_base}/course/index.php?categoryid={config.moodle.bootcamp_category_id}"
    )
    soup = BeautifulSoup(resp.text, "html.parser")
    turmas = {}
    for a in soup.find_all("a", href=True):
        text = a.text.strip() if a.text else ""
        href = a.get("href", "") or ""
        if "BootCamp Turma" in text and href and "course/view.php" in href:
            m = re.search(r"Turma\s+(\d+)", text)
            if m:
                num = m.group(1).zfill(2)
                if num not in turmas:
                    turmas[num] = href
    return turmas


def get_quiz_ids(session, config, course_url):
    """Obtém os IDs dos quizzes para uma turma."""
    resp = session.get(course_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    ids = {"activities": {}, "avaliativa": None}
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        text = re.sub(r"\s+", " ", a.text.strip()).lower()
        m = re.search(r"mod/quiz/view\.php\?id=(\d+)", str(href))
        if not m:
            continue
        qid = m.group(1)
        if qid in seen:
            continue

        for activity in config.moodle.activities:
            filename = activity["filename"]
            keywords = activity["keywords"]
            if filename not in ids["activities"] and any(kw in text for kw in keywords):
                ids["activities"][filename] = qid
                seen.add(qid)
                break
        else:
            if ids["avaliativa"] is None and any(
                kw in text for kw in config.moodle.softskills_keywords
            ):
                if "software" not in text and "letramento" not in text:
                    ids["avaliativa"] = qid
                    seen.add(qid)

    return ids


def download_csv(session, config, quiz_id):
    """Faz download do CSV de um quiz."""
    r = session.get(
        f"{config.moodle.url_base}/mod/quiz/report.php?id={quiz_id}&mode=overview"
    )
    sk = BeautifulSoup(r.text, "html.parser").find("input", {"name": "sesskey"})
    if not sk:
        return None
    dl = session.post(
        f"{config.moodle.url_base}/mod/quiz/report.php",
        data={
            "sesskey": sk["value"],
            "download": "csv",
            "id": quiz_id,
            "mode": "overview",
            "attempts": "enrolled_with",
            "onlygraded": "",
            "onlyregraded": "",
            "slotmarks": "",
        },
    )
    if dl.status_code == 200 and "csv" in dl.headers.get("Content-Type", ""):
        return dl.content
    return None


def download_bootcamp_data(session, config):
    """Faz download de todos os dados do bootcamp."""
    print("\nBuscando turmas do bootcamp...")
    turmas = get_turmas(session, config)
    print(f"  {len(turmas)} turmas: {sorted(turmas.keys())}")

    print("\nBaixando atividades...")
    results = {}

    for turma_num in sorted(turmas.keys()):
        turma_dir = os.path.join(config.moodle.output_directory, turma_num)
        os.makedirs(turma_dir, exist_ok=True)
        quiz_ids = get_quiz_ids(session, config, turmas[turma_num])
        print(f"  Turma {turma_num}:")

        activity_results = {}

        for activity in config.moodle.activities:
            label = activity["label"]
            filename = activity["filename"]
            qid = quiz_ids["activities"].get(filename)
            if not qid:
                print(f"    [NOT FOUND] {label}")
                continue
            content = download_csv(session, config, qid)
            if content:
                with open(os.path.join(turma_dir, f"{filename}.csv"), "wb") as f:
                    f.write(content)
                rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
                has_nota = "Nota/10,00" in (list(rows[0].keys()) if rows else [])
                print(
                    f"    [OK] {label} — {len(rows)} alunos | nota={'sim' if has_nota else 'não'}"
                )
                activity_results[filename] = {
                    "content": content,
                    "rows": rows,
                    "has_nota": has_nota,
                }
            else:
                print(f"    [ERROR] {label}")
            time.sleep(0.2)

        qid = quiz_ids["avaliativa"]
        if qid:
            content = download_csv(session, config, qid)
            if content:
                with open(
                    os.path.join(turma_dir, "atividade_avaliativa_softskills.csv"), "wb"
                ) as f:
                    f.write(content)
                rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
                print(f"    [OK] Atividade Avaliativa SS — {len(rows)} alunos")
                activity_results["avaliativa"] = {"content": content, "rows": rows}
            else:
                print("    [ERROR] Atividade Avaliativa SS")
        else:
            print("    [NOT FOUND] Atividade Avaliativa SS")
        time.sleep(0.2)

        results[turma_num] = activity_results

    return results
