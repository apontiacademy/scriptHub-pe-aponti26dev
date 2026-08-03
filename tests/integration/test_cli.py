import scripthub.cli as cli_module
from scripthub.services import perfil as perfil_module


def test_set_profile_persiste_e_loga_ok(mocker, tmp_path):
    mocker.patch("scripthub.services.perfil.diretorios.caminho_arquivo_perfil", return_value=tmp_path / "Profile")
    mock_log = mocker.patch("scripthub.cli.log")

    cli_module.set_profile("equipe-noturna")

    assert perfil_module.perfil_persistido() == "equipe-noturna"
    mock_log.ok.assert_called_once()


def test_unset_profile_quando_nao_default_remove_e_loga_ok(mocker, tmp_path):
    mocker.patch("scripthub.services.perfil.diretorios.caminho_arquivo_perfil", return_value=tmp_path / "Profile")
    mock_log = mocker.patch("scripthub.cli.log")
    cli_module.set_profile("equipe-noturna")
    mock_log.reset_mock()

    cli_module.unset_profile()

    assert perfil_module.perfil_persistido() == perfil_module.PADRAO
    mock_log.ok.assert_called_once()
    mock_log.aviso.assert_not_called()
