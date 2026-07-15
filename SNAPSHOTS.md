# Snapshots

Registro cumulativo do que já está em `dev`, mas ainda não foi promovido para `nightly` (branch de release candidate) nem virou uma entrada em [CHANGELOG.md](CHANGELOG.md).

`dev` usa squash manual — cada PR vira um único commit linear, sem commit de merge (mesmo mecanismo de `nightly`/`main`, ver "Squash manual em dev/nightly/main" em [CONTRIBUTING.md](CONTRIBUTING.md)). Cada commit em `dev` gera uma nova entrada `x.y.z.devN`, em que:

- `x.y.z` é a versão que está sendo construída — o próximo destino em `nightly`/`main`
- `N` é o número sequencial do snapshot dentro dessa versão (incrementa a cada commit em `dev`)

`pyproject.toml`, em `dev`, é atualizado junto com cada snapshot (`version = "x.y.z.devN"`) — formato PEP 440 (`.devN`), compatível com `uv lock`/`uv sync`.

Quando os snapshots de uma versão são promovidos para `nightly`, as entradas correspondentes saem daqui e viram a seção `[Unreleased]` de `CHANGELOG.md`. Quando `nightly` vira release em `main`, `[Unreleased]` vira `## [x.y.z] - data`.

Commits que só atualizam este arquivo, `CHANGELOG.md` ou a versão em `pyproject.toml` (`chore(changelog)`/`chore(release)`) não geram uma entrada própria — ver "Commits de changelog/release" em [CONTRIBUTING.md](CONTRIBUTING.md).

## 0.20.0 (em andamento em `dev`)

### 0.20.0.dev1 - 2026-06-25 - `6091df2` (PR#51)

- **Added**: `MoodleSessao` e `services/moodle/download.py` (cliente HTTP para Moodle); `GoogleSheetsClient` e `GoogleDriveClient` compartilhados (`services/google/`)
- **Changed**: `auditar_frequencias`, `auditar_relatorios` e `auditar_softskills` migrados de Playwright para requisições HTTP
- **Removed**: campo de configuração `headless` dos módulos migrados para HTTP

### 0.20.0.dev2 - 2026-07-02 - (PR#64)

- **Added**: `CHANGELOG.md`, `SNAPSHOTS.md` e `CONTRIBUTING.md`, documentando o fluxo `dev` → `nightly` → `main` e o protocolo de versionamento/changelog; flag `--version`/`-V` no CLI
- **Changed**: `CLAUDE.md` reduzido para referenciar `CONTRIBUTING.md` como fonte canônica; READMEs internos dos scripts atualizados para refletir a migração HTTP e o CLI atual

### 0.20.0.dev3 - 2026-07-03 - (PR#52)

- **Fixed**: `auditar_softskills` deixa de reprocessar aprovados já baixados, carregando-os do backup local (`carregar_aprovados_do_backup`); corrige detecção de "sem notas de soft skills" (comparação com `"0"` em vez de string falsy); corrige resolução de `credentials_path` (apontava para fora da pasta do módulo)
- **Changed**: `integracao_drive.py` usa `batch_clear` restrito às colunas do próprio CSV em vez de limpar a planilha inteira, preservando colunas adicionadas manualmente; mensagens de erro de configuração mais claras (`_obrigatorio`) e suporte a `moodle.urlBase` com fallback para `moodle.url` (legado)
- **Added**: logging de debug opcional em `get_quiz_ids` para diagnosticar turmas sem atividades encontradas

### 0.20.0.dev4 - 2026-07-07 - (chore/ruff-cleanup-dev)

