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

Essa convenção vale só durante o lifecycle da branch de feature — é o que dá rastreamento ao histórico de commits enquanto o trabalho está em andamento. Ela é eliminada a partir do momento em que a PR vira snapshot: o commit de squash final que chega em `dev`, `nightly` ou `main` nunca carrega o marcador `tipo(escopo):` — ele segue o padrão `[vX.Y.Z(.devN)] título (#pr)` descrito em "Versionamento e changelog".

### Checklist antes de abrir PR

```bash
uv run pytest              # cobertura mínima de 80% é obrigatória (falha o build se não bater)
uv run ruff check .
uv run ruff format --check .
```

PRs são abertos contra `dev`, nunca contra `nightly` ou `main`.

O fluxo de branches tem 4 estágios:

```
branch de feature → dev → nightly → main
```

- **`dev`** — branch de integração contínua, recebe os PRs via squash manual (mesmo mecanismo de `nightly`/`main`). Cada commit em `dev` gera uma entrada cumulativa em `SNAPSHOTS.md` — squash elimina a distinção entre "merge de PR" e "commit direto", todo commit em `dev` é um PR fechado.
- **`nightly`** — branch de release candidate. Quando um conjunto de snapshots em `dev` é considerado pronto, é promovido (merge) para `nightly` — é o que aparece na seção `[Unreleased]` de `CHANGELOG.md`.
- **`main`** — branch de release. Só recebe merge de `nightly` quando uma versão é oficialmente publicada.

## Versionamento e changelog

- **`CHANGELOG.md`** — histórico de versões já lançadas em `main`, no formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) (`0.x.y`: `x` sobe em mudança expressiva, `y` em mudança pontual). Versões retiradas por bug grave ou falha de segurança levam a tag `[YANKED]`.
- **`SNAPSHOTS.md`** — trabalho em andamento em `dev`, ainda não consolidado. Cada commit em `dev` vira uma entrada `x.y.z.devN` (`x.y.z` = versão sendo construída, `N` = snapshot sequencial), e `pyproject.toml` em `dev` é atualizado junto (`version = "x.y.z.devN"`) — usa o sufixo `.devN` do PEP 440 para permanecer uma versão válida (`x.y.z-Ns` quebraria `uv lock`/`uv sync`).

O commit de squash que chega em `dev`, `nightly` ou `main` deve possuir o código da versão no início do título (ex.: `[v0.19.2] título da PR (#74)`) — garante rastreabilidade entre o commit e a entrada correspondente em `SNAPSHOTS.md`/`CHANGELOG.md`, mesmo em merges fora do fluxo normal (ex.: PRs de infraestrutura abertas direto contra `main`). Ver "Squash manual em dev/nightly/main" abaixo para o passo a passo.

Ciclo de vida de uma mudança:

1. Mergeada em `dev` (squash) → entra em `SNAPSHOTS.md` como snapshot
2. Promovida de `dev` para `nightly` **e para o próprio `dev`** (mesmo diff, duas PRs) → sai de `SNAPSHOTS.md`, entra no `CHANGELOG.md` de ambos os branches como `### [x.y.z] - data` aninhado em `[Unreleased]`
3. `nightly` mergeada em `main`, com o mesmo diff ecoado em `nightly` e em `dev` (release) → `### [x.y.z] - data` deixa de estar aninhado em `[Unreleased]` e vira seção de topo `## [x.y.z] - data` nos três branches, e `pyproject.toml` em `main`/`nightly`/`docs/geral` reflete essa versão

Toda vez que a versão em `pyproject.toml` muda (novo snapshot, promoção `dev → nightly` ou release `nightly → main`), rode `uv sync` (ou `uv lock`) e commite o `uv.lock` atualizado junto — ele fixa a própria versão do pacote (`scripthub-pe-aponti26dev`) e fica desatualizado silenciosamente se o lock não for regenerado.

### Squash manual em dev/nightly/main

`dev`, `nightly` e `main` usam o mesmo mecanismo: squash manual via ruleset `pull_request` (sem merge queue em nenhum dos três). Quem faz o merge de uma PR aprovada edita manualmente a caixa "Squash and merge" do GitHub:

