import re
from typing import Any

from .campo import Campo


def validar_campo(campo: Campo, valor: Any) -> tuple[bool, str]:
    """Retorna (válido, mensagem_de_erro)."""
    vazio = valor is None or (isinstance(valor, str) and not valor.strip())

    if vazio:
        if campo.obrigatorio:
            return False, "Campo obrigatório não preenchido"
        return True, ""

    match campo.tipo:
        case "texto" | "senha":
            return True, ""

        case "url":
            if re.match(r"^https?://", str(valor)):
                return True, ""
            return False, "Deve ser uma URL válida começando com http:// ou https://"

        case "caminho":
            return True, ""

        case "bool":
            if isinstance(valor, bool):
                return True, ""
            return False, "Deve ser verdadeiro ou falso"

        case "int":
            try:
                int(valor)
                return True, ""
            except (ValueError, TypeError):
                return False, "Deve ser um número inteiro"

        case "lista_url":
            if not isinstance(valor, list) or len(valor) == 0:
                return False, "Deve conter pelo menos uma URL"
            invalidas = [v for v in valor if not re.match(r"^https?://", str(v))]
            if invalidas:
                return False, f"URL(s) inválida(s): {', '.join(str(u) for u in invalidas[:2])}"
            return True, ""

        case "dict_str_url":
            if not isinstance(valor, dict) or len(valor) == 0:
                return False, "Deve conter pelo menos um par chave → URL"
            invalidas = {k: v for k, v in valor.items() if not re.match(r"^https?://", str(v))}
            if invalidas:
                chaves = ", ".join(list(invalidas.keys())[:2])
                return False, f"URL(s) inválida(s) em: {chaves}"
            return True, ""

        case "dict_str_lista_url":
            if not isinstance(valor, dict) or len(valor) == 0:
                return False, "Deve conter pelo menos um mês com URLs"
            for chave, urls in valor.items():
                if not isinstance(urls, list) or len(urls) == 0:
                    return False, f"'{chave}' deve ter pelo menos uma URL"
                for url in urls:
                    if not re.match(r"^https?://", str(url)):
                        return False, f"URL inválida em '{chave}': {url}"
            return True, ""

        case _:
            return True, ""


def resumo_valor(campo: Campo, valor: Any) -> str:
    """Retorna uma string curta para exibição no checkbox de seleção."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return ""

    match campo.tipo:
        case "senha":
            return "••••••"
        case "lista_url":
            if isinstance(valor, list):
                return f"{len(valor)} URL(s)"
            return str(valor)
        case "dict_str_url":
            if isinstance(valor, dict):
                return f"{len(valor)} entr."
            return str(valor)
        case "dict_str_lista_url":
            if isinstance(valor, dict):
                total = sum(len(v) for v in valor.values())
                return f"{len(valor)} mês/meses, {total} URL(s)"
            return str(valor)
        case "bool":
            return "verdadeiro" if valor else "falso"
        case _:
            texto = str(valor)
            return texto if len(texto) <= 50 else texto[:47] + "..."
