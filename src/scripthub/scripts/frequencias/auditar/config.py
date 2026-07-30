from dataclasses import dataclass
from pathlib import Path

import tomllib

from scripthub.scripts.frequencias import DOMINIO
from scripthub.services import diretorios, keyring_moodle, perfil
from scripthub.services.erros import ErroConfiguracao


def _diretorio_config() -> Path:
    return diretorios.caminho_config(perfil.resolver_perfil(), DOMINIO)


def _diretorio_cache() -> Path:
    return diretorios.caminho_cache(perfil.resolver_perfil(), DOMINIO)


@dataclass
class MoodleConfig:
    usuario: str
    senha: str
    url_login: str
    urls_frequencias: dict[str, str]


@dataclass
class GsheetsConfig:
    id_planilha: str
    caminho_json_credenciais: Path


@dataclass
class Config:
    moodle: MoodleConfig
    gsheets: GsheetsConfig
    diretorio_download: Path

    @staticmethod
    def load() -> "Config":
        dados_settings = Config.__carregar_settings_toml()
        moodle_toml = dados_settings.get("moodle", {})
        gsheets_toml = dados_settings.get("gsheets", {})
        usuario, senha = Config.__carregar_credenciais_moodle(moodle_toml)

        moodle_config = MoodleConfig(
            usuario=usuario,
            senha=senha,
            url_login=moodle_toml["urlLogin"],
            urls_frequencias=moodle_toml["urlsFrequencias"],
        )

        caminho_json_credenciais = Path(gsheets_toml["caminhoJsonCredenciais"])
        if not caminho_json_credenciais.is_absolute():
            raise ErroConfiguracao(
                "gsheets.caminhoJsonCredenciais deve ser um caminho absoluto. "
                "Configure com `scripthub config -s frequencias`."
            )

        gsheets_config = GsheetsConfig(
            id_planilha=gsheets_toml["idPlanilha"],
            caminho_json_credenciais=caminho_json_credenciais,
        )

        return Config(
            moodle=moodle_config,
            gsheets=gsheets_config,
            diretorio_download=_diretorio_cache() / "frequencias",
        )

    @staticmethod
    def __carregar_credenciais_moodle(moodle_toml: dict) -> tuple[str, str]:
        usuario = moodle_toml.get("usuario")
        senha = keyring_moodle.obter_senha_moodle(DOMINIO)

        if not usuario or not senha:
            raise ErroConfiguracao(
                "moodle.usuario deve estar em settings.toml e a senha do Moodle deve estar salva no keyring "
                f"do sistema. Configure com: scripthub config {DOMINIO}"
            )
        return usuario, senha

    @staticmethod
    def __carregar_settings_toml() -> dict:
        caminho_settings = _diretorio_config() / "settings.toml"

        if not caminho_settings.exists():
            raise ErroConfiguracao(f"O arquivo {caminho_settings} não foi encontrado.")

        with open(caminho_settings, "rb") as f:
            return tomllib.load(f)
