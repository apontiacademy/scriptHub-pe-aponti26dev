# Contribuindo com o scriptHub

Guia de referência para o time da Aponti Academy contribuir com este repositório — como configurar o ambiente, o fluxo de branch/commit/PR, e os padrões que todo script novo precisa seguir para ser compatível com a estrutura do scriptHub.

## Ambiente de desenvolvimento

Requer Python 3.12+ e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run scripthub --help
```

Alguns scripts usam Playwright para automação de navegador. Se for mexer em um deles, instale o Chromium:

```bash
playwright install chromium
```

## Fluxo de contribuição

### Branches

`tipo/descrição-curta`, com o tipo indicando a natureza da mudança:

| Tipo | Uso |
|---|---|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `refactor` | Mudança interna sem alterar comportamento |
| `docs` | Documentação |
| `chore` | Manutenção (deps, config, testes, etc.) |

A descrição pode ter subhierarquia quando ajuda a localizar o escopo, ex.: `fix/ra/config` (fix em `auditar_relatorios`, área de config).

### Commits

```
tipo(escopo): descrição em pt-BR, no imperativo
```

O escopo é opcional e geralmente é o nome do módulo ou área afetada (`cli`, `frequencias`, `config,auditar_relatorios`, `log`). Exemplos reais do histórico:

```
feat(cli): substituir --passo int por slugs com aliases
fix(frequencias): alinhar seleção de form e inclusão do submit com download.py
refactor(log,config,menu): TSV log, aliases CLI no config e deprecar menu
chore(tests): implementar estrutura de testes completa com cobertura ≥ 80%
docs: atualizar READMEs internos
```

### Checklist antes de abrir PR

```bash
uv run pytest              # cobertura mínima de 80% é obrigatória (falha o build se não bater)
uv run ruff check .
uv run ruff format --check .
```

PRs são abertos contra `dev`, nunca contra `nightly` ou `main`. `dev` usa merge queue com squash — cada PR vira um único commit linear em `dev`, sem commit de merge.

O fluxo de branches tem 4 estágios:

```
branch de feature → dev → nightly → main
```

- **`dev`** — branch de integração contínua, recebe os PRs via merge queue (squash). Cada commit em `dev` gera uma entrada cumulativa em `SNAPSHOTS.md` — squash elimina a distinção entre "merge de PR" e "commit direto", todo commit em `dev` é um PR fechado.
- **`nightly`** — branch de release candidate, cortada a partir de `main` (não de `dev`). Quando um conjunto de snapshots em `dev` é considerado pronto, é promovido (merge) para `nightly` — é o que aparece na seção `[Unreleased]` de `CHANGELOG.md`.
- **`main`** — branch de release. Só recebe merge de `nightly` quando uma versão é oficialmente publicada.

## Versionamento e changelog

- **`CHANGELOG.md`** — histórico de versões já lançadas em `main`, no formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) (`0.x.y`: `x` sobe em mudança expressiva, `y` em mudança pontual). Versões retiradas por bug grave ou falha de segurança levam a tag `[YANKED]`.
- **`SNAPSHOTS.md`** — trabalho em andamento em `dev`, ainda não consolidado. Cada commit em `dev` vira uma entrada `x.y.z-Ns` (`x.y.z` = versão sendo construída, `N` = snapshot sequencial), e `pyproject.toml` em `dev` é atualizado junto (`version = "x.y.z-Ns"`).

Ciclo de vida de uma mudança:

1. Mergeada em `dev` (squash) → entra em `SNAPSHOTS.md` como snapshot
2. Promovida (merge) de `dev` para `nightly` → sai de `SNAPSHOTS.md`, entra em `[Unreleased]` no `CHANGELOG.md`
3. `nightly` mergeada em `main` (release) → `[Unreleased]` vira `## [x.y.z] - data`, e `pyproject.toml` em `main`/`nightly`/`docs/geral` reflete essa versão

