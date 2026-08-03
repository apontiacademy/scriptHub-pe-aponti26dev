import csv

from scripthub.scripts.softskills.download_softskills import carregar_aprovados_do_backup


def _write_backup_csv(path, rows):
    fieldnames = ["Nome Completo", "E-mail", "Trilha", "Turma Trilha"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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
