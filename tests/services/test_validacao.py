import pytest

from scripthub.services.config.campo import Campo
from scripthub.services.config.validacao import resumo_valor, validar_campo


def _campo(tipo, obrigatorio=True):
    return Campo(
        chave="k",
        rotulo="r",
        tipo=tipo,
        origem="settings",
        json_chaves=["k"],
        obrigatorio=obrigatorio,
    )


# ── validar_campo ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "tipo,valor,valido",
    [
        ("texto", "qualquer coisa", True),
        ("senha", "s3cr3t", True),
        ("url", "https://exemplo.com", True),
        ("url", "http://exemplo.com", True),
        ("url", "sem-protocolo.com", False),
        ("url", "ftp://invalido.com", False),
        ("caminho", "/home/user/arquivo.txt", True),
        ("bool", True, True),
        ("bool", False, True),
        ("bool", "sim", False),
        ("int", 42, True),
        ("int", "abc", False),
        ("lista_url", ["https://a.com"], True),
        ("lista_url", ["https://a.com", "https://b.com"], True),
        ("lista_url", [], False),
        ("lista_url", ["nao-url"], False),
        ("dict_str_url", {"turma": "https://a.com"}, True),
        ("dict_str_url", {}, False),
        ("dict_str_url", {"turma": "sem-protocolo"}, False),
        ("dict_str_lista_url", {"jan": ["https://a.com"]}, True),
        ("dict_str_lista_url", {"jan": []}, False),
        ("dict_str_lista_url", {"jan": ["nao-url"]}, False),
        ("dict_str_lista_url", {}, False),
    ],
)
def test_validar_campo_retorna_valido_esperado(tipo, valor, valido):
    ok, _ = validar_campo(_campo(tipo), valor)

    assert ok is valido


def test_validar_campo_obrigatorio_vazio_retorna_invalido():
    ok, msg = validar_campo(_campo("texto", obrigatorio=True), "")

    assert ok is False
    assert msg != ""


def test_validar_campo_opcional_vazio_retorna_valido():
    ok, msg = validar_campo(_campo("texto", obrigatorio=False), "")

    assert ok is True
    assert msg == ""


def test_validar_campo_none_obrigatorio_retorna_invalido():
    ok, _ = validar_campo(_campo("url", obrigatorio=True), None)

    assert ok is False


def test_validar_campo_invalido_retorna_mensagem_nao_vazia():
    ok, msg = validar_campo(_campo("url"), "sem-protocolo")

    assert ok is False
    assert len(msg) > 0


def test_validar_campo_lista_url_url_invalida_menciona_url_na_mensagem():
    _, msg = validar_campo(_campo("lista_url"), ["nao-e-url"])

    assert "nao-e-url" in msg


# ── resumo_valor ──────────────────────────────────────────────────────────────


def test_resumo_valor_senha_retorna_mascara():
    resultado = resumo_valor(_campo("senha"), "minha-senha-secreta")

    assert resultado == "••••••"


def test_resumo_valor_lista_url_exibe_contagem():
    resultado = resumo_valor(_campo("lista_url"), ["https://a.com", "https://b.com"])

    assert "2" in resultado


def test_resumo_valor_dict_str_url_exibe_contagem_de_entradas():
    resultado = resumo_valor(_campo("dict_str_url"), {"t1": "https://a.com", "t2": "https://b.com"})

    assert "2" in resultado


def test_resumo_valor_bool_true_retorna_texto_verdadeiro():
    resultado = resumo_valor(_campo("bool"), True)

    assert resultado == "verdadeiro"


def test_resumo_valor_bool_false_retorna_texto_falso():
    resultado = resumo_valor(_campo("bool"), False)

    assert resultado == "falso"


def test_resumo_valor_texto_longo_truncado_em_50_chars():
    texto_longo = "a" * 60

    resultado = resumo_valor(_campo("texto"), texto_longo)

    assert len(resultado) <= 53  # 47 + "..."
    assert resultado.endswith("...")


def test_resumo_valor_texto_curto_nao_truncado():
    texto_curto = "texto curto"

    resultado = resumo_valor(_campo("texto"), texto_curto)

    assert resultado == "texto curto"


def test_resumo_valor_none_retorna_vazio():
    resultado = resumo_valor(_campo("texto"), None)

    assert resultado == ""
