from pathlib import Path

from scripthub.services.erros import ErroConfiguracao
from scripthub.services.moodle import MoodleSessao, extrair_frequencia


def extrair_todas_frequencias(
    *,
    url_login: str,
    usuario: str,
    senha: str,
    urls_frequencias: dict[str, str],
    diretorio_saida: Path,
) -> None:
    """Extrai, via HTTP, o XLSX de frequência de cada turma em `urls_frequencias` para `diretorio_saida`.

    Compartilhada por `auditar`, `extrair` e `compilar`, que diferem só em qual `Config`
    fornece as credenciais/URLs e em qual diretório recebe os arquivos baixados.
    """
    if not urls_frequencias:
        raise ErroConfiguracao("Nenhuma URL de frequência encontrada no settings.toml")

    diretorio_saida.mkdir(parents=True, exist_ok=True)

    sessao = MoodleSessao(url_login=url_login, usuario=usuario, senha=senha)
    sessao.login()

    for nome_turma, url in urls_frequencias.items():
        extrair_frequencia(sessao, url, nome_turma, diretorio_saida)
