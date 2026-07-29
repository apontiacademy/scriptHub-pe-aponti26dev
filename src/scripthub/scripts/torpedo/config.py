from dataclasses import dataclass
from pathlib import Path

import tomllib

from scripthub.services import diretorios, keyring_moodle, perfil
from scripthub.services.erros import ErroConfiguracao

DOMINIO = "torpedo"


def _diretorio_config() -> Path:
    return diretorios.caminho_config(perfil.resolver_perfil(), DOMINIO)


def _diretorio_dados() -> Path:
    return diretorios.caminho_dados(perfil.resolver_perfil(), DOMINIO)


@dataclass
class MoodleConfig:
    usuario: str
    senha: str
    url_login: str
    urls_foruns: list[str]
    headless: bool
    post_delay: int
    caminho_post_file: Path
    caminho_imagem: Path | None


@dataclass
class Config:
    moodle: MoodleConfig

    @staticmethod
    def load() -> "Config":
        dados_settings = Config.__carregar_settings_toml()
        moodle_toml = dados_settings.get("moodle", {})
        usuario, senha = Config.__carregar_credenciais_moodle(moodle_toml)

        caminho_imagem_raw = moodle_toml.get("caminhoImagem")

        moodle_config = MoodleConfig(
            usuario=usuario,
            senha=senha,
            url_login=moodle_toml["urlLogin"],
            urls_foruns=[i.strip() for i in moodle_toml["urlsForuns"]],
            headless=moodle_toml.get("headless", True),
            post_delay=moodle_toml.get("postDelay", 3),
            caminho_post_file=_diretorio_dados() / moodle_toml.get("caminhoPostFile", "post.md"),
            caminho_imagem=_diretorio_dados() / caminho_imagem_raw if caminho_imagem_raw else None,
        )

        return Config(moodle=moodle_config)

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
