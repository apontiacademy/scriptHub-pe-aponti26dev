class ErroScriptHub(Exception):
    """Base para erros de biblioteca com código de saída próprio. Ver ERRORS.md."""

    codigo_saida = 1

    def __init__(self, mensagem: str, *, dica: str | None = None) -> None:
        super().__init__(mensagem)
        self.dica = dica


class ErroConfiguracao(ErroScriptHub):
    """settings.toml, keyring, credenciais ou um arquivo/diretório esperado de um passo anterior."""

    codigo_saida = 2


class ErroUsoCLI(ErroScriptHub):
    """Uso inválido da CLI — opção/passo/flag/argumento inválidos, validados antes do script rodar."""

    codigo_saida = 3


class FalhaParcial(ErroScriptHub):
    """Parte de um lote de itens falhou, mas o restante foi processado."""

    codigo_saida = 4


class ErroIntegracao(ErroScriptHub):
    """Moodle ou Google Sheets/Drive retornaram algo inesperado."""

    codigo_saida = 5
