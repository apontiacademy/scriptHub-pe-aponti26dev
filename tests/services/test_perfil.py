import pytest

from scripthub.services import perfil
from scripthub.services.erros import ErroConfiguracao, ErroUsoCLI


@pytest.fixture(autouse=True)
def _arquivo_perfil(tmp_path, mocker):
    caminho = tmp_path / "config" / "Profile"
    mocker.patch("scripthub.services.perfil.diretorios.caminho_arquivo_perfil", return_value=caminho)
    perfil.definir_override(None)
    yield caminho
    perfil.definir_override(None)


def test_perfil_persistido_e_default_quando_nada_foi_definido(_arquivo_perfil):
    assert perfil.perfil_persistido() == "default"


def test_definir_perfil_persiste_e_perfil_persistido_reflete(_arquivo_perfil):
    perfil.definir_perfil("equipe-noturna")

    assert perfil.perfil_persistido() == "equipe-noturna"
    assert _arquivo_perfil.read_text(encoding="utf-8").strip() == "equipe-noturna"


def test_remover_perfil_apaga_arquivo_e_volta_para_default(_arquivo_perfil):
    perfil.definir_perfil("equipe-noturna")

    perfil.remover_perfil()

    assert perfil.perfil_persistido() == "default"
    assert not _arquivo_perfil.exists()


def test_remover_perfil_quando_ja_e_default_e_no_op(_arquivo_perfil):
    perfil.remover_perfil()  # não deve levantar, mesmo sem arquivo existente

    assert perfil.perfil_persistido() == "default"


def test_resolver_perfil_usa_persistido_sem_override(_arquivo_perfil):
    perfil.definir_perfil("equipe-noturna")

    assert perfil.resolver_perfil() == "equipe-noturna"


def test_resolver_perfil_usa_override_sem_persistir(_arquivo_perfil):
    perfil.definir_perfil("equipe-noturna")

    perfil.definir_override("equipe-diurna")

    assert perfil.resolver_perfil() == "equipe-diurna"
    assert perfil.perfil_persistido() == "equipe-noturna"  # não foi alterado


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


def test_perfil_persistido_levanta_erro_configuracao_para_conteudo_invalido_editado_manualmente(_arquivo_perfil):
    """A validação de nome só rodava na escrita (definir_perfil/definir_override),
    não na leitura — um arquivo-marcador editado manualmente com conteúdo inválido
    era usado sem validação. perfil_persistido() deve validar também na leitura."""
    _arquivo_perfil.parent.mkdir(parents=True, exist_ok=True)
    _arquivo_perfil.write_text("a/b", encoding="utf-8")

    with pytest.raises(ErroConfiguracao):
        perfil.perfil_persistido()
