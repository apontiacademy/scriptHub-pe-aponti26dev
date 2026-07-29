import tomllib
from dataclasses import dataclass
from pathlib import Path

from scripthub.services import diretorios, keyring_moodle, perfil
from scripthub.services.erros import ErroConfiguracao

DOMINIO = "softskills"


def _diretorio_config() -> Path:
    return diretorios.caminho_config(perfil.resolver_perfil(), DOMINIO)


def _diretorio_dados() -> Path:
    return diretorios.caminho_dados(perfil.resolver_perfil(), DOMINIO)


def _obrigatorio(dados: dict, chave: str, caminho: str) -> str:
    valor = dados.get(chave)
    if not valor:
        raise ErroConfiguracao(f"settings.toml deve conter a chave '{caminho}'")
    return valor


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
        dados_settings = Config.__carregar_settings_toml()

        moodle_toml = dados_settings.get("moodle", {})
        drive_toml = dados_settings.get("drive", {})
        usuario, senha = Config.__carregar_credenciais_moodle(moodle_toml)

        credentials_raw = drive_toml.get("credentialsPath", "credentials.json")
        credentials_path = Path(credentials_raw)
        if not credentials_path.is_absolute():
            credentials_path = (_diretorio_config() / credentials_path).resolve()

        output_dir_raw = dados_settings.get("outputDir", "bootcamps")
        aprovados_dir_raw = dados_settings.get("aprovadosDir", "aprovados")

        url_raw = moodle_toml.get("urlBase") or moodle_toml.get("url")
        if not url_raw:
            raise ErroConfiguracao(
                "settings.toml deve conter a chave 'moodle.urlBase' (ou 'moodle.url' por compatibilidade)"
            )

        moodle_config = MoodleConfig(
            usuario=usuario,
            senha=senha,
            url=url_raw.rstrip("/"),
            bootcamp_cat_id=_obrigatorio(moodle_toml, "bootcampCatId", "moodle.bootcampCatId"),
            aprovados_cat_id=_obrigatorio(moodle_toml, "aprovadosCatId", "moodle.aprovadosCatId"),
        )

        drive_config = DriveConfig(
            folder_id=_obrigatorio(drive_toml, "folderId", "drive.folderId"),
            credentials_path=credentials_path,
        )

        return Config(
            moodle=moodle_config,
            drive=drive_config,
            output_dir=_diretorio_dados() / output_dir_raw,
            aprovados_dir=_diretorio_dados() / aprovados_dir_raw,
        )

    @staticmethod
    def __carregar_credenciais_moodle(moodle_toml: dict) -> tuple[str, str]:
        usuario = moodle_toml.get("usuario")
        senha = keyring_moodle.obter_senha_moodle(DOMINIO)

        if not usuario:
            raise ErroConfiguracao(f"moodle.usuario deve estar definido em settings.toml (domínio: {DOMINIO})")
        if not senha:
            raise ErroConfiguracao(f"A senha do Moodle deve estar salva no keyring do sistema (domínio: {DOMINIO})")

        return usuario, senha

    @staticmethod
    def __carregar_settings_toml() -> dict:
        caminho_settings = _diretorio_config() / "settings.toml"

        if not caminho_settings.exists():
            raise ErroConfiguracao(f"O arquivo {caminho_settings} não foi encontrado.")

        with open(caminho_settings, "rb") as f:
            return tomllib.load(f)
