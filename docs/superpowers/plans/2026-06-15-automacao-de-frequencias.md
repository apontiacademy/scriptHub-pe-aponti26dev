# automacao_de_frequencias — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar o módulo `automacao_de_frequencias` que faz login no Moodle e exporta relatórios de frequência como XLSX para cada turma configurada em `settings.json`.

**Architecture:** Módulo Python independente com o mesmo padrão de `automacao_de_relatorios`: `config.py` separa credenciais (`.env`) de configurações (`settings.json`); `exportar_frequencias.py` orquestra o Playwright (login único + loop de exportação por turma); `executar.py` é o ponto de entrada do pipeline.

**Tech Stack:** Python 3.10+, Playwright (sync API), python-dotenv, pytest

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `automacao_de_frequencias/__init__.py` | Criar | Docstring do módulo |
| `automacao_de_frequencias/__main__.py` | Criar | Entry point (`python -m`) |
| `automacao_de_frequencias/config.py` | Criar | Dataclasses + carregamento de .env e settings.json |
| `automacao_de_frequencias/exportar_frequencias.py` | Criar | Login + loop de export via Playwright |
| `automacao_de_frequencias/executar.py` | Criar | Pipeline: banner + chamada das funções |
| `automacao_de_frequencias/.env.example` | Criar | Template de credenciais |
| `automacao_de_frequencias/settings.example.json` | Criar | Template de configuração |
| `tests/__init__.py` | Criar | Marca como pacote de testes |
| `tests/automacao_de_frequencias/__init__.py` | Criar | Marca como pacote de testes |
| `tests/automacao_de_frequencias/test_config.py` | Criar | Testes de Config.load() |
| `tests/automacao_de_frequencias/test_exportar_frequencias.py` | Criar | Testes das funções Playwright |

---

## Task 1: Skeleton do módulo e arquivos de exemplo

**Files:**
- Criar: `automacao_de_frequencias/__init__.py`
- Criar: `automacao_de_frequencias/__main__.py`
- Criar: `automacao_de_frequencias/.env.example`
- Criar: `automacao_de_frequencias/settings.example.json`
- Criar: `tests/__init__.py`
- Criar: `tests/automacao_de_frequencias/__init__.py`

- [ ] **Step 1: Criar `automacao_de_frequencias/__init__.py`**

```python
"""Módulo de automação de exportação de frequências do Moodle."""
```

- [ ] **Step 2: Criar `automacao_de_frequencias/__main__.py`**

```python
from .executar import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Criar `automacao_de_frequencias/.env.example`**

```
MOODLE_USUARIO=seu_usuario_aqui
MOODLE_SENHA=sua_senha_aqui
```

- [ ] **Step 4: Criar `automacao_de_frequencias/settings.example.json`**

```json
{
  "moodle": {
    "urlLogin": "https://moodle.yourinstitution.edu/login/index.php",
    "urlsFrequencias": {
      "Turma A": "https://moodle.yourinstitution.edu/mod/attendance/view.php?id=1111",
      "Turma B": "https://moodle.yourinstitution.edu/mod/attendance/view.php?id=2222"
    },
    "caminhoExportacao": "/home/you/Downloads/frequencias"
  }
}
```

- [ ] **Step 5: Criar pacotes de teste**

Criar `tests/__init__.py` (vazio) e `tests/automacao_de_frequencias/__init__.py` (vazio).

- [ ] **Step 6: Verificar que pytest está disponível**

```bash
python -m pytest --version
```

Se não estiver instalado: `pip install pytest`

- [ ] **Step 7: Commit**

```bash
git add automacao_de_frequencias/__init__.py automacao_de_frequencias/__main__.py automacao_de_frequencias/.env.example automacao_de_frequencias/settings.example.json tests/__init__.py tests/automacao_de_frequencias/__init__.py
git commit -m "feat(automacao_de_frequencias): scaffold do módulo e arquivos de exemplo"
```

---

## Task 2: config.py

**Files:**
- Criar: `automacao_de_frequencias/config.py`
- Criar: `tests/automacao_de_frequencias/test_config.py`

- [ ] **Step 1: Escrever os testes que devem falhar**

Criar `tests/automacao_de_frequencias/test_config.py`:

```python
import json

import pytest

import automacao_de_frequencias.config as cfg_module
from automacao_de_frequencias.config import Config


