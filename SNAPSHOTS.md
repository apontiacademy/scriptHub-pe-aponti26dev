# Snapshots

Registro cumulativo do que já está em `dev`, mas ainda não foi promovido para `nightly` (branch de release candidate) nem virou uma entrada em [CHANGELOG.md](CHANGELOG.md).

`dev` usa merge queue com squash — cada PR vira um único commit linear, sem commit de merge. Cada commit em `dev` gera uma nova entrada `x.y.z.devN`, em que:

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