- **Changed**: limpeza das violações de `ruff` restantes em `dev` após a chegada de `.github/workflows/ci.yml` (propagado de `main`/`nightly`, issue #67) — imports não usados/desordenados, `raise ... from` em blocos `except`, `zip(strict=)` em `download_softskills.py`; necessário para o CI de lint rodar limpo em `dev`

### 0.20.0.dev5 - 2026-07-08 - (PR#65)

- **Fixed**: `caminhoExportacaoAnalise` configurado via `scripthub config -s ra` deixa de ser ignorado — `csv_saida_analise` agora é resolvido uma única vez em `Config.load()` e usado tanto pelo Escopo 2 (middleware) quanto pelo Escopo 3 (integração Google Sheets) (Closes #55)
- **Changed**: `caminhoExportacaoAnalise` passa a ser obrigatório quando `exportarAnaliseRelatorio=true` (levanta `ValueError` em vez de cair silenciosamente no caminho padrão); suporte genérico a campos condicionalmente obrigatórios (`resolver_dependencias()` em `campo.py`), refletido em `scripthub config -s ra`
- **Fixed**: com `exportarAnaliseRelatorio=false`, o Escopo 2 volta a usar o caminho padrão do sistema silenciosamente em vez de travar no prompt interativo de caminho de saída do Core (pentefino); diretório de saída deixa de ser criado antecipadamente quando a exportação está desativada
- **Fixed**: `persistir()` remove do `settings.json` a chave de um campo opcional limpo pelo usuário em vez de deixá-la gravada (o que bloqueava o fallback ao caminho padrão); `_remover_chave_json` deixa de assumir `json_chaves` não-vazio, evitando `IndexError`

### 0.20.0.dev6 - 2026-07-09 - (PR#82)

- **Fixed**: `exportar_frequencia` (Escopo 1 de `auditar_frequencias`) deixava de enviar o campo `format` (não lia `<select>`, só `<input>`) e podia postar no formulário errado da página (`editmode.php` em vez do `mform` real de exportação), fazendo o Moodle devolver HTML em vez de XLSX (Closes #80)
- **Fixed**: checkboxes marcados por padrão no Moodle via atributo booleano `checked` "bare" (sem valor) deixavam de ser detectados — `BeautifulSoup` representa esse atributo como string vazia (falsy); troca de `inp.get("checked")` para `inp.has_attr("checked")`, também aplicado à detecção de `selected`/`multiple` nos `<select>`
- **Added**: validação da assinatura ZIP do arquivo baixado (`_e_xlsx_valido`) para falhar cedo com erro claro caso o Moodle volte a devolver uma página HTML em vez do XLSX esperado

### 0.20.0.dev7 - 2026-07-09 - (PR#83)

- **Changed**: `dev` passa a usar squash manual (mesmo mecanismo de `nightly`/`main`) em vez de merge queue automática; `CONTRIBUTING.md` documenta o padrão único `[vX.Y.Z(.devN)] título (#pr)` de título/descrição do squash para os três branches e passa a exigir que o bump de `SNAPSHOTS.md`/`devN` em `pyproject.toml` seja feito como último commit da branch, após aprovação da PR, em vez de na abertura (Closes #79)
- **Removed**: ruleset "dev merge queue" no GitHub; trigger `merge_group` para `dev` em `.github/workflows/ci.yml`, que nunca mais dispara sem a ruleset

### 0.20.0.dev8 - 2026-07-15 - (PR#85)

- **Fixed**: `_injetar_cookies` (`torpedo_de_forum/main.py`) montava cada cookie do Playwright com `url` e `path` simultaneamente, o que o Playwright rejeita (`Cookie should have either url or path`) — quebrava 100% das execuções de `uv run scripthub t` logo após o login; corrigido usando `c.domain` (já preenchido pelo `RequestsCookieJar` de `MoodleSessao`) em vez de derivar `url` via `urlparse(sessao.url_login)` (Closes #84)

### 0.20.0.dev9 - 2026-07-15 - (PR#90)

- **Fixed**: `uv.lock` refeito para refletir em `dev` o mesmo hotfix aplicado direto em `main` (ver `[0.19.3]` em [CHANGELOG.md](CHANGELOG.md)) — `pentefinocli-pe-aponti26dev` `0.1.0` (release retirada/yanked) atualizado para `0.2.1`, com bump decorrente do `cffi` para `2.1.0`
