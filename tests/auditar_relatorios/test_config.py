import json

import pytest

import scripthub.scripts.auditar_relatorios.config as cfg_module
from scripthub.scripts.auditar_relatorios.config import Config


@pytest.fixture
def settings_valido(tmp_path):
    return {
        "moodle": {
            "urlLogin": "https://example.com/login",
            "urlsRelatorios": [
                "https://example.com/relatorio1",
                "https://example.com/relatorio2",
            ],
            "headless": True,
            "csvResidentes": str(tmp_path / "residentes.csv"),
            "exportarAnaliseRelatorio": False,
        },
        "gsheets": {
            "idPlanilha": "planilha-id-123",
            "nomeAba": "Resultados",
            "caminhoBackupLocal": str(tmp_path / "backups"),
        },
    }


def test_load_retorna_config_completa(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url_login == "https://example.com/login"
    assert len(config.moodle.urls_relatorios) == 2
    assert config.moodle.headless is True
    assert config.gsheets.id_planilha == "planilha-id-123"
    assert config.gsheets.nome_aba == "Resultados"


def test_load_sem_usuario_levanta_value_error(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.delenv("MOODLE_USUARIO", raising=False)

    with pytest.raises(ValueError, match="MOODLE_USUARIO"):
        Config.load()


def test_load_sem_senha_levanta_value_error(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
    monkeypatch.delenv("MOODLE_SENHA", raising=False)

    with pytest.raises(ValueError, match="MOODLE_SENHA"):
        Config.load()


def test_load_sem_settings_levanta_file_not_found(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(FileNotFoundError):
        Config.load()


def test_exportar_analise_false_resulta_em_caminho_none(tmp_path, monkeypatch, settings_valido):
    settings_valido["moodle"]["exportarAnaliseRelatorio"] = False
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    assert config.moodle.caminho_exportacao_analise is None


def test_exportar_analise_true_com_caminho_preenchido(tmp_path, monkeypatch, settings_valido):
    settings_valido["moodle"]["exportarAnaliseRelatorio"] = True
    settings_valido["moodle"]["caminhoExportacaoAnalise"] = str(tmp_path / "saida.csv")
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings_valido), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    assert config.moodle.caminho_exportacao_analise == tmp_path / "saida.csv"
