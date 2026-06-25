import os
import sys
from pathlib import Path

from ..menu.main import HEADER, SCRIPTS_FOLDER, STYLE, discover_modules
from .esquemas import ESQUEMAS
from .persistencia import carregar_valores, persistir
from .ui import exibir_campos, obter_input, selecionar_campos, selecionar_script


def config(nome_script: str | None = None) -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print(HEADER)
    print()

    if nome_script is not None:
        if nome_script not in ESQUEMAS:
            nomes = ", ".join(sorted(ESQUEMAS.keys()))
            print(f"❌ Script '{nome_script}' não encontrado. Scripts disponíveis: {nomes}", file=sys.stderr)
            sys.exit(1)
    else:
        modulos = discover_modules(SCRIPTS_FOLDER)
        modulos_com_esquema = [(nome, desc) for nome, desc in modulos if nome in ESQUEMAS]

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
        novo = obter_input(campo, valores.get(campo.chave))
        novos_valores[campo.chave] = novo

    print()
    persistir(nome_script, campos, novos_valores)
    print(f"✅ Configuração de {nome_script} salva com sucesso!")


def visualizar(nome_script: str | None = None) -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print(HEADER)
    print()

    if nome_script is not None:
        if nome_script not in ESQUEMAS:
            nomes = ", ".join(sorted(ESQUEMAS.keys()))
            print(f"❌ Script '{nome_script}' não encontrado. Scripts disponíveis: {nomes}", file=sys.stderr)
            sys.exit(1)
    else:
        modulos = discover_modules(SCRIPTS_FOLDER)
        modulos_com_esquema = [(nome, desc) for nome, desc in modulos if nome in ESQUEMAS]

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