- **Título**: trocar o prefixo de tipo (`tipo(escopo):`) pela versão — `[vX.Y.Z(.devN)] título (#pr)`, com `x.y.z.devN` em `dev` e `x.y.z` em `nightly`/`main`. O `(#pr)` só vem preenchido sozinho na sugestão inicial da caixa; ao editar o título, é preciso digitar `(#pr)` de volta manualmente.
- **Descrição**: o texto da entrada correspondente — a entrada nova em `SNAPSHOTS.md` (merge em `dev`) ou em `CHANGELOG.md` (merge em `nightly`/`main`).

Quando uma branch de promoção abre mais de uma PR (uma por branch de destino — ver "Promoção `dev → nightly`" e "Promoção `nightly → main`" em "Commits de changelog/release" abaixo), cada PR é squash-merged independentemente, seguindo esse mesmo padrão de título/descrição, só que para o seu próprio destino.

Sem merge queue serializando os merges, quem mergeia em `dev` precisa se atentar manualmente à ordem: mergear PRs aprovadas fora de ordem pode gerar dois commits com o mesmo `devN` ou pular a sequência.

É por isso que o bump de `SNAPSHOTS.md`/`devN` em `pyproject.toml` **não** é feito na abertura da PR — só se sabe o número correto depois que a PR é aprovada, já que outra PR pode mergear antes e consumir aquele `devN`. A entrada em `SNAPSHOTS.md` e o bump em `pyproject.toml` (+ `uv.lock`) são adicionados como último commit da branch, depois de aprovada a PR e imediatamente antes do squash: confira o HEAD atual de `dev`, calcule o próximo `devN` livre, empurre esse commit para a branch (a aprovação continua valendo — `dismiss_stale_reviews_on_push` é `false` na ruleset) e só então faça o squash. PRs contra `nightly`/`main` seguem a mesma lógica para a consolidação de `CHANGELOG.md`.

### Commits de changelog/release

Commits cujo único propósito é atualizar `CHANGELOG.md`, `SNAPSHOTS.md` ou a versão em `pyproject.toml` como parte de uma promoção ou release **não geram uma nova entrada própria** — eles são o mecanismo de registro, não o conteúdo registrado (senão todo update exigiria um update para documentá-lo, indefinidamente). Use os prefixos:

```
chore(changelog): promover snapshots para nightly    # dev → nightly
chore(release): 0.20.0                                 # nightly → main
```

O mesmo commit pode virar PR contra mais de um branch de destino ao mesmo tempo — ver os bullets "Promoção `dev → nightly`" e "Promoção `nightly → main`" logo abaixo.

`dev`, `nightly` e `main` são protegidas por ruleset — só aceitam mudança via PR, nunca commit direto. Isso também vale para esses commits, mas o mecanismo muda dependendo do caso:

- **Snapshot de cada PR** (entrada em `SNAPSHOTS.md` + versão `x.y.z.devN` em `pyproject.toml`) — não é um evento separado nem precisa de branch/PR dedicada: é adicionado como último commit da própria branch de feature, depois que a PR contra `dev` é aprovada e imediatamente antes do squash (ver "Squash manual em dev/nightly/main" acima).
- **Promoção `dev → nightly`** — branch dedicada a partir de `dev`, com o commit `chore(changelog)` que: (1) remove de `SNAPSHOTS.md` as entradas da versão sendo promovida; (2) adiciona esse mesmo conteúdo ao `CHANGELOG.md`, como `### [x.y.z] - data` aninhado dentro do `## [Unreleased]` (Keep a Changelog permite agrupar por versão mesmo dentro de "não lançado" — é assim que uma versão em `nightly` aparece documentada antes de virar release oficial em `main`); e (3) troca a versão em `pyproject.toml`/`uv.lock` do formato de snapshot para a versão plana (`x.y.z.devN` → `x.y.z`). Essa branch abre **duas PRs com o mesmo diff**: uma contra `nightly` e uma contra `dev` — as duas ficam sincronizadas quanto ao que já foi promovido (sem a PR contra `dev`, `CHANGELOG.md`/`SNAPSHOTS.md` de `dev` ficam defasados indefinidamente).
- **Promoção `nightly → main`** — branch dedicada a partir de `nightly`, que promove a entrada `### [x.y.z] - data` de dentro do `## [Unreleased]` para uma seção própria de topo, `## [x.y.z] - data` (os `####` de Added/Changed/Fixed/Removed dentro dela sobem para `###`), mantendo um `## [Unreleased]` vazio acima para a próxima leva. Corrige `pyproject.toml`/`uv.lock` para `x.y.z` quando aplicável (sempre em `main`; conferido/corrigido em `nightly` se necessário; `dev` normalmente não muda aqui, já que costuma estar adiantado no `devN` da próxima versão). Essa branch abre **três PRs com o mesmo diff**: contra `main` (release oficial), contra `nightly` e contra `dev` — os três ficam com o `CHANGELOG.md` sincronizado quanto a essa versão já ter sido oficialmente lançada.

