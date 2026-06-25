import json
from pathlib import Path
from typing import Any

from dotenv import dotenv_values, set_key

from .. import log
from .campo import Campo

_SCRIPTS_FOLDER = Path(__file__).resolve().parents[2] / "scripts"


def _script_dir(nome_script: str) -> Path:
    return _SCRIPTS_FOLDER / nome_script


def carregar_valores(nome_script: str, campos: list[Campo]) -> dict[str, Any]:
    diretorio = _script_dir(nome_script)

    env_path = diretorio / ".env"
    env = dotenv_values(env_path) if env_path.exists() else {}

    settings_path = diretorio / "settings.json"
    settings: dict = {}
    if settings_path.exists():
        with open(settings_path, encoding="utf-8") as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                settings = {}

    valores: dict[str, Any] = {}
    for campo in campos:
        if campo.origem == "env":
            v = env.get(campo.env_var)
            valores[campo.chave] = v if v is not None and v != "" else None
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

    env_path = diretorio / ".env"
    settings_path = diretorio / "settings.json"

    campos_env = [c for c in campos if c.origem == "env"]
    campos_settings = [c for c in campos if c.origem == "settings"]

    if campos_env:
        if not env_path.exists():
            env_path.touch()
        for campo in campos_env:
            novo = valores.get(campo.chave)
            if novo is not None:
                set_key(str(env_path), campo.env_var, str(novo))

    if campos_settings:
        if settings_path.exists():
            with open(settings_path, encoding="utf-8") as f:
                try:
                    settings: dict = json.load(f)
                except json.JSONDecodeError:
                    log.aviso(f"{settings_path} estava corrompido e será reescrito.")
                    settings = {}
        else:
            settings = {}

        for campo in campos_settings:
            novo = valores.get(campo.chave)
            if novo is None and not campo.obrigatorio:
                continue
            if novo is None:
                continue
            node = settings
            for chave in campo.json_chaves[:-1]:
                node = node.setdefault(chave, {})
            chave_final = campo.json_chaves[-1]
            node[chave_final] = novo

        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            f.write("\n")
