import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DIRETORIO_BASE = Path(__file__).resolve().parent


@dataclass
class MoodleConfig:
    usuario: str
    senha: str
    caminho_download_relatorio: Path
    headless: bool
    csv_residentes: Path
    csv_saida_analise: Path
    url_login: str
    urls_relatorios: list[str]
    exportar_analise_relatorio: bool
    caminho_exportacao_analise: Path | None


@dataclass
class GsheetsConfig:
    id_planilha: str
    nome_aba: str
    caminho_backup_local: Path
    caminho_json_credenciais: Path


@dataclass
class Config:
    moodle: MoodleConfig
    gsheets: GsheetsConfig

    @staticmethod
    def load() -> "Config":
        dados_env = Config.__carregar_env()
        dados_settings = Config.__carregar_settings_json()

        moodle_json = dados_settings.get("moodle", {})
        gsheets_json = dados_settings.get("gsheets", {})

        moodle_config = MoodleConfig(
            usuario=dados_env["moodle_usuario"],
            senha=dados_env["moodle_senha"],
            caminho_download_relatorio=DIRETORIO_BASE / "dados" / "relatorios",
            headless=True,
            csv_residentes=Path(moodle_json.get("csvResidentes", str(DIRETORIO_BASE / "dados" / "residentes.csv"))),
            csv_saida_analise=DIRETORIO_BASE / "dados" / "resultado_analise.csv",
            url_login=moodle_json["urlLogin"],
            urls_relatorios=[i.strip() for i in moodle_json["urlsRelatorios"]],
            exportar_analise_relatorio=moodle_json["exportarAnaliseRelatorio"],
            caminho_exportacao_analise=(
                Path(moodle_json["caminhoExportacaoAnalise"])
                if moodle_json["exportarAnaliseRelatorio"] and moodle_json.get("caminhoExportacaoAnalise")
                else None
            ),
        )

        gsheets_config = GsheetsConfig(
            id_planilha=gsheets_json["idPlanilha"],
            nome_aba=gsheets_json["nomeAba"],
            caminho_backup_local=Path(gsheets_json["caminhoBackupLocal"]),
            caminho_json_credenciais=DIRETORIO_BASE / "credentials.json",
        )

        return Config(moodle=moodle_config, gsheets=gsheets_config)

    @staticmethod
    def __carregar_env() -> dict:
        load_dotenv(dotenv_path=DIRETORIO_BASE / ".env")

        dados = {
            "moodle_usuario": os.getenv("MOODLE_USUARIO"),
            "moodle_senha": os.getenv("MOODLE_SENHA"),
        }

        if not dados["moodle_usuario"] or not dados["moodle_senha"]:
            raise ValueError("MOODLE_USUARIO e MOODLE_SENHA devem ser definidos no arquivo .env")
        return dados

    @staticmethod
    def __carregar_settings_json() -> dict:
        caminho_settings = DIRETORIO_BASE / "settings.json"

        if not caminho_settings.exists():
            raise FileNotFoundError(f"O arquivo {caminho_settings} não foi encontrado.")

        with open(caminho_settings, encoding="utf-8") as f:
            dados = json.load(f)
            return dados
