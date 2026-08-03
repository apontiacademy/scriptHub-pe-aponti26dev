from scripthub.scripts.relatorios.compilar.compilar_pdfs import _carregar_relatorios

_PATCH = "scripthub.scripts.relatorios.compilar.compilar_pdfs"


def test_carregar_relatorios_csv_corrompido_loga_aviso_e_continua(tmp_path, mocker):
    caminho_download = tmp_path / "relatorios"
    caminho_download.mkdir()
    caminho_csv = caminho_download / "janeiro_1.csv"
    caminho_csv.write_text("conteudo", encoding="utf-8")
    mocker.patch(f"{_PATCH}.pd.read_csv", side_effect=Exception("csv corrompido"))
    mock_log = mocker.patch(f"{_PATCH}.log")

    resultado = _carregar_relatorios({"Janeiro": ["url1"]}, caminho_download)

    assert resultado == {}
    mock_log.aviso.assert_any_call(f"Falha ao ler {caminho_csv}: csv corrompido")
    mock_log.erro.assert_not_called()