## Estrutura do projeto

```
src/scripthub/
├── cli.py                  # Ponto de entrada: comandos Typer
├── _i18n.py                # Traduções pt-BR para Typer/Click
├── scripts/                # Módulos de automação (um por pasta)
│   ├── frequencias/
│   ├── relatorios/
│   │   ├── compilar/
│   │   └── extrair/
│   ├── softskills/
│   └── torpedo/
└── services/
    ├── config/             # Configuração interativa (scripthub config)
    └── log.py              # Helpers de output unificados
```

Cada pacote de script segue um dos dois padrões:

**Padrão A — pipeline por escopos** (`frequencias`, `relatorios/extrair`):
- `__init__.py` — declara `CLI_CMD`, exporta `ESCOPOS` e `get_config`
- `ESCOPOS`: lista de `Escopo(slug, nome, func, aliases)` — ver `services/escopo.py`
- `get_config()`: retorna a dataclass de configuração (carrega `.env` + `settings.json`)
- O CLI usa `executar_script()` para iterar os escopos com log por passo e captura de exceção
- O `--passo <slug>` (ou alias de uma letra) executa apenas o passo correspondente

**Padrão B — função main** (`softskills`, `relatorios/compilar`, `torpedo`) — **DEPRECIADO**:
- `__init__.py` — declara `CLI_CMD`, exporta apenas `main`
- `main()` carrega configuração internamente e executa o pipeline diretamente
- Não crie novos scripts com este padrão. Os existentes devem ser migrados para o Padrão A o quanto antes.

## Adicionando um novo script

1. Criar pasta em `src/scripthub/scripts/<nome>/`
2. Arquivos obrigatórios: `__init__.py`, `main.py`, `config.py`
3. No `__init__.py`, declarar `CLI_CMD` e exportar `ESCOPOS` + `get_config` (Padrão A):

