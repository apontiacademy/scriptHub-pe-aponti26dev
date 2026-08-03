from scripthub.services.google.drive import GoogleDriveClient

_PATCH = "scripthub.services.google.drive"
_SCOPES = ["https://www.googleapis.com/auth/drive"]


def test_init_autentica_com_service_account(mocker, tmp_path):
    creds = tmp_path / "creds.json"
    creds.write_text("{}")
    mock_creds = mocker.patch(f"{_PATCH}.Credentials.from_service_account_file")
    mocker.patch(f"{_PATCH}.build")

    GoogleDriveClient(creds, _SCOPES)

    mock_creds.assert_called_once_with(str(creds), scopes=_SCOPES)


def test_init_builda_servico_drive(mocker, tmp_path):
    creds = tmp_path / "creds.json"
    creds.write_text("{}")
    mocker.patch(f"{_PATCH}.Credentials.from_service_account_file")
    mock_build = mocker.patch(f"{_PATCH}.build")

    GoogleDriveClient(creds, _SCOPES)

    mock_build.assert_called_once()
    assert mock_build.call_args[0][0] == "drive"
