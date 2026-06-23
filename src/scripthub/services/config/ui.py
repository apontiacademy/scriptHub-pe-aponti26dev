import re
from typing import Any

import questionary
from questionary import Style

from .campo import Campo
from .validacao import resumo_valor, validar_campo

STYLE = Style(
    [
        ("qmark", "fg:#00bfff bold"),
        ("question", "bold"),
        ("answer", "fg:#00bfff bold"),
        ("pointer", "fg:#00bfff bold"),
        ("highlighted", "fg:#00bfff bold"),
        ("selected", "fg:#00bfff"),
        ("separator", "fg:#444444"),
        ("instruction", "fg:#666666"),
        ("text", ""),
    ]
)

_SEPARADOR = "─" * 50


def selecionar_script(modulos: list[tuple[str, str]]) -> str | None:
    max_len = max((len(nome) for nome, _ in modulos), default=0)
    choices = []
    for nome, desc in modulos:
        bracketed = f"[{nome}]"
        titulo = f"{bracketed:<{max_len + 2}}  {desc}" if desc else bracketed
        choices.append(questionary.Choice(title=titulo, value=nome))

    return questionary.select(
        "Qual script configurar?",
        choices=choices,
        style=STYLE,
    ).ask()


def selecionar_campos(campos: list[Campo], valores: dict[str, Any]) -> list[Campo]:
    choices = []
    for campo in campos:
        valor = valores.get(campo.chave)
        ok, msg = validar_campo(campo, valor)

        if ok and (valor is not None and valor != ""):
            icone = "✅"
        elif not campo.obrigatorio and (valor is None or valor == ""):
            icone = "⚪"
        else:
            icone = "❌"

        resumo = resumo_valor(campo, valor)
        detalhe = f"  ({resumo})" if resumo else (f"  ({msg})" if msg else "  (não preenchido)")
        titulo = f"{icone} {campo.rotulo}{detalhe}"

        choices.append(questionary.Choice(title=titulo, value=campo))

    selecionados = questionary.checkbox(
        "Quais campos deseja modificar?",
        choices=choices,
        style=STYLE,
    ).ask()

    return selecionados or []


def exibir_campos(campos: list[Campo], valores: dict[str, Any]) -> None:
    max_rotulo = max((len(c.rotulo) for c in campos), default=0)
    print()
    for campo in campos:
        valor = valores.get(campo.chave)
        ok, msg = validar_campo(campo, valor)

        if ok and (valor is not None and valor != ""):
            icone = "✅"
            detalhe = resumo_valor(campo, valor)
        elif not campo.obrigatorio and (valor is None or valor == ""):
            icone = "⚪"
            detalhe = "opcional, não preenchido"
        else:
            icone = "❌"
            detalhe = msg or "não preenchido"

        rotulo_pad = campo.rotulo.ljust(max_rotulo)
        print(f"  {icone}  {rotulo_pad}  {detalhe}")
    print()


def obter_input(campo: Campo, valor_atual: Any) -> Any:
    print(f"\n{_SEPARADOR}")
    print(f"  {campo.rotulo}")
    if campo.descricao:
        print(f"  {campo.descricao}")
    print(_SEPARADOR)

    match campo.tipo:
        case "texto":
            return _input_texto(campo, valor_atual)
        case "senha":
            return _input_senha(campo)
        case "url":
            return _input_url(campo, valor_atual)
        case "caminho":
            return _input_caminho(campo, valor_atual)
        case "bool":
            return _input_bool(campo, valor_atual)
        case "int":
            return _input_int(campo, valor_atual)
        case "lista_url":
            return _input_lista_url(campo, valor_atual)
        case "dict_str_url":
            return _input_dict_str_url(campo, valor_atual)
        case "dict_str_lista_url":
            return _input_dict_str_lista_url(campo, valor_atual)
        case _:
            return _input_texto(campo, valor_atual)


def _input_texto(campo: Campo, valor_atual: Any) -> str | None:
    padrao = str(valor_atual) if valor_atual else ""
    while True:
        novo = questionary.text(
            f"{campo.rotulo}:",
            default=padrao,
            style=STYLE,
        ).ask()
        if novo is None:
            return valor_atual
        novo = novo.strip()
        ok, msg = validar_campo(campo, novo)
        if ok:
            return novo or None
        print(f"  ❌ {msg}")


def _input_senha(campo: Campo) -> str | None:
    while True:
        novo = questionary.password(
            f"{campo.rotulo}:",
            style=STYLE,
        ).ask()
        if novo is None:
            return None
        novo = novo.strip()
        ok, msg = validar_campo(campo, novo)
        if ok:
            return novo or None
        print(f"  ❌ {msg}")


def _input_url(campo: Campo, valor_atual: Any) -> str | None:
    padrao = str(valor_atual) if valor_atual else ""
    while True:
        novo = questionary.text(
            f"{campo.rotulo}:",
            default=padrao,
            style=STYLE,
        ).ask()
        if novo is None:
            return valor_atual
        novo = novo.strip()
        ok, msg = validar_campo(campo, novo)
        if ok:
            return novo or None
        print(f"  ❌ {msg}")


