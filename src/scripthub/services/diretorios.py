from pathlib import Path

import platformdirs

APPNAME = "scripthub"
APPAUTHOR = "apontiacademy"


def _dirs() -> platformdirs.PlatformDirs:
    return platformdirs.PlatformDirs(appname=APPNAME, appauthor=APPAUTHOR)


def caminho_config(perfil: str, dominio: str) -> Path:
    return Path(_dirs().user_config_dir) / perfil / dominio


def caminho_dados(perfil: str, dominio: str) -> Path:
    return Path(_dirs().user_data_dir) / perfil / dominio / "dados"


def caminho_log(perfil: str) -> Path:
    return Path(_dirs().user_state_dir) / perfil


def caminho_arquivo_perfil() -> Path:
    return Path(_dirs().user_config_dir) / "Profile"
