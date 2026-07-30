from dataclasses import dataclass
from pathlib import Path

import tomllib

from scripthub.scripts.relatorios import DOMINIO
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
    meses: dict[str, list[str]]  # Now stores list of weekly URLs per month
    caminho_download: Path


@dataclass
class PdfConfig:
    caminho_saida: Path


@dataclass
class Config:
    moodle: MoodleConfig
    pdf: PdfConfig

    @staticmethod
    def load() -> "Config":
        dados_settings = Config.__carregar_settings_toml()
        moodle_toml = dados_settings.get("moodle", {})
        pdf_toml = dados_settings.get("pdf", {})
        usuario, senha = Config.__carregar_credenciais_moodle(moodle_toml)

        moodle_config = MoodleConfig(
            usuario=usuario,
            senha=senha,
            url_login=moodle_toml["urlLogin"],
            meses={
                k: [url.strip() for url in (v if isinstance(v, list) else [v])] for k, v in moodle_toml["meses"].items()
            },
            caminho_download=_diretorio_dados() / "relatorios",
        )

        caminho_saida = Path(pdf_toml["caminhoSaida"])
        if not caminho_saida.is_absolute():
            raise ErroConfiguracao(
                "pdf.caminhoSaida deve ser um caminho absoluto. Configure com `scripthub config -s relatorios`."
            )

        pdf_config = PdfConfig(caminho_saida=caminho_saida)

        return Config(moodle=moodle_config, pdf=pdf_config)

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
