import typer
from typer.testing import CliRunner

from scripthub._i18n import instalar
from scripthub.cli import app as _app_real

instalar()

runner = CliRunner()


def _app_minimo() -> typer.Typer:
    app = typer.Typer()

    @app.command()
    def cmd(nome: str):
        pass

    return app


def test_erro_de_parsing_mostra_um_unico_painel():
    resultado = runner.invoke(_app_minimo(), ["--opcao-inexistente"])

    assert resultado.output.count("╭") == 1
    assert resultado.output.count("╰") == 1


def test_erro_de_parsing_inclui_codigo_de_saida_na_mensagem():
    resultado = runner.invoke(_app_minimo(), ["--opcao-inexistente"])

    assert "Código de saída: 2" in resultado.output
    assert resultado.exit_code == 2


def test_erro_de_parsing_mantem_linha_de_uso_dentro_do_painel():
    resultado = runner.invoke(_app_minimo(), ["--opcao-inexistente"])

    inicio_painel = resultado.output.index("╭")
    assert "Uso:" in resultado.output[inicio_painel:]


def test_opcao_invalida_com_sugestao_nao_mostra_tupla_crua():
    resultado = runner.invoke(_app_real, ["--passo", "invalido"])

    assert "',)" not in resultado.output
    assert "Opções possíveis" in resultado.output


def test_comando_inexistente_nao_duplica_ponto_final():
    resultado = runner.invoke(_app_real, ["comando-inexistente"])

    assert ".. Código de saída" not in resultado.output
    assert ". Código de saída: 2" in resultado.output
