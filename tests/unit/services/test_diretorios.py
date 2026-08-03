from types import SimpleNamespace

from scripthub.services import diretorios


def _fake_platformdirs(tmp_path, mocker):
    fake = SimpleNamespace(
        user_config_dir=str(tmp_path / "config"),
        user_data_dir=str(tmp_path / "data"),
        user_state_dir=str(tmp_path / "state"),
        user_cache_dir=str(tmp_path / "cache"),
    )
    mocker.patch.object(diretorios.platformdirs, "PlatformDirs", return_value=fake)
    return fake


def test_caminho_config_junta_perfil_e_dominio(tmp_path, mocker):
    _fake_platformdirs(tmp_path, mocker)

    resultado = diretorios.caminho_config("default", "frequencias")

    assert resultado == tmp_path / "config" / "default" / "frequencias"


def test_caminho_dados_junta_perfil_dominio_e_subpasta_dados(tmp_path, mocker):
    _fake_platformdirs(tmp_path, mocker)

    resultado = diretorios.caminho_dados("default", "frequencias")

    assert resultado == tmp_path / "data" / "default" / "frequencias" / "dados"


def test_caminho_cache_junta_perfil_dominio_e_script(tmp_path, mocker):
    """`script` é obrigatório: cache é usado por artefatos transitórios de um
    script específico (ex. `auditar`/`compilar` dentro do domínio `frequencias`)
    — sem esse terceiro segmento, dois scripts do mesmo domínio colidem no
    mesmo diretório de cache (visto na PR #124, achado #2 da revisão)."""
    _fake_platformdirs(tmp_path, mocker)

    resultado = diretorios.caminho_cache("default", "frequencias", "auditar")

    assert resultado == tmp_path / "cache" / "default" / "frequencias" / "auditar"


def test_caminho_log_e_dividido_so_por_perfil(tmp_path, mocker):
    _fake_platformdirs(tmp_path, mocker)

    resultado = diretorios.caminho_log("equipe-noturna")

    assert resultado == tmp_path / "state" / "equipe-noturna"


def test_caminho_arquivo_perfil_fica_na_raiz_do_config_fora_da_arvore_de_perfil(tmp_path, mocker):
    _fake_platformdirs(tmp_path, mocker)

    resultado = diretorios.caminho_arquivo_perfil()

    assert resultado == tmp_path / "config" / "Profile"


def test_platformdirs_e_chamado_com_appname_e_appauthor_corretos(tmp_path, mocker):
    fake = _fake_platformdirs(tmp_path, mocker)

    diretorios.caminho_config("default", "frequencias")

    diretorios.platformdirs.PlatformDirs.assert_called_with(appname="scripthub", appauthor="apontiacademy")
    assert fake.user_config_dir