Toda vez que a versão em `pyproject.toml` muda (novo snapshot, promoção `dev → nightly` ou release `nightly → main`), rode `uv sync` (ou `uv lock`) e commite o `uv.lock` atualizado junto — ele fixa a própria versão do pacote (`scripthub-pe-aponti26dev`) e fica desatualizado silenciosamente se o lock não for regenerado.

### Commits de changelog/release

Commits cujo único propósito é atualizar `CHANGELOG.md`, `SNAPSHOTS.md` ou a versão em `pyproject.toml` como parte de uma promoção ou release **não geram uma nova entrada própria** — eles são o mecanismo de registro, não o conteúdo registrado (senão todo update exigiria um update para documentá-lo, indefinidamente). Use os prefixos:

```
chore(changelog): promover snapshots para nightly    # dev → nightly
chore(release): 0.20.0                                 # nightly → main
```

`dev`, `nightly` e `main` são protegidas por ruleset — só aceitam mudança via PR, nunca commit direto. Isso também vale para esses commits, mas o mecanismo muda dependendo do caso:

- **Snapshot de cada PR** (entrada em `SNAPSHOTS.md` + versão `x.y.z-Ns` em `pyproject.toml`) — não é um evento separado. O autor já inclui essa atualização na própria branch de feature, como parte do PR normal contra `dev`. Não existe branch/PR dedicada para isso.
- **Promoção `dev → nightly`** — branch dedicada a partir de `dev`, levando as mudanças de código da versão + o commit `chore(changelog)`, que consolida `[Unreleased]` em `CHANGELOG.md` e troca a versão em `pyproject.toml` do formato de snapshot para a versão plana (`x.y.z-Ns` → `x.y.z`). PR contra `nightly`. Essa branch **não** limpa `SNAPSHOTS.md`.
- **Limpeza de `SNAPSHOTS.md`** — branch separada, também a partir de `dev`, com PR de volta contra o próprio `dev`, removendo as entradas já consolidadas em `[Unreleased]`. `SNAPSHOTS.md` é bookkeeping exclusivo de `dev`: essa limpeza nunca chega em `nightly` nem em `main`.
- **Promoção `nightly → main`** — branch dedicada a partir de `nightly`, com o commit `chore(release)`, que fecha `[Unreleased]` em `## [x.y.z] - data`. A versão em `pyproject.toml` já está correta desde a promoção anterior, não muda de novo aqui. PR contra `main`.

## Estrutura do projeto

```
src/scripthub/
├── cli.py                  # Ponto de entrada: comandos Typer
├── _i18n.py                # Traduções pt-BR para Typer/Click
├── scripts/                # Módulos de automação (um por pasta)
│   ├── auditar_frequencias/
│   ├── auditar_relatorios/
│   ├── auditar_softskills/
│   ├── compilacao_de_relatorios/
│   └── torpedo_de_forum/
└── services/
    ├── config/             # Configuração interativa (scripthub config)
    ├── log.py              # Helpers de output unificados
    └── menu/               # Menu interativo (scripthub menu)
```

Cada pacote de script segue um dos dois padrões:

**Padrão A — pipeline por escopos** (`auditar_frequencias`, `auditar_relatorios`):
- `__init__.py` — declara `MENU_CMD`, exporta `ESCOPOS` e `get_config`
- `ESCOPOS`: lista de `Escopo(slug, nome, func, aliases)` — ver `services/escopo.py`
- `get_config()`: retorna a dataclass de configuração (carrega `.env` + `settings.json`)
- O CLI usa `executar_script()` para iterar os escopos com log por passo e captura de exceção
- O `--passo <slug>` (ou alias de uma letra) executa apenas o passo correspondente

**Padrão B — função main** (`auditar_softskills`, `compilacao_de_relatorios`, `torpedo_de_forum`) — **DEPRECIADO**:
- `__init__.py` — declara `MENU_CMD`, exporta apenas `main`
- `main()` carrega configuração internamente e executa o pipeline diretamente
- Não crie novos scripts com este padrão. Os existentes devem ser migrados para o Padrão A o quanto antes.

