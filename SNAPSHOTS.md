# Snapshots

Registro cumulativo do que já está em `dev`, mas ainda não foi promovido para `nightly` (branch de release candidate) nem virou uma entrada em [CHANGELOG.md](CHANGELOG.md).

`dev` usa merge queue com squash — cada PR vira um único commit linear, sem commit de merge. Cada commit em `dev` gera uma nova entrada `x.y.z-Ns`, em que:

- `x.y.z` é a versão que está sendo construída — o próximo destino em `nightly`/`main`
- `N` é o número sequencial do snapshot dentro dessa versão (incrementa a cada commit em `dev`)

`pyproject.toml`, em `dev`, é atualizado junto com cada snapshot (`version = "x.y.z-Ns"`).

Quando os snapshots de uma versão são promovidos para `nightly`, as entradas correspondentes saem daqui e viram a seção `[Unreleased]` de `CHANGELOG.md`. Quando `nightly` vira release em `main`, `[Unreleased]` vira `## [x.y.z] - data`.

Commits que só atualizam este arquivo, `CHANGELOG.md` ou a versão em `pyproject.toml` (`chore(changelog)`/`chore(release)`) não geram uma entrada própria — ver "Commits de changelog/release" em [CONTRIBUTING.md](CONTRIBUTING.md).

## 0.20.0 (em andamento em `dev`)

### 0.20.0-1s - 2026-06-25 - `6091df2` (PR#51)

- **Added**: `MoodleSessao` e `services/moodle/download.py` (cliente HTTP para Moodle); `GoogleSheetsClient` e `GoogleDriveClient` compartilhados (`services/google/`)
- **Changed**: `auditar_frequencias`, `auditar_relatorios` e `auditar_softskills` migrados de Playwright para requisições HTTP
- **Removed**: campo de configuração `headless` dos módulos migrados para HTTP
