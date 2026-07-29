"""Migração do layout legado (settings.json/.env/dados dentro do pacote instalado)
para o novo layout (diretórios do SO via platformdirs + keyring), usada pelo comando
depreciado `scripthub migrate-legacy-config`. Não apaga nenhum arquivo/pasta de
origem — só copia/persiste no novo layout, para não arriscar perda de dados."""

import json
import shutil
from pathlib import Path

import tomli_w
import tomllib

import scripthub

from . import diretorios, keyring_moodle, log, perfil

_SCRIPTS_FOLDER = Path(scripthub.__file__).resolve().parent / "scripts"

_DOMINIO_RAIZ: dict[str, Path] = {
    "frequencias": _SCRIPTS_FOLDER / "frequencias",
    "relatorios": _SCRIPTS_FOLDER / "relatorios",
    "softskills": _SCRIPTS_FOLDER / "softskills",
    "torpedo": _SCRIPTS_FOLDER / "torpedo",
}

# Pastas de dados legadas conhecidas por domínio, resolvidas package-relative — os
# únicos "dados/" hardcoded do código-fonte antes da issue #78.
_DADOS_LEGADOS: dict[str, list[Path]] = {
    "frequencias": [],
    "relatorios": [_SCRIPTS_FOLDER / "relatorios" / "compilar" / "dados"],
    "softskills": [
        _SCRIPTS_FOLDER / "softskills" / "bootcamps",
        _SCRIPTS_FOLDER / "softskills" / "aprovados",
    ],
    "torpedo": [],
}


def _migrar_settings_json(raiz: Path, novo_config_dir: Path) -> bool:
    settings_json_path = raiz / "settings.json"
    if not settings_json_path.exists():
        return False

    with open(settings_json_path, encoding="utf-8") as f:
        settings = json.load(f)

    novo_config_dir.mkdir(parents=True, exist_ok=True)
    with open(novo_config_dir / "settings.toml", "wb") as f:
        tomli_w.dump(settings, f)
    log.ok(f"{settings_json_path} → {novo_config_dir / 'settings.toml'}")
    return True


def _migrar_env(raiz: Path, nome_dominio: str, novo_config_dir: Path) -> bool:
    env_path = raiz / ".env"
    if not env_path.exists():
        return False

    from dotenv import dotenv_values

    valores = dotenv_values(env_path)
    usuario = valores.get("MOODLE_USUARIO")
    senha = valores.get("MOODLE_SENHA")
    migrou = False

    if usuario:
        novo_config_dir.mkdir(parents=True, exist_ok=True)
        settings_toml_path = novo_config_dir / "settings.toml"
        settings: dict = {}
        if settings_toml_path.exists():
            with open(settings_toml_path, "rb") as f:
                settings = tomllib.load(f)
        settings.setdefault("moodle", {})["usuario"] = usuario
        with open(settings_toml_path, "wb") as f:
            tomli_w.dump(settings, f)
        log.ok(f"{env_path}: MOODLE_USUARIO → {settings_toml_path} (moodle.usuario)")
        migrou = True

    if senha:
        keyring_moodle.definir_senha_moodle(nome_dominio, senha)
        log.ok(f"{env_path}: MOODLE_SENHA → keyring do sistema (domínio: {nome_dominio})")
        migrou = True

    return migrou


def _migrar_dados_legados(nome_dominio: str, novo_dados_dir: Path) -> bool:
    migrou = False
    for pasta_dados in _DADOS_LEGADOS.get(nome_dominio, []):
        if not pasta_dados.exists():
            continue
        itens = list(pasta_dados.iterdir())
        if not itens:
            continue
        novo_dados_dir.mkdir(parents=True, exist_ok=True)
        for item in itens:
            destino = novo_dados_dir / item.name
            if destino.exists():
                continue
            shutil.move(str(item), str(destino))
        log.ok(f"{pasta_dados} → {novo_dados_dir}")
        migrou = True
    return migrou


def _migrar_dominio(nome_dominio: str) -> bool:
    raiz = _DOMINIO_RAIZ[nome_dominio]
    perfil_ativo = perfil.resolver_perfil()
    novo_config_dir = diretorios.caminho_config(perfil_ativo, nome_dominio)
    novo_dados_dir = diretorios.caminho_dados(perfil_ativo, nome_dominio)

    migrou_settings = _migrar_settings_json(raiz, novo_config_dir)
    migrou_env = _migrar_env(raiz, nome_dominio, novo_config_dir)
    migrou_dados = _migrar_dados_legados(nome_dominio, novo_dados_dir)

    return migrou_settings or migrou_env or migrou_dados


def migrar_configuracao_legada() -> None:
    resultados = [_migrar_dominio(nome_dominio) for nome_dominio in _DOMINIO_RAIZ]

    if not any(resultados):
        log.aviso("Nenhuma configuração no layout antigo foi encontrada. Nada a migrar.")
        return

    log.ok("Migração do layout antigo concluída.")