```python
CLI_CMD = ("meu_script",)
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
6. Seguir o padrão de output (log helpers) e o contrato de erros abaixo — consultar [ERRORS.md](ERRORS.md) ao decidir que exceção levantar
7. Registrar o comando em `src/scripthub/cli.py`
8. Escrever os testes antes ou junto da implementação (ver "TDD e testes" abaixo) — o comando `config` detecta automaticamente novos scripts que tenham `CLI_CMD` no `__init__.py`, não precisa de registro manual ali

## Padrão de output dos scripts

Todos os scripts devem usar os helpers de `scripthub.services.log`:

```python
from scripthub.services import log
```

| Helper | Quando usar | Saída |
|---|---|---|
| `log.secao("TÍTULO")` | Início de uma etapa principal | `\n===...===\n▶ TÍTULO\n===...===` |
| `log.passo("msg")` | Passo em andamento | `  • msg` |
| `log.ok("msg")` | Passo/item concluído — não implica que o processo inteiro terminou | `  ✔ msg` |
| `log.sucesso("msg")` | Processo/pipeline **inteiro** terminou com sucesso (exit code `0`) — usar uma única vez, no fim | `  ✅ msg` (grava `SUCCESS` em `logs/scripthub.log`) |
| `log.erro("msg")` | Erro que leva o processo a terminar com exit code `!= 0` (vai para stderr) | painel Rich (`╭─ Erro ─╮`) no terminal; `  ❌ msg` em texto plano em `logs/scripthub.log` |
| `log.aviso("msg")` | Aviso não-fatal — execução segue, exit code final não é afetado | `  ⚠️  msg` |
| `log.traceback()` | Traceback completo de um erro genérico, só quando `--debug` está ativo (ver [ERRORS.md](ERRORS.md)) | traceback formatado pelo Rich no terminal; texto puro (`traceback.format_exc()`) em `logs/scripthub.log` |

**Nunca use `print()` diretamente nos scripts.**

Todo output é persistido automaticamente em `logs/scripthub.log` (ignorado pelo git).

### Como decidir entre `erro()` e `aviso()`

Pergunta prática: **se eu remover esta chamada de log e rodar o script até o
fim, o exit code final muda?**

- Se sim (o fluxo de controle logo depois é um `raise`/`sys.exit`/`typer.Exit`
  não-zero que **sempre** acontece quando essa condição ocorre) → `log.erro()`.
- Se não (o fluxo segue: `return` simples, `continue` em um loop, e nenhum
  contador dessa falha é verificado depois de forma a abortar o processo) →
  `log.aviso()`.

Um erro comum é usar `log.erro()` "porque parece grave", mesmo quando o
código imediatamente depois apenas segue em frente — isso conflita com o
contrato acima.

**Exceção documentada**: as linhas de `services/menu/main.py` que reportam o
resultado de um script escolhido no menu interativo (`log.ok(...)`/`log.erro(...)`
com o código de retorno) usam `ok`/`erro` para exibir o exit code de um
**subprocesso filho** (`scripthub <cmd>` rodado via `subprocess`), não o exit
code do próprio processo do `menu` — que sempre termina com código `0`
independentemente do resultado do filho. Por isso essas linhas não seguem, de
propósito, o contrato acima.

## Contrato de erros

- **Funções de biblioteca e comandos da CLI**: apenas levantar a exceção certa — nunca chamar `sys.exit()`/`typer.Exit()`, nunca logar o erro final diretamente. Prefira a subclasse mais específica de `scripthub.services.erros` (`ErroConfiguracao`, `ErroUsoCLI`, `FalhaParcial`, `ErroIntegracao`) quando a causa se encaixar numa categoria; caso contrário, uma exceção genérica do Python (`ValueError`, `RuntimeError`, `FileNotFoundError`, etc.) cai no código de saída genérico. Ver [ERRORS.md](ERRORS.md) para a tabela completa de códigos e a pergunta prática para escolher a categoria certa.
- **CLI**: um único handler global, `_executar_com_tratamento_global` (chamado a partir de `run()`, o entry point do pacote), envolve a execução do app inteiro — captura qualquer `ErroScriptHub`/exceção genérica, loga a mensagem final mesclada com o código de saída e termina com `SystemExit(<código>)`. Nenhum outro ponto do código (comandos, `executar_script`, `_carregar_config`) faz esse tratamento — todos só levantam a exceção.
- **Menu**: invoca o CLI via subprocess (`scripthub <cmd>`), o exit code do processo é exibido ao final

```python
# ✅ Correto — função de biblioteca, erro classificado
from scripthub.services.erros import ErroConfiguracao

def main(config: Config):
    if not arquivo.exists():
        raise ErroConfiguracao(f"Arquivo não encontrado: {arquivo}")

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
├── frequencias/
│   ├── test_config.py
│   └── test_exportar_frequencias.py
├── relatorios/
│   ├── compilar/
│   │   ├── test_config.py
│   │   └── test_compilar_pdfs.py
│   └── extrair/
│       ├── test_config.py
│       └── test_download_de_relatorios.py
├── softskills/
│   ├── test_config.py
│   ├── test_download_softskills.py
│   └── test_integracao_drive.py
├── torpedo/
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
- Orquestradores Padrão A/B pesados (ex.: `softskills/main.py`) cujo `main()`/`ESCOPOS` exigiria mockar
  muitos serviços externos para pouco ganho — teste os helpers que ele chama isoladamente; o próprio arquivo
  entra no `omit` de cobertura do `pyproject.toml` quando esse for o caso
