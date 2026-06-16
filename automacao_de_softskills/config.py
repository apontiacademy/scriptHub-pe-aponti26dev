import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv

DIRETORIO_BASE = Path(__file__).resolve().parent


@dataclass
class MoodleConfig:
    url_base: str
    bootcamp_category_id: str
    aprovados_category_id: str
    output_directory: Path
    activities: List[Dict[str, Any]]
    softskills_keywords: List[str]
    usuario: str
    senha: str


@dataclass
class Config:
    moodle: MoodleConfig

    @staticmethod
    def load() -> "Config":
        dados_env = Config.__carregar_env()
        dados_settings = Config.__carregar_settings_json()

        moodle_json = dados_settings.get("moodle", {})

        moodle_config = MoodleConfig(
            url_base=moodle_json["urlBase"],
            bootcamp_category_id=moodle_json["bootcampCategoryId"],
            aprovados_category_id=moodle_json["aprovadosCategoryId"],
            output_directory=DIRETORIO_BASE / moodle_json["outputDirectory"],
            activities=moodle_json["activities"],
            softskills_keywords=moodle_json["softskillsKeywords"],
            usuario=dados_env["moodle_usuario"],
            senha=dados_env["moodle_senha"],
        )

        return Config(moodle=moodle_config)

    @staticmethod
    def __carregar_env() -> dict:
        load_dotenv(dotenv_path=DIRETORIO_BASE / ".env")

        dados = {
            "moodle_usuario": os.getenv("MOODLE_USUARIO"),
            "moodle_senha": os.getenv("MOODLE_SENHA"),
        }

        if not dados["moodle_usuario"] or not dados["moodle_senha"]:
            raise ValueError(
                "MOODLE_USUARIO e MOODLE_SENHA devem ser definidos no arquivo .env"
            )
        return dados

    @staticmethod
    def __carregar_settings_json() -> dict:
        caminho_settings = DIRETORIO_BASE / "settings.json"

        if not caminho_settings.exists():
            raise FileNotFoundError(f"O arquivo {caminho_settings} não foi encontrado.")

        with open(caminho_settings, "r", encoding="utf-8") as f:
            dados = json.load(f)
            return dados
