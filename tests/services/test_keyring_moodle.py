import pytest

from scripthub.services import keyring_moodle
from scripthub.services.erros import ErroConfiguracao


def test_definir_e_obter_senha_moodle_por_dominio(mocker):
    mock_keyring = mocker.patch("scripthub.services.keyring_moodle.keyring")

    keyring_moodle.definir_senha_moodle("frequencias", "default", "minhasenha")

    mock_keyring.set_password.assert_called_once_with("scripthub-default-frequencias", "moodle_senha", "minhasenha")


def test_obter_senha_moodle_delega_para_keyring_get_password(mocker):
    mock_keyring = mocker.patch("scripthub.services.keyring_moodle.keyring")
    mock_keyring.get_password.return_value = "minhasenha"

    resultado = keyring_moodle.obter_senha_moodle("torpedo", "default")

    mock_keyring.get_password.assert_called_once_with("scripthub-default-torpedo", "moodle_senha")
    assert resultado == "minhasenha"


def test_obter_senha_moodle_retorna_none_quando_nao_existe(mocker):
    mock_keyring = mocker.patch("scripthub.services.keyring_moodle.keyring")
    mock_keyring.get_password.return_value = None

    assert keyring_moodle.obter_senha_moodle("torpedo", "default") is None


def test_remover_senha_moodle_delega_para_delete_password(mocker):
    mock_keyring = mocker.patch("scripthub.services.keyring_moodle.keyring")

    keyring_moodle.remover_senha_moodle("softskills", "default")

    mock_keyring.delete_password.assert_called_once_with("scripthub-default-softskills", "moodle_senha")


def test_remover_senha_moodle_inexistente_nao_levanta(mocker):
    mock_keyring = mocker.patch("scripthub.services.keyring_moodle.keyring")
    mock_keyring.errors.PasswordDeleteError = Exception
    mock_keyring.delete_password.side_effect = mock_keyring.errors.PasswordDeleteError()

    keyring_moodle.remover_senha_moodle("softskills", "default")  # não deve levantar

    mock_keyring.delete_password.assert_called_once()


def test_dominios_diferentes_usam_servicos_de_keyring_diferentes(mocker):
    mock_keyring = mocker.patch("scripthub.services.keyring_moodle.keyring")

    keyring_moodle.definir_senha_moodle("frequencias", "default", "a")
    keyring_moodle.definir_senha_moodle("torpedo", "default", "b")

    servicos = {c.args[0] for c in mock_keyring.set_password.call_args_list}
    assert servicos == {"scripthub-default-frequencias", "scripthub-default-torpedo"}


def test_obter_senha_moodle_com_keyring_indisponivel_levanta_erro_configuracao(mocker):
    mock_keyring = mocker.patch("scripthub.services.keyring_moodle.keyring")
    mock_keyring.errors.KeyringError = Exception
    mock_keyring.get_password.side_effect = mock_keyring.errors.KeyringError("backend ausente")

    with pytest.raises(ErroConfiguracao):
        keyring_moodle.obter_senha_moodle("frequencias", "default")


def test_definir_senha_moodle_com_keyring_indisponivel_levanta_erro_configuracao(mocker):
    mock_keyring = mocker.patch("scripthub.services.keyring_moodle.keyring")
    mock_keyring.errors.KeyringError = Exception
    mock_keyring.set_password.side_effect = mock_keyring.errors.KeyringError("keychain bloqueado")

    with pytest.raises(ErroConfiguracao):
        keyring_moodle.definir_senha_moodle("frequencias", "default", "minhasenha")


def test_perfis_diferentes_usam_servicos_de_keyring_diferentes(mocker):
    mock_keyring = mocker.patch("scripthub.services.keyring_moodle.keyring")

    keyring_moodle.definir_senha_moodle("frequencias", "equipe-diurna", "a")
    keyring_moodle.definir_senha_moodle("frequencias", "equipe-noturna", "b")

    servicos = {c.args[0] for c in mock_keyring.set_password.call_args_list}
    assert servicos == {"scripthub-equipe-diurna-frequencias", "scripthub-equipe-noturna-frequencias"}
