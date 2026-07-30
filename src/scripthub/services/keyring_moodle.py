import keyring
import keyring.errors

from .erros import ErroConfiguracao

_SERVICO_PREFIXO = "scripthub"
_USUARIO_KEYRING = "moodle_senha"


def _servico(nome_dominio: str, perfil: str) -> str:
    return f"{_SERVICO_PREFIXO}-{perfil}-{nome_dominio}"


def obter_senha_moodle(nome_dominio: str, perfil: str) -> str | None:
    try:
        return keyring.get_password(_servico(nome_dominio, perfil), _USUARIO_KEYRING)
    except keyring.errors.KeyringError as e:
        raise ErroConfiguracao(f"Não foi possível ler a senha do Moodle no keyring do sistema: {e}") from e


def definir_senha_moodle(nome_dominio: str, perfil: str, senha: str) -> None:
    try:
        keyring.set_password(_servico(nome_dominio, perfil), _USUARIO_KEYRING, senha)
    except keyring.errors.KeyringError as e:
        raise ErroConfiguracao(f"Não foi possível salvar a senha do Moodle no keyring do sistema: {e}") from e


def remover_senha_moodle(nome_dominio: str, perfil: str) -> None:
    try:
        keyring.delete_password(_servico(nome_dominio, perfil), _USUARIO_KEYRING)
    except keyring.errors.PasswordDeleteError:
        pass
