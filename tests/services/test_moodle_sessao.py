from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripthub.services.moodle.sessao import MoodleSessao

_LOGIN_URL = "https://moodle.example.com/login/index.php"
_HOME_URL = "https://moodle.example.com/my/"


def _resp(text="", url=_HOME_URL, status_code=200, content=b""):
    r = MagicMock()
    r.text = text
    r.url = url
    r.status_code = status_code
    r.content = content
    r.raise_for_status = MagicMock()
    return r


def _sessao(session=None):
    return MoodleSessao(_LOGIN_URL, "user", "pass", _session=session or MagicMock())


# ── login ─────────────────────────────────────────────────────────────────────


def test_login_faz_get_na_url_de_login():
    mock = MagicMock()
    mock.get.return_value = _resp(text='<input name="logintoken" value="tok1">')
    mock.post.return_value = _resp(url=_HOME_URL)
    s = MoodleSessao(_LOGIN_URL, "user", "pass", _session=mock)

    s.login()

    mock.get.assert_called_once_with(_LOGIN_URL)


def test_login_posta_credenciais_e_token_extraido():
    mock = MagicMock()
    mock.get.return_value = _resp(text='<input name="logintoken" value="tok42">')
    mock.post.return_value = _resp(url=_HOME_URL)
    s = MoodleSessao(_LOGIN_URL, "myuser", "mypass", _session=mock)

    s.login()

    _, kwargs = mock.post.call_args
    data = kwargs["data"]
    assert data["username"] == "myuser"
    assert data["password"] == "mypass"
    assert data["logintoken"] == "tok42"


def test_login_sem_logintoken_posta_com_token_none():
    mock = MagicMock()
    mock.get.return_value = _resp(text="<html>sem token</html>")
    mock.post.return_value = _resp(url=_HOME_URL)
    s = MoodleSessao(_LOGIN_URL, "u", "p", _session=mock)

    s.login()  # não deve lançar

    _, kwargs = mock.post.call_args
    assert kwargs["data"]["logintoken"] is None


def test_login_levanta_runtime_error_quando_redireciona_para_login():
    mock = MagicMock()
    mock.get.return_value = _resp(text='<input name="logintoken" value="t">')
    mock.post.return_value = _resp(url=_LOGIN_URL)  # ainda no login → falha
    s = MoodleSessao(_LOGIN_URL, "u", "p", _session=mock)

    with pytest.raises(RuntimeError, match="[Ll]ogin"):
        s.login()


# ── get / post ────────────────────────────────────────────────────────────────


def test_get_delega_para_session():
    mock = MagicMock()
    s = _sessao(mock)

    s.get("https://moodle.example.com/page")

    mock.get.assert_called_once_with("https://moodle.example.com/page")


def test_post_delega_para_session():
    mock = MagicMock()
    s = _sessao(mock)

    s.post("https://moodle.example.com/action", data={"key": "val"})

    mock.post.assert_called_once_with("https://moodle.example.com/action", data={"key": "val"})


# ── baixar ────────────────────────────────────────────────────────────────────


def test_baixar_get_salva_bytes_no_destino(tmp_path):
    mock = MagicMock()
    mock.get.return_value = _resp(url="https://moodle.example.com/file.csv", content=b"col1,col2\n1,2")
    s = _sessao(mock)
    destino = tmp_path / "saida.csv"

    s.baixar("https://moodle.example.com/file.csv", destino)

    assert destino.exists()
    assert destino.read_bytes() == b"col1,col2\n1,2"


def test_baixar_post_usa_method_post_e_data(tmp_path):
    mock = MagicMock()
    mock.post.return_value = _resp(url="https://moodle.example.com/report", content=b"data")
    s = _sessao(mock)
    destino = tmp_path / "relatorio.csv"

    s.baixar("https://moodle.example.com/report", destino, method="post", data={"sesskey": "sk1"})

    mock.post.assert_called_once_with("https://moodle.example.com/report", data={"sesskey": "sk1"})
    assert destino.exists()


def test_baixar_cria_diretorios_pais(tmp_path):
    mock = MagicMock()
    mock.get.return_value = _resp(url="https://moodle.example.com/file.xlsx", content=b"xlsx")
    s = _sessao(mock)
    destino = tmp_path / "subdir" / "outro" / "arquivo.xlsx"

    s.baixar("https://moodle.example.com/file.xlsx", destino)

    assert destino.exists()


def test_baixar_levanta_runtime_error_quando_redireciona_para_login(tmp_path):
    mock = MagicMock()
    mock.get.return_value = _resp(url="https://moodle.example.com/login/index.php", content=b"<html>login</html>")
    s = _sessao(mock)

    with pytest.raises(RuntimeError, match="[Ss]ess"):
        s.baixar("https://moodle.example.com/protected", tmp_path / "f.csv")
