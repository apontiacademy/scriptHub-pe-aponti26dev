from __future__ import annotations

from pathlib import Path

import requests
from bs4 import BeautifulSoup

from scripthub.services import log

_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


class MoodleSessao:
    """Cliente HTTP autenticado para o Moodle.

    Substitui o Playwright nos scripts de download — autentica via POST,
    mantém cookies entre requisições e baixa arquivos diretamente.
    """

    def __init__(
        self,
        url_login: str,
        usuario: str,
        senha: str,
        *,
        _session: requests.Session | None = None,
    ) -> None:
        self.url_login = url_login
        self.usuario = usuario
        self.senha = senha
        self._session: requests.Session = _session or requests.Session()
        self._session.headers.update({"User-Agent": _USER_AGENT})

    # ── autenticação ──────────────────────────────────────────────────────────

    def login(self) -> None:
        """Autentica no Moodle via POST. Lança RuntimeError se falhar."""
        resp = self._session.get(self.url_login)
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("input", {"name": "logintoken"})
        token = tag["value"] if tag else None

        post_resp = self._session.post(
            self.url_login,
            data={
                "username": self.usuario,
                "password": self.senha,
                "logintoken": token,
                "anchor": "",
            },
        )
        if "/login/" in post_resp.url:
            raise RuntimeError(
                "Login falhou: credenciais inválidas ou redirecionado para a tela de login"
            )
        log.ok("Login OK")

    # ── requisições genéricas ─────────────────────────────────────────────────

    def get(self, url: str, **kwargs) -> requests.Response:
        return self._session.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self._session.post(url, **kwargs)

    # ── download de arquivos ──────────────────────────────────────────────────

    def baixar(
        self,
        url: str,
        destino: Path,
        *,
        method: str = "get",
        data: dict | None = None,
    ) -> None:
        """Baixa um arquivo para *destino*.

        Lança RuntimeError se a resposta indicar sessão expirada (redirect para /login/).
        """
        if method == "post":
            resp = self._session.post(url, data=data or {})
        else:
            resp = self._session.get(url)

        if "/login/" in resp.url:
            raise RuntimeError(
                f"Sessão expirada ao tentar baixar: {url}"
            )

        resp.raise_for_status()
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(resp.content)
