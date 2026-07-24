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

### 0.21.0.dev3 - 2026-07-23 - (PR#108)

- **Changed**: seção "Comandos úteis" de `CLAUDE.md` — remove a referência obsoleta a `scripthub menu` (removido em #107) e adiciona os comandos de teste/lint do checklist de PR

### 0.21.0.dev4 - 2026-07-24 - (PR#109)

- **Changed**: pacotes de script renomeados para nomes de domínio mais curtos (`auditar_frequencias` → `frequencias`, `auditar_softskills` → `softskills`, `torpedo_de_forum` → `torpedo`) via `git mv` puro — comandos CLI (`scripthub frequencias`/`f`, `softskills`/`s`, `torpedo`/`t`) e configuração local (`.env`/`settings.json`) não mudam, movidos junto com a pasta (Closes #59)
- **Changed**: `auditar_relatorios`/`compilacao_de_relatorios` viram subpacotes `relatorios/{auditar,compilar}` de um único domínio `relatorios`, com CLI reescrito em subapps Typer (`relatorios auditar`/`relatorios compilar`) e `.env`/`settings.json` agora compartilhados na raiz do domínio (`relatorios/`) em vez de um arquivo por script. **Breaking change**: quem já tinha configuração local de `auditar_relatorios`/`compilacao_de_relatorios` precisa reconfigurar manualmente (`scripthub config relatorios`) — não há migração automática dos arquivos antigos; o alias plano `ra`/`rc` também deixa de existir, substituído pelo alias encadeado `r a`/`r c`
- **Changed**: `scripthub config`/`visualizar` passam a receber o domínio como argumento posicional em vez da opção `-s`/`--script` (ex.: `scripthub config -s relatorios` vira `scripthub config relatorios`); `--script`/`-s` passa a existir só como opção de priorização de campos dentro de domínios multi-script (ex.: `scripthub config relatorios --script auditar`). **Breaking change**: scripts/automações que invocam `scripthub config -s <nome>` diretamente precisam migrar para a forma posicional; nomes antigos de script (`auditar_relatorios`, `compilacao_de_relatorios`, `auditar_softskills`, `torpedo_de_forum`, `auditar_frequencias`) não são mais reconhecidos por `ALIASES_CLI`/`ESQUEMAS`
- **Fixed**: `--script` em `scripthub config`/`visualizar` deixava campos exclusivos de outro script do mesmo domínio marcados como obrigatórios, mantendo o domínio permanentemente `⚠️ pendente` para quem usa só um dos scripts; e um typo em `--script` era silenciosamente ignorado, sem nenhum aviso — corrigidos com `_escopar_por_script` (obrigatoriedade) e `_validar_script` (`ErroUsoCLI` para valor inválido)
