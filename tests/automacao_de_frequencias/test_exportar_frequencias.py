from contextlib import contextmanager
from unittest.mock import MagicMock, call, patch

from automacao_de_frequencias.exportar_frequencias import (
    exportar_frequencia,
    realizar_login,
)


def _make_page_mock(ghost_session=False):
    """Retorna um mock de page configurado para o cenário indicado."""
    page = MagicMock()

    ghost_locator = MagicMock()
    if ghost_session:
        ghost_locator.first.wait_for.return_value = None
    else:
        ghost_locator.first.wait_for.side_effect = Exception("timeout")

    username_locator = MagicMock()
    password_locator = MagicMock()
    loginbtn_locator = MagicMock()

    def locator_side_effect(selector):
        if "logininsidebaric" in selector or "Sair" in selector:
            return ghost_locator
        if selector == "#username":
            return username_locator
        if selector == "#password":
            return password_locator
        if selector == "#loginbtn":
            return loginbtn_locator
        return MagicMock()

    page.locator.side_effect = locator_side_effect
    return page, username_locator, password_locator, loginbtn_locator


def test_realizar_login_fluxo_normal():
    page, username_loc, password_loc, loginbtn_loc = _make_page_mock()

    realizar_login(page, "https://example.com/login", "user", "pass")

    page.goto.assert_called_with("https://example.com/login")
    username_loc.fill.assert_called_with("user")
    password_loc.fill.assert_called_with("pass")
    loginbtn_loc.click.assert_called()


def test_realizar_login_com_sessao_fantasma():
    page, _, _, _ = _make_page_mock(ghost_session=True)

    realizar_login(page, "https://example.com/login", "user", "pass")

    # Deve ir à URL de login duas vezes (uma para limpar sessão, outra para logar)
    assert page.goto.call_count == 2
    assert page.goto.call_args_list[0] == call("https://example.com/login")
    assert page.goto.call_args_list[1] == call("https://example.com/login")


def _make_page_com_download(url_atual="https://example.com/freq?id=1"):
    """Retorna page mock configurado para fluxo de download."""
    page = MagicMock()
    page.url = url_atual

    download_mock = MagicMock()

    @contextmanager
    def mock_expect_download(**kwargs):
        yield download_mock

    page.expect_download = mock_expect_download
    page.get_by_label.return_value.is_checked.return_value = False

    return page, download_mock


def test_exportar_frequencia_sucesso(tmp_path):
    page, download_mock = _make_page_com_download()

    exportar_frequencia(
        page,
        "https://example.com/freq?id=1",
        "Turma A",
        tmp_path,
        "https://example.com/login",
        "user",
        "pass",
    )

    # Checkbox foi marcado
    page.get_by_label.return_value.check.assert_called_once()
    # Botão OK foi clicado
    page.get_by_role.assert_called_with("button", name="OK")
    page.get_by_role.return_value.click.assert_called_once()
    # Arquivo salvo com nome da turma
    download_mock.value.save_as.assert_called_with(str(tmp_path / "Turma A.xlsx"))


def test_exportar_frequencia_ja_marcado_nao_marca_novamente(tmp_path):
    page, download_mock = _make_page_com_download()
    page.get_by_label.return_value.is_checked.return_value = True

    exportar_frequencia(
        page,
        "https://example.com/freq?id=1",
        "Turma A",
        tmp_path,
        "https://example.com/login",
        "user",
        "pass",
    )

    page.get_by_label.return_value.check.assert_not_called()


def test_exportar_frequencia_redireciona_para_login(tmp_path):
    page, download_mock = _make_page_com_download(url_atual="https://example.com/login")

    with patch("automacao_de_frequencias.exportar_frequencias.realizar_login") as mock_login:
        exportar_frequencia(
            page,
            "https://example.com/freq?id=1",
            "Turma A",
            tmp_path,
            "https://example.com/login",
            "user",
            "pass",
        )

        mock_login.assert_called_once_with(page, "https://example.com/login", "user", "pass")
