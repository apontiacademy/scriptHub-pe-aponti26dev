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

### 0.21.0.dev5 - 2026-07-24 - (PR#110)

- **Added**: `scripthub relatorios extrair` — subcomando novo, atalho pro passo de extração (`relatorios auditar --passo extrair`)
- **Added**: `scripthub frequencias auditar` — subcomando novo, pipeline completo; `frequencias_app` sai do modelo `callback(invoke_without_command=True)` e passa a espelhar `relatorios_app`
- **Added**: `scripthub frequencias extrair` — subcomando novo, atalho pro passo de extração (`frequencias auditar --passo exportar`)
- **Changed**: `_ALIASES`/`--aliases` e READMEs de `relatorios`/`frequencias` atualizados com os comandos novos; `--passo`/`-p` permanece 100% intocado, sem depreciação nem remoção. **Breaking change**: `scripthub frequencias` sem subcomando agora dá o mesmo erro "Comando não fornecido" (exit 2) que `scripthub relatorios` sem subcomando já dava (Closes #89)

### 0.21.0.dev6 - 2026-07-27 - (PR#112)

- **Added**: `scripthub frequencias compilar`, novo subcomando irmão de `auditar` — extrai as frequências do Moodle (cópia própria, independente de `auditar`) e gera uma ata de frequência em PDF por turma: capa configurável, resumo geral da turma por mês, uma página por mês com a presença de cada aluno marcada por uma bolinha colorida, resumo geral por aluno do período inteiro e lista de justificativas consolidada ao final do documento
- **Added**: regras de negócio da ata — status do Moodle mapeado para cor (`PR`/`AU`/`AT`/`JU`), só `AU` conta como falta, `"Inscrições suspensas"` exclui o aluno inteiramente, matrícula tardia justifica automaticamente as sessões anteriores à data de inscrição, `"?"` (sessão sem chamada) conta como falta, e mais de 3 faltas no mês (limite fixo, não configurável) destaca a linha na página daquele mês
- **Added**: campos de configuração `atas.caminhoSaida`/`atas.caminhoLogo`/`atas.caminhoAssinatura`, escopados por script (`auditar`/`compilar`) em `services/config/esquemas.py` (Closes #58)
- **Changed**: lógica de download compartilhada entre `auditar` e `compilar` extraída para `services/moodle/attendance.py`; `frequencias/exportar_frequencias.py`/`integracao_google_sheets.py` movidos para `frequencias/auditar/`, com `exportar` renomeado para `extrair`

### 0.21.0.dev7 - 2026-07-27 - (PR#116)

- **Changed**: `relatorios extrair`/`frequencias extrair` deixam de ser um recorte do pipeline `auditar` (reaproveitavam `get_config`/`ESCOPOS` de lá, filtrando o passo `"extrair"`) e passam a ser scripts Padrão A próprios (`relatorios/extrair/`, `frequencias/extrair/`), com config enxuta (só `moodle.*`, sem `gsheets.*`) — comandos, aliases e flags permanecem idênticos, só o título do log muda de "AUDITORIA DE ..." para "EXTRAÇÃO DE ..." (Closes #113)
- **Added**: campo `moodle.caminhoDownloadRelatorio` em `settings.json` de `relatorios`, obrigatório para `auditar`/`extrair` — substitui o caminho fixo (`dados/relatorios/`) usado até então, deixando `relatorios` simétrico com `frequencias` (que já exigia `moodle.caminhoExportacao` para o mesmo tipo de saída). **Breaking change**: quem já tinha `settings.json` de `relatorios` configurado precisa adicionar essa chave manualmente (`scripthub config relatorios --script auditar`) — não há migração automática
- **Fixed**: coluna "Usado por" desatualizada nos READMEs de `relatorios`/`frequencias` — `moodle.urlLogin` (e, em `frequencias`, `moodle.urlsFrequencias`) aparecia como `ambos` desde que `compilar` foi adicionado (#115), quando na verdade já é lido por três scripts (`auditar`, `compilar`, `extrair`)

### 0.21.0.dev8 - 2026-07-27 - (PR#120)

- **Removed**: comando `relatorios auditar` (e alias `r a`/`relatorios a`) — na prática só o passo `extrair` tinha uso real, e já havia sido promovido a script próprio (`relatorios/extrair/`, #116); remove junto o pacote `relatorios/auditar/` (análise pente-fino via `pentefino`, integração Google Sheets, backup local em `.xlsx`), os campos de config exclusivos desses passos em `ESQUEMAS["relatorios"]` e a dependência `pentefinocli-pe-aponti26dev`, que ficou órfã (Closes #111)
- **Fixed**: `services/moodle/download.py::baixar_relatorio` (compartilhado entre `relatorios/extrair` e `relatorios/compilar`) só tinha cobertura de teste via os testes de `relatorios/auditar` apagados nesta PR — adiciona `tests/services/test_moodle_download.py` dedicado, restaurando a cobertura perdida
