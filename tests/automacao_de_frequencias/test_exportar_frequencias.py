from unittest.mock import MagicMock, call

from automacao_de_frequencias.exportar_frequencias import realizar_login


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
