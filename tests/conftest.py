import pytest


@pytest.fixture
def moodle_env(tmp_path):
    """Escreve .env com credenciais Moodle válidas em tmp_path."""
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    return tmp_path
