from dataclasses import dataclass
from pathlib import Path

import tomllib

from scripthub.scripts.frequencias import DOMINIO
from scripthub.services import diretorios, keyring_moodle, perfil
from scripthub.services.erros import ErroConfiguracao


def _diretorio_config() -> Path:
    return diretorios.caminho_config(perfil.resolver_perfil(), DOMINIO)


def _diretorio_dados() -> Path:
    return diretorios.caminho_dados(perfil.resolver_perfil(), DOMINIO)


@dataclass
class MoodleConfig:
    usuario: str
    senha: str
    url_login: str
    urls_frequencias: dict[str, str]


@dataclass
class AtasConfig:
    caminho_saida: Path
    caminho_logo: Path | None = None
    caminho_assinatura: Path | None = None


@dataclass
class Config:
    moodle: MoodleConfig
    atas: AtasConfig
    diretorio_download: Path

    @staticmethod
    def load() -> "Config":
        dados_settings = Config.__carregar_settings_toml()
        moodle_toml = dados_settings.get("moodle", {})
        atas_toml = dados_settings.get("atas", {})
        usuario, senha = Config.__carregar_credenciais_moodle(moodle_toml)

        moodle_config = MoodleConfig(
            usuario=usuario,
            senha=senha,
            url_login=moodle_toml["urlLogin"],
            urls_frequencias=moodle_toml["urlsFrequencias"],
        )

        caminho_saida = Path(atas_toml["caminhoSaida"])
        if not caminho_saida.is_absolute():
            raise ErroConfiguracao(
                "atas.caminhoSaida deve ser um caminho absoluto. Configure com `scripthub config -s frequencias`."
            )

        caminho_logo = Path(atas_toml["caminhoLogo"]) if atas_toml.get("caminhoLogo") else None
        if caminho_logo is not None and not caminho_logo.is_absolute():
            raise ErroConfiguracao(
                "atas.caminhoLogo deve ser um caminho absoluto. Configure com `scripthub config -s frequencias`."
            )

        caminho_assinatura = Path(atas_toml["caminhoAssinatura"]) if atas_toml.get("caminhoAssinatura") else None
        if caminho_assinatura is not None and not caminho_assinatura.is_absolute():
            raise ErroConfiguracao(
                "atas.caminhoAssinatura deve ser um caminho absoluto. Configure com `scripthub config -s frequencias`."
            )

        atas_config = AtasConfig(
            caminho_saida=caminho_saida,
            caminho_logo=caminho_logo,
            caminho_assinatura=caminho_assinatura,
        )

        return Config(
            moodle=moodle_config,
            atas=atas_config,
            diretorio_download=_diretorio_dados() / "frequencias",
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
