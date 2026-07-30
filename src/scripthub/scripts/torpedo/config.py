from dataclasses import dataclass
from pathlib import Path

import tomllib

from scripthub.services import diretorios, keyring_moodle, perfil
from scripthub.services.erros import ErroConfiguracao

DOMINIO = "torpedo"


def _diretorio_config() -> Path:
    return diretorios.caminho_config(perfil.resolver_perfil(), DOMINIO)


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

        caminho_post_file_raw = moodle_toml.get("caminhoPostFile")
        if not caminho_post_file_raw:
            raise ErroConfiguracao(f"settings.toml deve conter a chave 'moodle.caminhoPostFile' (domínio: {DOMINIO})")

        caminho_post_file = Path(caminho_post_file_raw)
        if not caminho_post_file.is_absolute():
            raise ErroConfiguracao(
                "moodle.caminhoPostFile deve ser um caminho absoluto. Configure com `scripthub config -s torpedo`."
            )

        caminho_imagem_raw = moodle_toml.get("caminhoImagem")
        caminho_imagem = Path(caminho_imagem_raw) if caminho_imagem_raw else None
        if caminho_imagem is not None and not caminho_imagem.is_absolute():
            raise ErroConfiguracao(
                "moodle.caminhoImagem deve ser um caminho absoluto. Configure com `scripthub config -s torpedo`."
            )

        moodle_config = MoodleConfig(
            usuario=usuario,
            senha=senha,
            url_login=moodle_toml["urlLogin"],
            urls_foruns=[i.strip() for i in moodle_toml["urlsForuns"]],
            headless=moodle_toml.get("headless", True),
            post_delay=moodle_toml.get("postDelay", 3),
            caminho_post_file=caminho_post_file,
            caminho_imagem=caminho_imagem,
        )

        return Config(moodle=moodle_config)

    @staticmethod
    def __carregar_credenciais_moodle(moodle_toml: dict) -> tuple[str, str]:
        usuario = moodle_toml.get("usuario")
        senha = keyring_moodle.obter_senha_moodle(DOMINIO, perfil.resolver_perfil())

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
