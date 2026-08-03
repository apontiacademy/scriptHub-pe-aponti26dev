import pytest

from scripthub.services.erros import (
    ErroConfiguracao,
    ErroIntegracao,
    ErroScriptHub,
    ErroUsoCLI,
    FalhaParcial,
)


@pytest.mark.parametrize(
    "classe,codigo_esperado",
    [
        (ErroScriptHub, 1),
        (ErroConfiguracao, 2),
        (ErroUsoCLI, 3),
        (FalhaParcial, 4),
        (ErroIntegracao, 5),
    ],
)
def test_codigo_saida(classe, codigo_esperado):
    assert classe.codigo_saida == codigo_esperado


@pytest.mark.parametrize("classe", [ErroConfiguracao, ErroUsoCLI, FalhaParcial, ErroIntegracao])
def test_subclasses_herdam_de_erro_scripthub(classe):
    assert issubclass(classe, ErroScriptHub)
    assert issubclass(classe, Exception)


def test_mensagem_preservada():
    exc = ErroConfiguracao("settings.json não encontrado")
    assert str(exc) == "settings.json não encontrado"


def test_dica_padrao_e_none():
    exc = ErroConfiguracao("settings.json não encontrado")
    assert exc.dica is None


def test_dica_pode_ser_definida_na_criacao():
    exc = ErroConfiguracao("settings.json não encontrado", dica="Execute: scripthub config -s x")
    assert exc.dica == "Execute: scripthub config -s x"


def test_dica_pode_ser_atribuida_depois():
    exc = ErroUsoCLI("Passo 'x' inválido")
    exc.dica = "Consulte --help"
    assert exc.dica == "Consulte --help"
