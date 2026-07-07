class ErroScriptHub(Exception):
    """Base para erros de biblioteca com código de saída próprio. Ver ERRORS.md."""

    codigo_saida = 1


class ErroConfiguracao(ErroScriptHub):
    """.env, settings.json, credenciais ou um arquivo/diretório esperado de um passo anterior."""

    codigo_saida = 2


class FalhaParcial(ErroScriptHub):
    """Parte de um lote de itens falhou, mas o restante foi processado."""

    codigo_saida = 4


class ErroIntegracao(ErroScriptHub):
    """Moodle, Google Sheets/Drive ou o pentefino retornaram algo inesperado."""

    codigo_saida = 5
