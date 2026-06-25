import pytest

from scripthub.scripts.torpedo_de_forum.main import (
    _md_para_html,
    carregar_conteudo,
    encontrar_imagem,
)


# ── carregar_conteudo ─────────────────────────────────────────────────────────


def test_carregar_conteudo_retorna_titulo_e_html(tmp_path):
    md = tmp_path / "post.md"
    md.write_text("# Semana 10\n\nConteúdo do post.", encoding="utf-8")

    titulo, html = carregar_conteudo(md)

    assert titulo == "Semana 10"
    assert "Conteúdo do post." in html


def test_carregar_conteudo_sem_body_retorna_html_vazio(tmp_path):
    md = tmp_path / "post.md"
    md.write_text("# Só o Título\n", encoding="utf-8")

    titulo, html = carregar_conteudo(md)

    assert titulo == "Só o Título"
    assert html == ""


def test_carregar_conteudo_arquivo_inexistente_levanta_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        carregar_conteudo(tmp_path / "nao_existe.md")


def test_carregar_conteudo_sem_titulo_levanta_value_error(tmp_path):
    md = tmp_path / "post.md"
    md.write_text("Sem título aqui.\n\nApenas parágrafos.", encoding="utf-8")

    with pytest.raises(ValueError, match="título"):
        carregar_conteudo(md)


# ── _md_para_html ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "md,tag_esperada",
    [
        ("**negrito**", "<strong>negrito</strong>"),
        ("*italico*", "<em>italico</em>"),
        ("## Título H2", "<h2>Título H2</h2>"),
        ("### Título H3", "<h3>Título H3</h3>"),
        ("[link](https://x.com)", '<a href="https://x.com">link</a>'),
    ],
)
def test_md_para_html_elementos_inline(md, tag_esperada):
    assert tag_esperada in _md_para_html(md)


def test_md_para_html_lista_gera_ul_e_li():
    resultado = _md_para_html("- item1\n- item2")

    assert "<ul>" in resultado
    assert "<li>item1</li>" in resultado
    assert "<li>item2</li>" in resultado


def test_md_para_html_paragrafo_envolve_texto_simples():
    resultado = _md_para_html("Texto sem marcação")

    assert "<p>Texto sem marcação</p>" in resultado


def test_md_para_html_nao_envolve_bloco_html_em_paragrafo():
    resultado = _md_para_html("<h2>Título</h2>")

    assert "<p><h2>" not in resultado


# ── encontrar_imagem ──────────────────────────────────────────────────────────


def test_encontrar_imagem_override_existente(tmp_path):
    img = tmp_path / "foto.png"
    img.write_bytes(b"PNG")

    caminho = encontrar_imagem(tmp_path, override=str(img))

    assert caminho == str(img)


def test_encontrar_imagem_override_inexistente_levanta_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        encontrar_imagem(tmp_path, override=str(tmp_path / "nao_existe.png"))


def test_encontrar_imagem_sem_override_retorna_primeira_imagem_da_pasta(tmp_path):
    img = tmp_path / "banner.jpg"
    img.write_bytes(b"JPG")

    caminho = encontrar_imagem(tmp_path, override=None)

    assert caminho == str(img)


def test_encontrar_imagem_sem_imagens_retorna_none(tmp_path):
    resultado = encontrar_imagem(tmp_path, override=None)

    assert resultado is None
