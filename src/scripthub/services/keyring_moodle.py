import keyring
import keyring.errors

_SERVICO_PREFIXO = "scripthub"
_USUARIO_KEYRING = "moodle_senha"


def _servico(nome_dominio: str) -> str:
    return f"{_SERVICO_PREFIXO}-{nome_dominio}"


def obter_senha_moodle(nome_dominio: str) -> str | None:
    return keyring.get_password(_servico(nome_dominio), _USUARIO_KEYRING)


def definir_senha_moodle(nome_dominio: str, senha: str) -> None:
    keyring.set_password(_servico(nome_dominio), _USUARIO_KEYRING, senha)


def remover_senha_moodle(nome_dominio: str) -> None:
    try:
        keyring.delete_password(_servico(nome_dominio), _USUARIO_KEYRING)
    except keyring.errors.PasswordDeleteError:
        pass
