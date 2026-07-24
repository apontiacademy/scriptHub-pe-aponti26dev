import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from scripthub.services.erros import ErroConfiguracao

DIRETORIO_BASE = Path(__file__).resolve().parent
DIRETORIO_DOMINIO = DIRETORIO_BASE.parent


@dataclass
class MoodleConfig:
    usuario: str
    senha: str
    url_login: str
    urls_frequencias: dict[str, str]


@dataclass
class AtasConfig:
    caminho_saida: Path


@dataclass
class Config:
    moodle: MoodleConfig
    atas: AtasConfig

    @staticmethod
    def load() -> "Config":
        dados_env = Config.__carregar_env()
        dados_settings = Config.__carregar_settings_json()

        moodle_json = dados_settings.get("moodle", {})
        atas_json = dados_settings.get("atas", {})

        moodle_config = MoodleConfig(
            usuario=dados_env["moodle_usuario"],
            senha=dados_env["moodle_senha"],
            url_login=moodle_json["urlLogin"],
            urls_frequencias=moodle_json["urlsFrequencias"],
        )

        atas_config = AtasConfig(caminho_saida=Path(atas_json["caminhoSaida"]))

        return Config(moodle=moodle_config, atas=atas_config)

    @staticmethod
    def __carregar_env() -> dict:
        load_dotenv(dotenv_path=DIRETORIO_DOMINIO / ".env")

        dados = {
            "moodle_usuario": os.getenv("MOODLE_USUARIO"),
            "moodle_senha": os.getenv("MOODLE_SENHA"),
        }

        if not dados["moodle_usuario"] or not dados["moodle_senha"]:
            raise ErroConfiguracao("MOODLE_USUARIO e MOODLE_SENHA devem ser definidos no arquivo .env")
        return dados

    @staticmethod
    def __carregar_settings_json() -> dict:
        caminho_settings = DIRETORIO_DOMINIO / "settings.json"

        if not caminho_settings.exists():
            raise ErroConfiguracao(f"O arquivo {caminho_settings} não foi encontrado.")

        with open(caminho_settings, encoding="utf-8") as f:
            return json.load(f)
