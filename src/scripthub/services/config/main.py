import sys
from pathlib import Path

from ..menu.main import SCRIPTS_FOLDER, discover_modules
from .esquemas import ESQUEMAS
from .persistencia import _script_dir, carregar_valores, persistir
from .ui import exibir_campos, obter_input, selecionar_campos, selecionar_script


def config(nome_script: str | None = None) -> None:
    if nome_script is not None:
        if nome_script not in ESQUEMAS:
            nomes = ", ".join(sorted(ESQUEMAS.keys()))
            print(f"❌ Script '{nome_script}' não encontrado. Scripts disponíveis: {nomes}", file=sys.stderr)
            sys.exit(1)
    else:
        modulos = discover_modules(SCRIPTS_FOLDER)
        modulos_com_esquema = [(nome, desc) for nome, _, desc in modulos if nome in ESQUEMAS]

        if not modulos_com_esquema:
            print("❌ Nenhum script com configuração disponível foi encontrado.", file=sys.stderr)
            return

        nome_script = selecionar_script(modulos_com_esquema)
        if nome_script is None:
            return

    campos = ESQUEMAS[nome_script]
    valores = carregar_valores(nome_script, campos)

    print()
    selecionados = selecionar_campos(campos, valores)

    if not selecionados:
        print("\nNenhum campo selecionado. Nada foi alterado.")
        return

    novos_valores = dict(valores)
    for campo in selecionados:
        if campo.depende_de and not novos_valores.get(campo.depende_de):
            novos_valores[campo.chave] = None
            continue
        novo = obter_input(campo, valores.get(campo.chave))
        novos_valores[campo.chave] = novo

    print()
    persistir(nome_script, campos, novos_valores)
    print(f"✅ Configuração de {nome_script} salva com sucesso!")


def visualizar(nome_script: str | None = None) -> None:
    if nome_script is not None:
        if nome_script not in ESQUEMAS:
            nomes = ", ".join(sorted(ESQUEMAS.keys()))
            print(f"❌ Script '{nome_script}' não encontrado. Scripts disponíveis: {nomes}", file=sys.stderr)
            sys.exit(1)
    else:
        modulos = discover_modules(SCRIPTS_FOLDER)
        modulos_com_esquema = [(nome, desc) for nome, _, desc in modulos if nome in ESQUEMAS]

        if not modulos_com_esquema:
            print("❌ Nenhum script com configuração disponível foi encontrado.", file=sys.stderr)
            return

        nome_script = selecionar_script(modulos_com_esquema)
        if nome_script is None:
            return

    campos = ESQUEMAS[nome_script]
    valores = carregar_valores(nome_script, campos)

    print(f"  Configuração atual de {nome_script}:")
    exibir_campos(campos, valores)


def limpar(nome_script: str | None = None) -> None:
    if nome_script is not None:
        if nome_script not in ESQUEMAS:
            nomes = ", ".join(sorted(ESQUEMAS.keys()))
            print(f"❌ Script '{nome_script}' não encontrado. Scripts disponíveis: {nomes}", file=sys.stderr)
            return
    else:
        modulos = discover_modules(SCRIPTS_FOLDER)
        modulos_com_esquema = [(nome, desc) for nome, _, desc in modulos if nome in ESQUEMAS]

        if not modulos_com_esquema:
            print("❌ Nenhum script com configuração disponível foi encontrado.", file=sys.stderr)
            return

        nome_script = selecionar_script(modulos_com_esquema)
        if nome_script is None:
            return

    pasta = _script_dir(nome_script)
    arquivos = [pasta / ".env", pasta / "settings.json"]
    existentes = [a for a in arquivos if a.exists()]

    if not existentes:
        print(f"  ⚠️  Nenhuma configuração encontrada para '{nome_script}'.")
        return

    print(f"\n  Arquivos que serão removidos:")
    for a in existentes:
        print(f"    • {a}")

    resposta = input("\nDeseja apagar esses arquivos? [s/N]: ").strip().lower()
    if resposta not in ("s", "sim"):
        print("  Operação cancelada.")
        return

    for a in existentes:
        a.unlink()
        print(f"  ✔ Removido: {a.name}")
    print(f"✅ Configuração de {nome_script} limpa com sucesso!")