@pytest.fixture
def settings_valido():
    return {
        "moodle": {
            "urlLogin": "https://example.com/login",
            "urlsFrequencias": {
                "Turma A": "https://example.com/freq?id=1",
                "Turma B": "https://example.com/freq?id=2",
            },
            "caminhoExportacao": "/tmp/frequencias",
        }
    }


def test_load_valido(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(
        json.dumps(settings_valido), encoding="utf-8"
    )
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    config = Config.load()

    assert config.moodle.usuario == "user"
    assert config.moodle.senha == "pass"
    assert config.moodle.url_login == "https://example.com/login"
    assert config.moodle.urls_frequencias == {
        "Turma A": "https://example.com/freq?id=1",
        "Turma B": "https://example.com/freq?id=2",
    }
    assert str(config.moodle.caminho_exportacao) == "/tmp/frequencias"


def test_load_sem_credenciais_levanta_excecao(tmp_path, monkeypatch, settings_valido):
    (tmp_path / ".env").write_text("")
    (tmp_path / "settings.json").write_text(
        json.dumps(settings_valido), encoding="utf-8"
    )
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(ValueError, match="MOODLE_USUARIO"):
        Config.load()


def test_load_sem_settings_levanta_excecao(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)

    with pytest.raises(FileNotFoundError):
        Config.load()
```

- [ ] **Step 2: Rodar testes — devem falhar**

```bash
python -m pytest tests/automacao_de_frequencias/test_config.py -v
```

Resultado esperado: `ERROR` ou `ModuleNotFoundError` (módulo não existe ainda).

- [ ] **Step 3: Criar `automacao_de_frequencias/config.py`**

```python
import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DIRETORIO_BASE = Path(__file__).resolve().parent


@dataclass
class MoodleConfig:
    usuario: str
    senha: str
    url_login: str
    urls_frequencias: dict[str, str]
    caminho_exportacao: Path


@dataclass
class Config:
    moodle: MoodleConfig

    @staticmethod
    def load() -> "Config":
        dados_env = Config.__carregar_env()
        dados_settings = Config.__carregar_settings_json()

        moodle_json = dados_settings.get("moodle", {})

        moodle_config = MoodleConfig(
            usuario=dados_env["moodle_usuario"],
            senha=dados_env["moodle_senha"],
            url_login=moodle_json["urlLogin"],
            urls_frequencias=moodle_json["urlsFrequencias"],
            caminho_exportacao=Path(moodle_json["caminhoExportacao"]),
        )

        return Config(moodle=moodle_config)

    @staticmethod
    def __carregar_env() -> dict:
        load_dotenv(dotenv_path=DIRETORIO_BASE / ".env")

        dados = {
            "moodle_usuario": os.getenv("MOODLE_USUARIO"),
            "moodle_senha": os.getenv("MOODLE_SENHA"),
        }

        if not dados["moodle_usuario"] or not dados["moodle_senha"]:
            raise ValueError(
                "MOODLE_USUARIO e MOODLE_SENHA devem ser definidos no arquivo .env"
            )
        return dados

    @staticmethod
    def __carregar_settings_json() -> dict:
        caminho_settings = DIRETORIO_BASE / "settings.json"

        if not caminho_settings.exists():
            raise FileNotFoundError(
                f"O arquivo {caminho_settings} não foi encontrado."
            )

        with open(caminho_settings, "r", encoding="utf-8") as f:
            return json.load(f)
```

- [ ] **Step 4: Rodar testes — devem passar**

```bash
python -m pytest tests/automacao_de_frequencias/test_config.py -v
```

Resultado esperado:
```
PASSED tests/automacao_de_frequencias/test_config.py::test_load_valido
PASSED tests/automacao_de_frequencias/test_config.py::test_load_sem_credenciais_levanta_excecao
PASSED tests/automacao_de_frequencias/test_config.py::test_load_sem_settings_levanta_excecao
```

- [ ] **Step 5: Commit**

```bash
git add automacao_de_frequencias/config.py tests/automacao_de_frequencias/test_config.py
git commit -m "feat(automacao_de_frequencias): config.py com MoodleConfig e Config.load()"
```

---

## Task 3: realizar_login

**Files:**
- Criar: `automacao_de_frequencias/exportar_frequencias.py` (parcial — só `realizar_login`)
- Modificar: `tests/automacao_de_frequencias/test_exportar_frequencias.py`

- [ ] **Step 1: Escrever o teste**

Criar `tests/automacao_de_frequencias/test_exportar_frequencias.py`:

```python
from unittest.mock import MagicMock, call

from automacao_de_frequencias.exportar_frequencias import realizar_login


def _make_page_mock(ghost_session=False):
    """Retorna um mock de page configurado para o cenário indicado."""
    page = MagicMock()

    ghost_locator = MagicMock()
    if ghost_session:
        ghost_locator.first.wait_for.return_value = None
    else:
        ghost_locator.first.wait_for.side_effect = Exception("timeout")

    username_locator = MagicMock()
    password_locator = MagicMock()
    loginbtn_locator = MagicMock()

    def locator_side_effect(selector):
        if "logininsidebaric" in selector or "Sair" in selector:
            return ghost_locator
        if selector == "#username":
            return username_locator
        if selector == "#password":
            return password_locator
        if selector == "#loginbtn":
            return loginbtn_locator
        return MagicMock()

    page.locator.side_effect = locator_side_effect
    return page, username_locator, password_locator, loginbtn_locator


def test_realizar_login_fluxo_normal():
    page, username_loc, password_loc, loginbtn_loc = _make_page_mock()

    realizar_login(page, "https://example.com/login", "user", "pass")

    page.goto.assert_called_with("https://example.com/login")
    username_loc.fill.assert_called_with("user")
    password_loc.fill.assert_called_with("pass")
    loginbtn_loc.click.assert_called()


def test_realizar_login_com_sessao_fantasma():
    page, _, _, _ = _make_page_mock(ghost_session=True)

    realizar_login(page, "https://example.com/login", "user", "pass")

    # Deve ir à URL de login duas vezes (uma para limpar sessão, outra para logar)
    assert page.goto.call_count == 2
    assert page.goto.call_args_list[0] == call("https://example.com/login")
    assert page.goto.call_args_list[1] == call("https://example.com/login")
```

- [ ] **Step 2: Rodar teste — deve falhar**

```bash
python -m pytest tests/automacao_de_frequencias/test_exportar_frequencias.py -v
```

Resultado esperado: `ERROR` (módulo não existe).

- [ ] **Step 3: Criar `automacao_de_frequencias/exportar_frequencias.py` com `realizar_login`**

```python
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from .config import Config

BASE_DIR = Path(__file__).resolve().parent


def realizar_login(page, url_login, usuario, senha):
    print("  • Iniciando processo de login...")
    page.goto(url_login)
    page.wait_for_load_state("domcontentloaded")

    try:
        botao_sair = page.locator(
            "#logininsidebaric, button:has-text('Sair'), button:has-text('Log out')"
        ).first
        botao_sair.wait_for(state="visible", timeout=2000)
        print("  • Sessão fantasma detectada! Clicando em 'Sair' para limpar...")
        botao_sair.click()
        page.wait_for_load_state("networkidle")
        page.goto(url_login)
        page.wait_for_load_state("domcontentloaded")
    except Exception:
        pass

    print("  • Preenchendo credenciais...")
    page.locator("#username").fill(usuario)

    try:
        page.locator("#password").fill(senha)
    except Exception:
        page.locator("input[name='password']").fill(senha)

    try:
        page.locator("#loginbtn").click(timeout=5000)
        page.wait_for_load_state("networkidle")
    except Exception:
        page.screenshot(path=str(BASE_DIR / "debug_falha_login.png"))
        page.locator("button[type='submit']").click()
        page.wait_for_load_state("networkidle")

    print("  ✔ Login realizado com sucesso!")
```

- [ ] **Step 4: Rodar testes — devem passar**

```bash
python -m pytest tests/automacao_de_frequencias/test_exportar_frequencias.py -v
```

Resultado esperado:
```
PASSED ...::test_realizar_login_fluxo_normal
PASSED ...::test_realizar_login_com_sessao_fantasma
```

- [ ] **Step 5: Commit**

```bash
git add automacao_de_frequencias/exportar_frequencias.py tests/automacao_de_frequencias/test_exportar_frequencias.py
git commit -m "feat(automacao_de_frequencias): realizar_login via Playwright"
```

---

## Task 4: exportar_frequencia

**Files:**
- Modificar: `automacao_de_frequencias/exportar_frequencias.py` (adicionar função)
- Modificar: `tests/automacao_de_frequencias/test_exportar_frequencias.py` (adicionar testes)

- [ ] **Step 1: Adicionar testes ao arquivo de teste existente**

No **topo** de `tests/automacao_de_frequencias/test_exportar_frequencias.py`, substituir os imports existentes por:

```python
from contextlib import contextmanager
from unittest.mock import MagicMock, call, patch

from automacao_de_frequencias.exportar_frequencias import exportar_frequencia, realizar_login
```

Ao **final** do arquivo, adicionar as funções abaixo:


def _make_page_com_download(url_atual="https://example.com/freq?id=1"):
    """Retorna page mock configurado para fluxo de download."""
    page = MagicMock()
    page.url = url_atual

    download_mock = MagicMock()

    @contextmanager
    def mock_expect_download(**kwargs):
        yield download_mock

    page.expect_download = mock_expect_download
    page.get_by_label.return_value.is_checked.return_value = False

    return page, download_mock


def test_exportar_frequencia_sucesso(tmp_path):
    page, download_mock = _make_page_com_download()

    exportar_frequencia(
        page,
        "https://example.com/freq?id=1",
        "Turma A",
        tmp_path,
        "https://example.com/login",
        "user",
        "pass",
    )

    # Checkbox foi marcado
    page.get_by_label.return_value.check.assert_called_once()
    # Botão OK foi clicado
    page.get_by_role.assert_called_with("button", name="OK")
    page.get_by_role.return_value.click.assert_called_once()
    # Arquivo salvo com nome da turma
    download_mock.value.save_as.assert_called_with(str(tmp_path / "Turma A.xlsx"))


def test_exportar_frequencia_ja_marcado_nao_marca_novamente(tmp_path):
    page, download_mock = _make_page_com_download()
    page.get_by_label.return_value.is_checked.return_value = True

    exportar_frequencia(
        page,
        "https://example.com/freq?id=1",
        "Turma A",
        tmp_path,
        "https://example.com/login",
        "user",
        "pass",
    )

    page.get_by_label.return_value.check.assert_not_called()


def test_exportar_frequencia_redireciona_para_login(tmp_path):
    page, download_mock = _make_page_com_download(url_atual="https://example.com/login")

    with patch(
        "automacao_de_frequencias.exportar_frequencias.realizar_login"
    ) as mock_login:
        exportar_frequencia(
            page,
            "https://example.com/freq?id=1",
            "Turma A",
            tmp_path,
            "https://example.com/login",
            "user",
            "pass",
        )

        mock_login.assert_called_once_with(
            page, "https://example.com/login", "user", "pass"
        )
```

- [ ] **Step 2: Rodar testes — devem falhar**

```bash
python -m pytest tests/automacao_de_frequencias/test_exportar_frequencias.py::test_exportar_frequencia_sucesso -v
```

Resultado esperado: `AttributeError` ou `ImportError` (função não existe).

- [ ] **Step 3: Adicionar `exportar_frequencia` ao `exportar_frequencias.py`**

Adicionar após `realizar_login`:

```python
def exportar_frequencia(page, url, nome_turma, caminho_saida, url_login, usuario, senha):
    print(f"  • Exportando frequência: {nome_turma}")
    page.goto(url)
    page.wait_for_load_state("networkidle")

    if "login" in page.url:
        print("  • Sessão expirada. Reconectando...")
        realizar_login(page, url_login, usuario, senha)
        page.goto(url)
        page.wait_for_load_state("networkidle")

    try:
        checkbox = page.get_by_label(re.compile(r"observa", re.IGNORECASE))
        if not checkbox.is_checked():
            checkbox.check()

        caminho_arquivo = caminho_saida / f"{nome_turma}.xlsx"
        with page.expect_download(timeout=15000) as download_info:
            page.get_by_role("button", name="OK").click()

        download_info.value.save_as(str(caminho_arquivo))
        print(f"  ✔ Salvo em: {caminho_arquivo}")

    except Exception as e:
        print(f"  ❌ ERRO ao exportar {nome_turma}: {e}", file=sys.stderr)
```

- [ ] **Step 4: Rodar todos os testes — devem passar**

```bash
python -m pytest tests/automacao_de_frequencias/test_exportar_frequencias.py -v
```

Resultado esperado: todos os 5 testes `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add automacao_de_frequencias/exportar_frequencias.py tests/automacao_de_frequencias/test_exportar_frequencias.py
git commit -m "feat(automacao_de_frequencias): exportar_frequencia com checkbox e download XLSX"
```

---

## Task 5: main em exportar_frequencias.py

**Files:**
- Modificar: `automacao_de_frequencias/exportar_frequencias.py` (adicionar `main`)

Sem testes unitários para `main` — ela orquestra Playwright diretamente e é coberta por teste de integração manual descrito no passo de verificação.

- [ ] **Step 1: Adicionar `main` ao final de `exportar_frequencias.py`**

```python
def main(config: Config):
    print("=" * 80)
    print("▶ [ESCOPO 1] EXPORTAÇÃO DE FREQUÊNCIAS (MOODLE)")
    print("=" * 80)

    url_login = config.moodle.url_login
    usuario = config.moodle.usuario
    senha = config.moodle.senha
    urls_frequencias = config.moodle.urls_frequencias
    caminho_saida = config.moodle.caminho_exportacao

    if not urls_frequencias:
        print(
            "  ❌ ERRO: Nenhuma URL de frequência encontrada no settings.json",
            file=sys.stderr,
        )
        print("=" * 80)
        return

    caminho_saida.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as p:
            chrome_args = ["--disable-blink-features=AutomationControlled"]
            navegador = p.chromium.launch(headless=True, args=chrome_args)
            contexto = navegador.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768},
            )
            pagina = contexto.new_page()

            realizar_login(pagina, url_login, usuario, senha)

            for nome_turma, url in urls_frequencias.items():
                exportar_frequencia(
                    pagina, url, nome_turma, caminho_saida, url_login, usuario, senha
                )
                time.sleep(1.5)

        print("\n✔ Escopo 1 finalizado com sucesso!")
    except Exception as e:
        print(f"\n⚠️ Escopo 1 terminou com falhas: {e}", file=sys.stderr)

    print("=" * 80)
```

- [ ] **Step 2: Rodar suite completa de testes**

```bash
python -m pytest tests/automacao_de_frequencias/ -v
```

Resultado esperado: todos os testes anteriores ainda `PASSED`.

- [ ] **Step 3: Commit**

```bash
git add automacao_de_frequencias/exportar_frequencias.py
git commit -m "feat(automacao_de_frequencias): main do pipeline de exportação"
```

---

## Task 6: executar.py

**Files:**
- Criar: `automacao_de_frequencias/executar.py`

- [ ] **Step 1: Criar `automacao_de_frequencias/executar.py`**

```python
import automacao_de_frequencias.exportar_frequencias as exportar_frequencias

from .config import Config


def main():
    config = Config.load()

    print("=" * 80)
    print("▶ INICIANDO PIPELINE DE EXPORTAÇÃO DE FREQUÊNCIAS")
    print("=" * 80)
    print()

    exportar_frequencias.main(config)
    print()

    print("=" * 80)
    print("✔ PIPELINE EXECUTADO E CONCLUÍDO COM SUCESSO ABSOLUTO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar suite completa de testes**

```bash
python -m pytest tests/automacao_de_frequencias/ -v
```

Resultado esperado: todos os testes `PASSED`.

- [ ] **Step 3: Verificar que o módulo é importável**

```bash
python -c "import automacao_de_frequencias; print('OK')"
```

Resultado esperado: `OK`

- [ ] **Step 4: Commit**

```bash
git add automacao_de_frequencias/executar.py
git commit -m "feat(automacao_de_frequencias): executar.py e pipeline completo"
```

---

## Verificação final

- [ ] **Checar estrutura de arquivos**

```bash
python -c "
import os
for f in sorted(os.listdir('automacao_de_frequencias')):
    print(f)
"
```

Resultado esperado (entre outros arquivos):
```
__init__.py
__main__.py
.env.example
config.py
executar.py
exportar_frequencias.py
settings.example.json
```

- [ ] **Rodar suite completa**

```bash
python -m pytest tests/automacao_de_frequencias/ -v
```

Resultado esperado: todos os testes `PASSED`, nenhum `FAILED` ou `ERROR`.

- [ ] **Instrução para uso**

Copiar e preencher os arquivos de configuração antes de rodar:

```bash
cp automacao_de_frequencias/.env.example automacao_de_frequencias/.env
cp automacao_de_frequencias/settings.example.json automacao_de_frequencias/settings.json
# editar .env e settings.json com dados reais
python -m automacao_de_frequencias
```
