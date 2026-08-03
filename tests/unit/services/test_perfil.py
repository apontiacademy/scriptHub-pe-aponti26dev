import pytest

from scripthub.services import perfil
from scripthub.services.erros import ErroUsoCLI


@pytest.fixture(autouse=True)
def _arquivo_perfil(tmp_path, mocker):
    caminho = tmp_path / "config" / "Profile"
    mocker.patch("scripthub.services.perfil.diretorios.caminho_arquivo_perfil", return_value=caminho)
    perfil.definir_override(None)
    yield caminho
    perfil.definir_override(None)


def test_perfil_persistido_e_default_quando_nada_foi_definido(_arquivo_perfil):
    assert perfil.perfil_persistido() == "default"


def test_remover_perfil_quando_ja_e_default_e_no_op(_arquivo_perfil):
    perfil.remover_perfil()  # não deve levantar, mesmo sem arquivo existente

    assert perfil.perfil_persistido() == "default"


@pytest.mark.parametrize("nome_invalido", ["a/b", "a\\b", ".", ".."])
def test_definir_perfil_rejeita_nome_invalido(_arquivo_perfil, nome_invalido):
    with pytest.raises(ErroUsoCLI):
        perfil.definir_perfil(nome_invalido)


@pytest.mark.parametrize("nome_invalido", ["a/b", "a\\b", ".", ".."])
def test_definir_override_rejeita_nome_invalido(_arquivo_perfil, nome_invalido):
    with pytest.raises(ErroUsoCLI):
        perfil.definir_override(nome_invalido)


@pytest.mark.parametrize("nome_reservado", ["Profile", "profile", "PROFILE"])
def test_definir_perfil_rejeita_nome_reservado_profile(_arquivo_perfil, nome_reservado):
    """Regressão: 'Profile' é o nome do arquivo-marcador (caminho_arquivo_perfil()
    → user_config_dir/Profile) — um profile com esse nome faria
    caminho_config('Profile', dominio) colidir com esse arquivo no mesmo
    segmento de caminho. Bloqueado case-insensitive por sistemas de arquivos
    case-insensitive (macOS/Windows)."""
    with pytest.raises(ErroUsoCLI):
        perfil.definir_perfil(nome_reservado)
