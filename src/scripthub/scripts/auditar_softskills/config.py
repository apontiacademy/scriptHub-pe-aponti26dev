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
    url: str
    bootcamp_cat_id: str
    aprovados_cat_id: str


@dataclass
class DriveConfig:
    folder_id: str
    credentials_path: Path


@dataclass
class Config:
    moodle: MoodleConfig
    drive: DriveConfig
    output_dir: Path
    aprovados_dir: Path

    @staticmethod
    def load() -> "Config":
        dados_env = Config.__carregar_env()
        dados_settings = Config.__carregar_settings_json()

        moodle_json = dados_settings.get("moodle", {})
        drive_json = dados_settings.get("drive", {})

        credentials_raw = drive_json.get("credentialsPath", "credentials.json")
        credentials_path = Path(credentials_raw)
        if not credentials_path.is_absolute():
            credentials_path = (DIRETORIO_BASE / credentials_path).resolve()

        output_dir_raw = dados_settings.get("outputDir", "bootcamps")
        aprovados_dir_raw = dados_settings.get("aprovadosDir", "aprovados")

        moodle_config = MoodleConfig(
            usuario=dados_env["moodle_usuario"],
            senha=dados_env["moodle_senha"],
            url=moodle_json["urlBase"].rstrip("/"),
            bootcamp_cat_id=moodle_json["bootcampCatId"],
            aprovados_cat_id=moodle_json["aprovadosCatId"],
        )

        drive_config = DriveConfig(
            folder_id=drive_json["folderId"],
            credentials_path=credentials_path,
        )

        return Config(
            moodle=moodle_config,
            drive=drive_config,
            output_dir=DIRETORIO_BASE / output_dir_raw,
            aprovados_dir=DIRETORIO_BASE / aprovados_dir_raw,
        )

    @staticmethod
    def __carregar_env() -> dict:
        load_dotenv(DIRETORIO_BASE / ".env", override=True)

        usuario = os.getenv("MOODLE_USUARIO")
        senha = os.getenv("MOODLE_SENHA")

        if not usuario:
            raise ValueError("MOODLE_USUARIO deve ser definido no arquivo .env")
        if not senha:
            raise ValueError("MOODLE_SENHA deve ser definida no arquivo .env")

        return {
            "moodle_usuario": usuario,
            "moodle_senha": senha,
        }

    @staticmethod
    def __carregar_settings_json() -> dict:
        caminho_settings = DIRETORIO_BASE / "settings.json"

        if not caminho_settings.exists():
            raise FileNotFoundError(f"O arquivo {caminho_settings} não foi encontrado.")

        with open(caminho_settings, encoding="utf-8") as f:
            return json.load(f)
