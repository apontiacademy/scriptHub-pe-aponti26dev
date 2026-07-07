import pytest

from scripthub.services.erros import (
    ErroConfiguracao,
    ErroIntegracao,
    ErroScriptHub,
    FalhaParcial,
)


@pytest.mark.parametrize(
    "classe,codigo_esperado",
    [
        (ErroScriptHub, 1),
        (ErroConfiguracao, 2),
        (FalhaParcial, 4),
        (ErroIntegracao, 5),
    ],
)
def test_codigo_saida(classe, codigo_esperado):
    assert classe.codigo_saida == codigo_esperado


@pytest.mark.parametrize("classe", [ErroConfiguracao, FalhaParcial, ErroIntegracao])
def test_subclasses_herdam_de_erro_scripthub(classe):
    assert issubclass(classe, ErroScriptHub)
    assert issubclass(classe, Exception)


def test_mensagem_preservada():
    exc = ErroConfiguracao("settings.json não encontrado")
    assert str(exc) == "settings.json não encontrado"
