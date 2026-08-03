import pytest

from scripthub.scripts.torpedo.main import (
    _injetar_cookies,
    _md_para_html,
    carregar_conteudo,
    encontrar_imagem,
)
from scripthub.services.erros import ErroConfiguracao
from scripthub.services.moodle import MoodleSessao

# ── carregar_conteudo ─────────────────────────────────────────────────────────


def test_carregar_conteudo_arquivo_inexistente_levanta_erro_configuracao(tmp_path):
    with pytest.raises(ErroConfiguracao):
        carregar_conteudo(tmp_path / "nao_existe.md")


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


def test_encontrar_imagem_override_inexistente_levanta_erro_configuracao(tmp_path):
    with pytest.raises(ErroConfiguracao):
        encontrar_imagem(tmp_path, override=str(tmp_path / "nao_existe.png"))


def test_encontrar_imagem_sem_imagens_retorna_none(tmp_path):
    resultado = encontrar_imagem(tmp_path, override=None)

    assert resultado is None


# ── _injetar_cookies ──────────────────────────────────────────────────────────


def test_injetar_cookies_injeta_cookies_no_contexto(mocker):
    mock_session = mocker.MagicMock()
    mock_cookie = mocker.MagicMock()
    mock_cookie.name = "MoodleSession"
    mock_cookie.value = "abc123"
    mock_cookie.domain = "moodle.example.com"
    mock_cookie.path = "/"
    mock_session.cookies = [mock_cookie]
    sessao = MoodleSessao("https://moodle.example.com/login/index.php", "u", "p", _session=mock_session)
    mock_contexto = mocker.MagicMock()

    _injetar_cookies(mock_contexto, sessao)

    mock_contexto.add_cookies.assert_called_once_with(
        [{"name": "MoodleSession", "value": "abc123", "domain": "moodle.example.com", "path": "/"}]
    )


def test_injetar_cookies_sem_cookies_nao_chama_add_cookies(mocker):
    mock_session = mocker.MagicMock()
    mock_session.cookies = []
    sessao = MoodleSessao("https://moodle.example.com/login/index.php", "u", "p", _session=mock_session)
    mock_contexto = mocker.MagicMock()

    _injetar_cookies(mock_contexto, sessao)

    mock_contexto.add_cookies.assert_not_called()
