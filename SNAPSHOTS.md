# Snapshots

Registro cumulativo do que já está em `dev`, mas ainda não foi promovido para `nightly` (branch de release candidate) nem virou uma entrada em [CHANGELOG.md](CHANGELOG.md).

`dev` usa squash manual — cada PR vira um único commit linear, sem commit de merge (mesmo mecanismo de `nightly`/`main`, ver "Squash manual em dev/nightly/main" em [CONTRIBUTING.md](CONTRIBUTING.md)). Cada commit em `dev` gera uma nova entrada `x.y.z.devN`, em que:

- `x.y.z` é a versão que está sendo construída — o próximo destino em `nightly`/`main`
- `N` é o número sequencial do snapshot dentro dessa versão (incrementa a cada commit em `dev`)

`pyproject.toml`, em `dev`, é atualizado junto com cada snapshot (`version = "x.y.z.devN"`) — formato PEP 440 (`.devN`), compatível com `uv lock`/`uv sync`.

Quando os snapshots de uma versão são promovidos para `nightly`, as entradas correspondentes saem daqui e viram a seção `[Unreleased]` de `CHANGELOG.md`. Quando `nightly` vira release em `main`, `[Unreleased]` vira `## [x.y.z] - data`.

Commits que só atualizam este arquivo, `CHANGELOG.md` ou a versão em `pyproject.toml` (`chore(changelog)`/`chore(release)`) não geram uma entrada própria — ver "Commits de changelog/release" em [CONTRIBUTING.md](CONTRIBUTING.md).

## 0.21.0 (em andamento em `dev`)

### 0.21.0.dev1 - 2026-07-22 - (PR#105)

- **Removed**: campo CPF do PDF de relatório de residência (`compilacao_de_relatorios`) — dado não disponível na origem (Moodle/CSV); configuração órfã `pdf.csvResidentes`/`PdfConfig.csv_residentes`, que ficou sem nenhum leitor após a remoção do único consumidor (`_carregar_cpfs()`) (Closes #100)

### 0.21.0.dev2 - 2026-07-23 - (PR#107)

- **Removed**: comandos `scripthub menu`/`m` e o pacote `services/menu` (depreciados) — a descoberta de scripts usada por `scripthub config` foi preservada em `services/config/main.py` (Closes #106)