## Adicionando um novo script

1. Criar pasta em `src/scripthub/scripts/<nome>/`
2. Arquivos obrigatórios: `__init__.py`, `main.py`, `config.py`
3. No `__init__.py`, declarar `MENU_CMD` e exportar `ESCOPOS` + `get_config` (Padrão A):

```python
MENU_CMD = ("meu_script",)
from .main import ESCOPOS
from .config import get_config
```

4. Em `main.py`, importar `Escopo` e definir `ESCOPOS` como lista de instâncias:

```python
from scripthub.services.escopo import Escopo

ESCOPOS = [
    Escopo("baixar",    "Baixar dados", baixar_dados,  ("b",)),
    Escopo("processar", "Processar",    processar,     ("p",)),
]

def baixar_dados(config: Config): ...
def processar(config: Config): ...
```

Slugs devem ser verbos no infinitivo. Aliases são letras únicas para uso rápido no terminal.

5. Adicionar campos configuráveis em `services/config/esquemas.py` (ver "Sistema de configuração" abaixo)
6. Seguir o padrão de output (log helpers) e o contrato de erros abaixo
7. Registrar o comando em `src/scripthub/cli.py`
8. Escrever os testes antes ou junto da implementação (ver "TDD e testes" abaixo) — o menu detecta automaticamente novos scripts que tenham `MENU_CMD` no `__init__.py`, não precisa de registro manual ali

## Padrão de output dos scripts

Todos os scripts devem usar os helpers de `scripthub.services.log`:

```python
from scripthub.services import log
```

| Helper | Quando usar | Saída |
|---|---|---|
| `log.secao("TÍTULO")` | Início de uma etapa principal | `\n===...===\n▶ TÍTULO\n===...===` |
| `log.passo("msg")` | Passo em andamento | `  • msg` |
| `log.ok("msg")` | Conclusão bem-sucedida | `  ✔ msg` |
| `log.erro("msg")` | Erro (vai para stderr) | `  ❌ msg` |
| `log.aviso("msg")` | Aviso não-fatal | `  ⚠️  msg` |

**Nunca use `print()` diretamente nos scripts.**

Todo output é persistido automaticamente em `logs/scripthub.log` (ignorado pelo git).

## Contrato de erros

- **Funções de biblioteca**: levantar exceções (`ValueError`, `RuntimeError`, `FileNotFoundError`, etc.) — nunca chamar `sys.exit()`
- **CLI (`executar_script`)**: captura exceções das funções ESCOPOS e termina com `typer.Exit(1)`
- **Menu**: invoca o CLI via subprocess (`scripthub <cmd>`), o exit code do processo é exibido ao final

```python
# ✅ Correto — função de biblioteca
def main(config: Config):
    if not arquivo.exists():
        raise RuntimeError(f"Arquivo não encontrado: {arquivo}")

# ❌ Errado — sys.exit dentro de função de biblioteca
def main(config: Config):
    if not arquivo.exists():
        print("❌ Arquivo não encontrado", file=sys.stderr)
        sys.exit(1)
```

## Sistema de configuração

Os campos configuráveis de cada script são declarados em `services/config/esquemas.py` como entradas do dict `ESQUEMAS`, usando a dataclass `Campo` de `services/config/campo.py`.

```python
# services/config/esquemas.py
ESQUEMAS: dict[str, list[Campo]] = {
    "nome_do_modulo": [
        Campo(
            chave="moodle_usuario",
            rotulo="Usuário do Moodle",
            tipo="texto",
            origem="env",           # "env" → .env  |  "settings" → settings.json
            env_var="MOODLE_USUARIO",
        ),
        Campo(
            chave="moodle_url_login",
            rotulo="URL de login",
            tipo="url",
            origem="settings",
            json_chaves=["moodle", "urlLogin"],   # caminho de acesso no JSON
            obrigatorio=True,
        ),
    ],
}
```

