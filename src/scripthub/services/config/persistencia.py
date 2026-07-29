from pathlib import Path
from typing import Any

import tomli_w
import tomllib

from .. import diretorios, keyring_moodle, log, perfil
from .campo import Campo


def _script_dir(nome_script: str) -> Path:
    return diretorios.caminho_config(perfil.resolver_perfil(), nome_script)


def _remover_chave_toml(settings: dict, chaves: list[str]) -> None:
    if not chaves:
        return
    node = settings
    for chave in chaves[:-1]:
        node = node.get(chave, {})
        if not isinstance(node, dict):
            return
    node.pop(chaves[-1], None)


def carregar_valores(nome_script: str, campos: list[Campo]) -> dict[str, Any]:
    diretorio = _script_dir(nome_script)

    settings_path = diretorio / "settings.toml"
    settings: dict = {}
    if settings_path.exists():
        with open(settings_path, "rb") as f:
            try:
                settings = tomllib.load(f)
            except tomllib.TOMLDecodeError:
                settings = {}

    valores: dict[str, Any] = {}
    for campo in campos:
        if campo.origem == "keyring":
            valores[campo.chave] = keyring_moodle.obter_senha_moodle(nome_script)
        else:
            node: Any = settings
            for chave in campo.json_chaves:
                if isinstance(node, dict):
                    node = node.get(chave)
                else:
                    node = None
                    break
            valores[campo.chave] = node

    return valores


def persistir(nome_script: str, campos: list[Campo], valores: dict[str, Any]) -> None:
    diretorio = _script_dir(nome_script)
    diretorio.mkdir(parents=True, exist_ok=True)

    settings_path = diretorio / "settings.toml"

    campos_keyring = [c for c in campos if c.origem == "keyring"]
    campos_settings = [c for c in campos if c.origem == "settings"]

    for campo in campos_keyring:
        novo = valores.get(campo.chave)
        if novo is not None:
            keyring_moodle.definir_senha_moodle(nome_script, str(novo))

    if campos_settings:
        if settings_path.exists():
            with open(settings_path, "rb") as f:
                try:
                    settings: dict = tomllib.load(f)
                except tomllib.TOMLDecodeError:
                    log.aviso(f"{settings_path} estava corrompido e será reescrito.")
                    settings = {}
        else:
            settings = {}

        for campo in campos_settings:
            novo = valores.get(campo.chave)
            if novo is None:
                if not campo.obrigatorio:
                    _remover_chave_toml(settings, campo.json_chaves)
                continue
            node = settings
            for chave in campo.json_chaves[:-1]:
                node = node.setdefault(chave, {})
            chave_final = campo.json_chaves[-1]
            node[chave_final] = novo

        with open(settings_path, "wb") as f:
            tomli_w.dump(settings, f)
