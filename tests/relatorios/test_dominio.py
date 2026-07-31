import scripthub.scripts.relatorios as relatorios
import scripthub.scripts.relatorios.compilar.config as compilar_config
import scripthub.scripts.relatorios.extrair.config as extrair_config


def test_dominio_e_definido_uma_unica_vez_na_raiz_do_pacote():
    assert relatorios.DOMINIO == "relatorios"


def test_submodulos_importam_dominio_da_raiz_em_vez_de_redefinir():
    assert compilar_config.DOMINIO is relatorios.DOMINIO
    assert extrair_config.DOMINIO is relatorios.DOMINIO
