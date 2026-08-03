from unittest.mock import MagicMock

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


def test_baixar_retorna_a_resposta(tmp_path):
    mock = MagicMock()
    resp = _resp(url="https://moodle.example.com/file.csv", content=b"col1,col2\n1,2")
    mock.get.return_value = resp
    s = _sessao(mock)

    resultado = s.baixar("https://moodle.example.com/file.csv", tmp_path / "f.csv")

    assert resultado is resp


def test_baixar_get_com_data_envia_como_query_params(tmp_path):
    mock = MagicMock()
    mock.get.return_value = _resp(url="https://moodle.example.com/report", content=b"data")
    s = _sessao(mock)

    s.baixar(
        "https://moodle.example.com/report",
        tmp_path / "relatorio.csv",
        data={"sesskey": "sk1", "download": "csv"},
    )

    mock.get.assert_called_once_with("https://moodle.example.com/report", params={"sesskey": "sk1", "download": "csv"})
