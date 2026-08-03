import pytest

from scripthub.scripts.torpedo.main import carregar_conteudo, encontrar_imagem
from scripthub.services.erros import ErroConfiguracao

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


def test_carregar_conteudo_sem_titulo_levanta_erro_configuracao(tmp_path):
    md = tmp_path / "post.md"
    md.write_text("Sem título aqui.\n\nApenas parágrafos.", encoding="utf-8")

    with pytest.raises(ErroConfiguracao, match="título"):
        carregar_conteudo(md)


# ── encontrar_imagem ──────────────────────────────────────────────────────────


def test_encontrar_imagem_override_existente(tmp_path):
    img = tmp_path / "foto.png"
    img.write_bytes(b"PNG")

    caminho = encontrar_imagem(tmp_path, override=str(img))

    assert caminho == str(img)


def test_encontrar_imagem_sem_override_retorna_primeira_imagem_da_pasta(tmp_path):
    img = tmp_path / "banner.jpg"
    img.write_bytes(b"JPG")

    caminho = encontrar_imagem(tmp_path, override=None)

    assert caminho == str(img)