Tipos de campo disponíveis:

| Tipo | Descrição |
|---|---|
| `texto` | String simples |
| `senha` | String mascarada na exibição |
| `url` | URL validada por regex |
| `caminho` | Caminho de arquivo ou diretório |
| `bool` | Booleano (sim/não interativo) |
| `int` | Inteiro |
| `lista_url` | Lista de URLs |
| `dict_str_url` | Dict `{str: url}` |
| `dict_str_lista_url` | Dict `{str: [url, ...]}` |

Use `depende_de="chave_outro_campo"` para tornar um campo condicional ao valor de outro campo booleano.

Com o campo declarado, ele já aparece automaticamente em `uv run scripthub config -s <modulo>` — não é preciso nenhum código adicional de UI.

## TDD e testes

Sempre escreva o teste antes da implementação:

1. **Escreva o teste que falha** — defina a interface e o comportamento esperado
2. **Implemente o mínimo para passar** — sem código especulativo
3. **Refatore** — limpe duplicação, sem alterar comportamento
4. **Repita** por função ou camada

### Ordem de complexidade crescente

1. Funções puras (sem I/O) — sem mocks
2. Funções com arquivo/path — use `tmp_path`
3. Funções com API externa — use `mocker.patch()`
4. Orquestradores (ESCOPOS) — mocke os serviços que chamam

### Regra: novo serviço = teste primeiro

Antes de criar qualquer arquivo em `services/`, escreva `tests/services/test_<nome>.py` com pelo menos um teste que falha. Só então crie o serviço.

### Estrutura

```
tests/
├── conftest.py                          # Fixture compartilhada: moodle_env(tmp_path)
├── menu/test_menu.py
├── auditar_frequencias/
│   ├── test_config.py
│   └── test_exportar_frequencias.py
├── auditar_relatorios/
│   ├── test_config.py
│   ├── test_backup.py
│   └── test_middleware.py
├── auditar_softskills/
│   ├── test_config.py
│   ├── test_download_softskills.py
│   └── test_integracao_drive.py
├── compilacao_de_relatorios/
│   ├── test_config.py
│   └── test_compilar_pdfs.py
├── torpedo_de_forum/
│   ├── test_config.py
│   └── test_main.py
└── services/
    ├── test_validacao.py
    └── test_persistencia.py
```

### Comandos

```bash
# Rodar todos com coverage
uv run pytest

# Rodar sem coverage (mais rápido para iteração)
uv run pytest --no-cov

# Rodar um módulo específico
uv run pytest --no-cov tests/services/
```

### Padrões obrigatórios

**Mocking de I/O externo** — usar `mocker` fixture do `pytest-mock`:
```python
def test_algo(mocker):
    mocker.patch("scripthub.scripts.<modulo>.<arquivo>.<funcao>", return_value=...)
```

**Config loading** — substituir `DIRETORIO_BASE` via `monkeypatch`:
```python
def test_config(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("MOODLE_USUARIO=user\nMOODLE_SENHA=pass\n")
    (tmp_path / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    monkeypatch.setattr(cfg_module, "DIRETORIO_BASE", tmp_path)
```

**Casos data-driven** — usar `@pytest.mark.parametrize`:
```python
@pytest.mark.parametrize("entrada,esperado", [...])
def test_funcao(entrada, esperado):
    assert funcao(entrada) == esperado
```

### O que NÃO testar

- Playwright real (fazer_login, publicar_no_forum) — teste apenas funções puras como `carregar_conteudo`, `_md_para_html`
- Geração de PDF com FPDF — instanciar `RelatorioPDF` requer fontes instaladas
- Google API real — sempre mockar `build`, `Credentials.from_service_account_file`, `gspread.authorize`
- pentefino Core real — mockar `executar_analise_core`
