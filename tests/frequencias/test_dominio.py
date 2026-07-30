import scripthub.scripts.frequencias as frequencias
import scripthub.scripts.frequencias.auditar.config as auditar_config
import scripthub.scripts.frequencias.compilar.config as compilar_config
import scripthub.scripts.frequencias.extrair.config as extrair_config


def test_dominio_e_definido_uma_unica_vez_na_raiz_do_pacote():
    assert frequencias.DOMINIO == "frequencias"


def test_submodulos_importam_dominio_da_raiz_em_vez_de_redefinir():
    assert auditar_config.DOMINIO is frequencias.DOMINIO
    assert compilar_config.DOMINIO is frequencias.DOMINIO
    assert extrair_config.DOMINIO is frequencias.DOMINIO