def _input_caminho(campo: Campo, valor_atual: Any) -> str | None:
    padrao = str(valor_atual) if valor_atual else ""
    while True:
        novo = questionary.text(
            f"{campo.rotulo}:",
            default=padrao,
            style=STYLE,
        ).ask()
        if novo is None:
            return valor_atual
        novo = novo.strip()
        if not novo and not campo.obrigatorio:
            return None
        ok, msg = validar_campo(campo, novo)
        if ok:
            return novo or None
        print(f"  ❌ {msg}")


def _input_bool(campo: Campo, valor_atual: Any) -> bool:
    padrao = bool(valor_atual) if valor_atual is not None else True
    resultado = questionary.confirm(
        f"{campo.rotulo}:",
        default=padrao,
        style=STYLE,
    ).ask()
    return resultado if resultado is not None else padrao


def _input_int(campo: Campo, valor_atual: Any) -> int | None:
    padrao = str(valor_atual) if valor_atual is not None else ""
    while True:
        novo = questionary.text(
            f"{campo.rotulo} (número inteiro):",
            default=padrao,
            style=STYLE,
        ).ask()
        if novo is None:
            return valor_atual
        novo = novo.strip()
        try:
            return int(novo)
        except ValueError:
            print("  ❌ Deve ser um número inteiro")


def _input_lista_url(campo: Campo, valor_atual: Any) -> list[str]:
    lista: list[str] = list(valor_atual) if isinstance(valor_atual, list) else []

    _ADICIONAR = "➕ Adicionar URL"
    _EDITAR = "✏️  Editar URL"
    _REMOVER = "🗑️  Remover URL"
    _CONCLUIR = "✅ Concluído"

    while True:
        print()
        if lista:
            print("  URLs atuais:")
            for i, url in enumerate(lista, 1):
                print(f"    {i}. {url}")
        else:
            print("  (lista vazia)")
        print()

        opcoes = [_ADICIONAR]
        if lista:
            opcoes += [_EDITAR, _REMOVER]
        opcoes.append(_CONCLUIR)

        acao = questionary.select("O que deseja fazer?", choices=opcoes, style=STYLE).ask()

        if acao is None or acao == _CONCLUIR:
            break

        if acao == _ADICIONAR:
            nova = _pedir_url("Nova URL")
            if nova:
                lista.append(nova)

        elif acao == _EDITAR:
            escolha = questionary.select(
                "Qual URL editar?",
                choices=[questionary.Choice(title=f"{i}. {u}", value=i - 1) for i, u in enumerate(lista, 1)],
                style=STYLE,
            ).ask()
            if escolha is not None:
                nova = _pedir_url("Nova URL", lista[escolha])
                if nova:
                    lista[escolha] = nova

        elif acao == _REMOVER:
            escolha = questionary.select(
                "Qual URL remover?",
                choices=[questionary.Choice(title=f"{i}. {u}", value=i - 1) for i, u in enumerate(lista, 1)],
                style=STYLE,
            ).ask()
            if escolha is not None:
                lista.pop(escolha)

    return lista


def _input_dict_str_url(campo: Campo, valor_atual: Any) -> dict[str, str]:
    dicio: dict[str, str] = dict(valor_atual) if isinstance(valor_atual, dict) else {}

    _ADICIONAR = "➕ Adicionar entrada"
    _EDITAR = "✏️  Editar entrada"
    _REMOVER = "🗑️  Remover entrada"
    _CONCLUIR = "✅ Concluído"

    while True:
        print()
        if dicio:
            print("  Entradas atuais:")
            for chave, url in dicio.items():
                print(f"    {chave!r} → {url}")
        else:
            print("  (dicionário vazio)")
        print()

        opcoes = [_ADICIONAR]
        if dicio:
            opcoes += [_EDITAR, _REMOVER]
        opcoes.append(_CONCLUIR)

        acao = questionary.select("O que deseja fazer?", choices=opcoes, style=STYLE).ask()

        if acao is None or acao == _CONCLUIR:
            break

        if acao == _ADICIONAR:
            nome = questionary.text("Nome da entrada (ex: Turma A):", style=STYLE).ask()
            if not nome:
                continue
            nome = nome.strip()
            url = _pedir_url(f"URL para '{nome}'")
            if url:
                dicio[nome] = url

        elif acao == _EDITAR:
            chaves = list(dicio.keys())
            escolha = questionary.select(
                "Qual entrada editar?",
                choices=[questionary.Choice(title=f"{k} → {dicio[k]}", value=k) for k in chaves],
                style=STYLE,
            ).ask()
            if escolha is not None:
                sub = questionary.select(
                    f"Editar '{escolha}':",
                    choices=["Renomear chave", "Alterar URL", "Cancelar"],
                    style=STYLE,
                ).ask()
                if sub == "Renomear chave":
                    novo_nome = questionary.text("Novo nome:", default=escolha, style=STYLE).ask()
                    if novo_nome and novo_nome.strip() and novo_nome.strip() != escolha:
                        dicio[novo_nome.strip()] = dicio.pop(escolha)
                elif sub == "Alterar URL":
                    nova = _pedir_url(f"Nova URL para '{escolha}'", dicio[escolha])
                    if nova:
                        dicio[escolha] = nova

        elif acao == _REMOVER:
            chaves = list(dicio.keys())
            escolha = questionary.select(
                "Qual entrada remover?",
                choices=[questionary.Choice(title=f"{k} → {dicio[k]}", value=k) for k in chaves],
                style=STYLE,
            ).ask()
            if escolha is not None:
                del dicio[escolha]

    return dicio


