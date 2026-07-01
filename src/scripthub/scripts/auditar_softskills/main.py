import csv
import io
import re
import time
from collections import defaultdict
from pathlib import Path as _Path

import requests

import scripthub.scripts.auditar_softskills.download_softskills as download_softskills
import scripthub.scripts.auditar_softskills.integracao_drive as integracao_drive

from scripthub.services import log

from .config import Config


def main():
    config = Config.load()

    log.secao("PIPELINE DE SOFT SKILLS")

    session = None

    # ── 1. Download bootcamp ──────────────────────────────────────────────────
    if download_softskills.bootcamp_ja_baixado(config):
        log.passo("[CACHE] Dados do bootcamp já existem em disco — pulando download.")
        turmas_nums = download_softskills.turmas_do_disco(config)
        log.passo(f"{len(turmas_nums)} turmas encontradas: {turmas_nums}")
    else:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        download_softskills.login(session, config)

        log.passo("Buscando turmas do bootcamp...")
        turmas = download_softskills.get_turmas(session, config)
        turmas_nums = sorted(turmas.keys())
        log.passo(f"{len(turmas_nums)} turmas: {turmas_nums}")

        log.passo("Baixando atividades...")
        for i, turma_num in enumerate(turmas_nums):
            turma_dir = config.output_dir / turma_num
            turma_dir.mkdir(parents=True, exist_ok=True)
            quiz_ids = download_softskills.get_quiz_ids(session, turmas[turma_num], debug=(i == 0))
            log.passo(f"Turma {turma_num}:")

            for label, fname in download_softskills.ACTIVITIES:
                qid = quiz_ids["activities"].get(fname)
                if not qid:
                    log.aviso(f"[NOT FOUND] {label}")
                    continue
                content = download_softskills.download_csv(session, qid, config)
                if content:
                    (turma_dir / f"{fname}.csv").write_bytes(content)
                    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
                    has_nota = "Nota/10,00" in (list(rows[0].keys()) if rows else [])
                    log.ok(f"{label} — {len(rows)} alunos | nota={'sim' if has_nota else 'não'}")
                else:
                    log.erro(f"[ERROR] {label}")
                time.sleep(0.2)

            qid = quiz_ids["avaliativa"]
            if qid:
                content = download_softskills.download_csv(session, qid, config)
                if content:
                    (turma_dir / "atividade_avaliativa_softskills.csv").write_bytes(content)
                    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))
                    log.ok(f"Atividade Avaliativa SS — {len(rows)} alunos")
                else:
                    log.erro("[ERROR] Atividade Avaliativa SS")
            else:
                log.aviso("[NOT FOUND] Atividade Avaliativa SS")
            time.sleep(0.2)

    # ── 2. Build softskills_resultado.csv ─────────────────────────────────────
    log.passo("Construindo softskills_resultado.csv...")
    rows_out = []
    for turma_num in turmas_nums:
        turma_dir = config.output_dir / turma_num
        students = {}
        act_notas = defaultdict(dict)

        for label, fname in download_softskills.ACTIVITIES:
            fpath = turma_dir / f"{fname}.csv"
            if not fpath.exists():
                continue
            with open(fpath, encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    email = row.get("Endereço de e-mail", "").strip().lower()
                    if not email:
                        continue
                    if email not in students:
                        nome = row.get("Nome", "").strip()
                        sobrenome = row.get("Sobrenome", "").strip()
                        students[email] = nome if sobrenome in (".", "-", "") else f"{nome} {sobrenome}".strip()
                    act_notas[email][label] = row.get("Nota/10,00", "").strip()

        geral_notas = {}
        av_path = turma_dir / "atividade_avaliativa_softskills.csv"
        if av_path.exists():
            with open(av_path, encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    email = row.get("Endereço de e-mail", "").strip().lower()
                    geral_notas[email] = row.get("Nota/100,00", "").strip()

        for email, nome in sorted(students.items(), key=lambda x: x[1]):
            row_out = {"Turma": turma_num, "Nome Completo": nome, "E-mail": email}
            for label, _ in download_softskills.ACTIVITIES:
                row_out[f"Nota {label}"] = act_notas[email].get(label, "")
            row_out["Nota Geral Soft Skills"] = geral_notas.get(email, "")
            rows_out.append(row_out)

    ss_fieldnames = (
        ["Turma", "Nome Completo", "E-mail"]
        + [f"Nota {label}" for label, _ in download_softskills.ACTIVITIES]
        + ["Nota Geral Soft Skills"]
    )
    ss_path = config.output_dir / "softskills_resultado.csv"
    with open(ss_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=ss_fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    softskills_lookup = {r["E-mail"]: r for r in rows_out}
    log.ok(f"{ss_path} — {len(rows_out)} alunos")

    sem_notas = [
        t
        for t in turmas_nums
        if not any(
            r.get(f"Nota {label}", "")
            for r in rows_out
            if r["Turma"] == t
            for label, _ in download_softskills.ACTIVITIES
        )
    ]
    if sem_notas:
        log.aviso(f"Turmas sem notas: {sem_notas} (alunos ainda não responderam)")

    # ── 3. Build aprovados_bootcamp_fap2026.csv ───────────────────────────────
    ap_path = _Path(__file__).resolve().parent / "aprovados_bootcamp_fap2026.csv"
    approved = {}

    if ap_path.exists():
        with open(ap_path, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                email = row.get("E-mail", "").strip().lower()
                if not email or email in approved:
                    continue
                trilha = row.get("Trilha", "").strip()
                turma_str = row.get("Turma Trilha", "").strip()
                try:
                    turma_num = str(int(float(turma_str))).zfill(2) if turma_str else ""
                except ValueError:
                    turma_num = turma_str
                approved[email] = {
                    "nome": row.get("Nome Completo", "").strip(),
                    "email": email,
                    "trilha_raw": f"{trilha} - Turma {turma_num}" if trilha and turma_num else trilha,
                }
        if approved:
            log.passo(f"{len(approved)} aprovados carregados do backup local.")

    if not approved:
        if download_softskills.aprovados_ja_baixados(config):
            log.passo("[CACHE] Dados dos aprovados já existem em disco — pulando download.")
            approved = download_softskills.aprovados_do_disco(config)
            log.passo(f"{len(approved)} aprovados carregados do disco.")
        else:
            if session is None:
                session = requests.Session()
                session.headers.update({"User-Agent": "Mozilla/5.0"})
                download_softskills.login(session, config)

            log.passo("Coletando aprovados...")
            approved_courses = download_softskills.get_approved_courses(session, config)
            log.passo(f"{len(approved_courses)} cursos encontrados")

            config.aprovados_dir.mkdir(parents=True, exist_ok=True)
            ap_part_fieldnames = ["nome", "email", "trilha_raw"]

            for cid, name in approved_courses.items():
                parts = download_softskills.get_course_participants(session, cid, name, config)
                new = 0
                for p in parts:
                    if p["email"] not in approved:
                        approved[p["email"]] = p
                        new += 1
                log.passo(f"{name}: {len(parts)} participantes ({new} novos)")

                safe_name = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")
                ap_course_path = config.aprovados_dir / f"{safe_name}.csv"
                with open(ap_course_path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.DictWriter(f, fieldnames=ap_part_fieldnames)
                    writer.writeheader()
                    writer.writerows(parts)

                time.sleep(0.2)

    ap_fieldnames = [
        "Nome Completo",
        "E-mail",
        "Trilha",
        "Turma Trilha",
        "Nota Gestão de Tempo",
        "Nota Inteligência Emocional",
        "Nota Trabalho em Equipe",
        "Nota Resolução de Problemas",
        "Nota Comunicação",
        "Nota Liderança Pessoal",
        "Nota Geral Soft Skills",
    ]
    ap_rows = []
    for email, info in sorted(approved.items(), key=lambda x: x[1]["nome"]):
        trilha, turma_trilha = download_softskills.split_trilha(info["trilha_raw"])
        ss = softskills_lookup.get(email, {})

        def nota(campo, _ss=ss):
            return _ss.get(campo, "") or "0"

        ap_rows.append(
            {
                "Nome Completo": info["nome"] or ss.get("Nome Completo", ""),
                "E-mail": email,
                "Trilha": trilha,
                "Turma Trilha": turma_trilha,
                "Nota Gestão de Tempo": nota("Nota Gestão de Tempo"),
                "Nota Inteligência Emocional": nota("Nota Inteligência Emocional"),
                "Nota Trabalho em Equipe": nota("Nota Trabalho em Equipe"),
                "Nota Resolução de Problemas": nota("Nota Resolução de Problemas"),
                "Nota Comunicação": nota("Nota Comunicação"),
                "Nota Liderança Pessoal": nota("Nota Liderança Pessoal"),
                "Nota Geral Soft Skills": nota("Nota Geral Soft Skills"),
            }
        )

    with open(ap_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=ap_fieldnames)
        writer.writeheader()
        writer.writerows(ap_rows)

    sem_ss = sum(1 for r in ap_rows if r["Nota Gestão de Tempo"] == "0")
    log.passo("Construindo aprovados_bootcamp_fap2026.csv...")
    log.ok(f"{ap_path} — {len(ap_rows)} aprovados ({len(ap_rows) - sem_ss} com notas soft skills)")

    # ── 4. Upload para Google Drive ───────────────────────────────────────────
    log.passo("Enviando para o Google Drive...")
    integracao_drive.upload_to_drive(str(ap_path), config)

    log.ok("PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