def _input_dict_str_lista_url(campo: Campo, valor_atual: Any) -> dict[str, list[str]]:
    dicio: dict[str, list[str]] = {k: list(v) for k, v in valor_atual.items()} if isinstance(valor_atual, dict) else {}

    _ADICIONAR = "➕ Adicionar mês"
    _EDITAR = "✏️  Editar URLs de um mês"
    _REMOVER = "🗑️  Remover mês"
    _CONCLUIR = "✅ Concluído"

    while True:
        print()
        if dicio:
            print("  Meses configurados:")
            for mes, urls in dicio.items():
                print(f"    {mes}: {len(urls)} URL(s)")
        else:
            print("  (nenhum mês configurado)")
        print()

        opcoes = [_ADICIONAR]
        if dicio:
            opcoes += [_EDITAR, _REMOVER]
        opcoes.append(_CONCLUIR)

        acao = questionary.select("O que deseja fazer?", choices=opcoes, style=STYLE).ask()

        if acao is None or acao == _CONCLUIR:
            break

        if acao == _ADICIONAR:
            nome = questionary.text("Nome do mês (ex: Abril 2026):", style=STYLE).ask()
            if not nome:
                continue
            nome = nome.strip()
            dicio[nome] = []
            print(f"\n  Adicionando URLs para '{nome}':")
            dicio[nome] = _editar_lista_urls_do_mes(dicio[nome])

        elif acao == _EDITAR:
            meses = list(dicio.keys())
            escolha = questionary.select(
                "Qual mês editar?",
                choices=[questionary.Choice(title=f"{m} ({len(dicio[m])} URLs)", value=m) for m in meses],
                style=STYLE,
            ).ask()
            if escolha is not None:
                print(f"\n  Editando URLs de '{escolha}':")
                dicio[escolha] = _editar_lista_urls_do_mes(dicio[escolha])

        elif acao == _REMOVER:
            meses = list(dicio.keys())
            escolha = questionary.select(
                "Qual mês remover?",
                choices=[questionary.Choice(title=f"{m} ({len(dicio[m])} URLs)", value=m) for m in meses],
                style=STYLE,
            ).ask()
            if escolha is not None:
                del dicio[escolha]

    return dicio


def _editar_lista_urls_do_mes(lista: list[str]) -> list[str]:
    _ADICIONAR = "➕ Adicionar URL"
    _EDITAR = "✏️  Editar URL"
    _REMOVER = "🗑️  Remover URL"
    _CONCLUIR = "✅ Concluído"

    while True:
        print()
        if lista:
            for i, url in enumerate(lista, 1):
                print(f"    {i}. {url}")
        else:
            print("    (lista vazia)")
        print()

        opcoes = [_ADICIONAR]
        if lista:
            opcoes += [_EDITAR, _REMOVER]
        opcoes.append(_CONCLUIR)

        acao = questionary.select("O que deseja fazer?", choices=opcoes, style=STYLE).ask()

        if acao is None or acao == _CONCLUIR:
            break

        if acao == _ADICIONAR:
            nova = _pedir_url("Nova URL")
            if nova:
                lista.append(nova)

        elif acao == _EDITAR:
            escolha = questionary.select(
                "Qual URL editar?",
                choices=[questionary.Choice(title=f"{i}. {u}", value=i - 1) for i, u in enumerate(lista, 1)],
                style=STYLE,
            ).ask()
            if escolha is not None:
                nova = _pedir_url("Nova URL", lista[escolha])
                if nova:
                    lista[escolha] = nova

        elif acao == _REMOVER:
            escolha = questionary.select(
                "Qual URL remover?",
                choices=[questionary.Choice(title=f"{i}. {u}", value=i - 1) for i, u in enumerate(lista, 1)],
                style=STYLE,
            ).ask()
            if escolha is not None:
                lista.pop(escolha)

    return lista


def _pedir_url(rotulo: str, padrao: str = "") -> str | None:
    while True:
        novo = questionary.text(f"{rotulo}:", default=padrao, style=STYLE).ask()
        if novo is None:
            return None
        novo = novo.strip()
        if not novo:
            return None
        if re.match(r"^https?://", novo):
            return novo
        print("  ❌ Deve ser uma URL válida começando com http:// ou https://")
