# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog v1.1.0](https://keepachangelog.com/pt-BR/1.1.0/), e este projeto adere a versionamento `0.x.y` (API/CLI ainda instável — `x` sobe em mudanças expressivas, `y` em mudanças pontuais).

Versões retiradas por bug grave ou falha de segurança são marcadas com `[YANKED]` logo após a data (ex.: `## [0.0.5] - 2014-12-13 [YANKED]`). Nenhuma versão abaixo foi retirada até o momento.

O histórico de 0.1.0 a 0.19.1 foi reconstruído a partir do `git log` de `main`: cada merge de PR ou commit direto em `main` corresponde a uma versão.

## [Unreleased]

Nenhuma mudança promovida de `dev` para `nightly` ainda. O trabalho em andamento em `dev` (ainda não consolidado) é acompanhado em [SNAPSHOTS.md](SNAPSHOTS.md).

## [0.19.1] - 2026-06-25

### Added
- Suíte de testes completa, com cobertura mínima de 80% obrigatória no CI

### Changed
- `.gitignore` e `pyproject.toml` ajustados para suportar a suíte de testes

## [0.19.0] - 2026-06-25

### Added
- Serviço `escopo.py` para gerenciar os passos de um pipeline

### Changed
- `--passo` substituído por slugs com aliases no CLI (`auditar_relatorios`, `auditar_frequencias`)

## [0.18.1] - 2026-06-25

### Fixed
- Configuração do `auditar_relatorios`

## [0.18.0] - 2026-06-25

### Added
- Sistema de i18n (`_i18n.py`) para tradução da CLI
- Serviço de logging (`log.py`)
- `CLAUDE.md`

### Changed
- CLI e menu revisados

## [0.17.3] - 2026-06-25

### Changed
- Dependência `pentefino` via https em vez de ssh

## [0.17.2] - 2026-06-25

### Fixed
- Bugs identificados na revisão de código do comando `config`

## [0.17.1] - 2026-06-23

### Changed
- README com instruções de instalação via `uv` e do comando `config`

## [0.17.0] - 2026-06-23

### Added
- Comando `scripthub config` — sistema de configuração declarativo

## [0.16.0] - 2026-06-19

### Added
- Pacote `src/scripthub` e CLI baseada em Typer (comando `scripthub`)
- `uv.lock`

### Removed
- Estrutura antiga em módulos soltos na raiz do projeto
- `requirements.txt`

## [0.15.1] - 2026-06-19

### Changed
- Comandos Python no README

## [0.15.0] - 2026-06-19

### Added
- Módulo `compilacao_de_relatorios` (download e compilação de relatórios em PDF)

## [0.14.0] - 2026-06-18

### Added
- Integração com Google Sheets para exportação de frequências

## [0.13.10] - 2026-06-18

### Added
- READMEs internos por módulo

### Changed
- README principal reduzido e reorganizado

## [0.13.9] - 2026-06-17

### Fixed
- Feedback do script e retorno ao menu (#32)

## [0.13.8] - 2026-06-17

### Fixed
- Loop indevido no menu; status de conclusão do script (#32)

## [0.13.7] - 2026-06-17

### Changed
- Estilo do menu com cabeçalho

## [0.13.6] - 2026-06-17

### Changed
- Lint aplicado a todos os módulos

## [0.13.5] - 2026-06-17

### Removed
- Dependências não utilizadas (`requirements.txt`)

## [0.13.4] - 2026-06-17

### Removed
- Resíduo do módulo `negatividade_de_relatorios`

## [0.13.3] - 2026-06-17

### Added
- Mensagem personalizada ao sair do menu

## [0.13.2] - 2026-06-16

### Added
- Configuração de lint (`pyproject.toml`)

### Changed
- Pequenos ajustes de execução em `auditoria_de_relatorios` e `automacao_de_relatorios`

## [0.13.1] - 2026-06-16

### Removed
- `.DS_Store` versionado por engano

## [0.13.0] - 2026-06-16

### Added
- `config.py`, `download_softskills.py` e `integracao_drive.py` no `automacao_de_softskills` (nova arquitetura)

### Removed
- `download_softskills_fap2026.py` e seus testes antigos

## [0.12.0] - 2026-06-16

### Added
- Menu interativo (`menu.py`) unificando a execução dos módulos

## [0.11.1] - 2026-06-16

### Removed
- Script `negatividade_de_relatorios` (não utilizado)

## [0.11.0] - 2026-06-16

### Changed
- Integração com Google Sheets API para aprovados do bootcamp expandida

## [0.10.1] - 2026-06-16

### Added
- `config.py` e `settings.example.json` para `automacao_de_forum`

### Changed
- `executar.py` do `automacao_de_forum` reescrito

## [0.10.0] - 2026-06-16

### Added
- Módulo `automacao_de_frequencias` com exportação de frequências do Moodle

## [0.9.1] - 2026-06-16

### Changed
- Melhorias no fluxo de postagem do `automacao_de_forum`

## [0.9.0] - 2026-06-15

### Added
- Sistema de configuração via `settings.json`
- Integração com Google Sheets e backup local em `automacao_de_relatorios`

### Removed
- `escopo1.py`, `escopo2.py`, `escopo3.py` e `escopo4.py` antigos de `automacao_de_relatorios`

## [0.8.0] - 2026-06-15

### Added
- Módulo `automacao_de_forum`
- Script de download de softskills do bootcamp FAP 2026

## [0.7.0] - 2026-06-12

### Added
- Novo escopo (`escopo4`) no pipeline de `automacao_de_relatorios`

### Changed
- Escopos 1-3 do pipeline revisados

## [0.6.0] - 2026-06-11

### Added
- Módulo `negatividade_de_relatorios`

### Changed
- Renomeações: `automacao` → `automacao_de_relatorios`, `analise` → `auditoria_de_relatorios`

## [0.5.1] - 2026-06-11

### Changed
- Dependências (`requirements.txt`)

## [0.5.0] - 2026-06-11

### Added
- Pipeline de automação (`automacao/`) com múltiplos escopos de execução

### Changed
- `analise/` reorganizado em pacote; README reescrito

## [0.4.4] - 2026-06-10

### Changed
- Reestruturação de diretórios (`analise/`)

## [0.4.3] - 2026-06-10

### Changed
- Tratamento de entrada do usuário para diretório e caminho de saída

## [0.4.2] - 2026-06-10

### Changed
- Argumentos de diretório de entrada e melhorias na seleção de arquivos

## [0.4.1] - 2026-06-10

### Added
- Seleção de caminho de saída via argumento de linha de comando

## [0.4.0] - 2026-06-10

### Added
- Argumentos de linha de comando para arquivo de entrada e modo de exibição

## [0.3.0] - 2026-06-05

### Added
- Modos de auditoria configuráveis

## [0.2.0] - 2026-06-01

### Added
- Suporte a múltiplos formatos de planilha geral (`analise_negatividade.py`)

### Changed
- Exibição completa de alunos em `pente_fino.py`

## [0.1.5] - 2026-05-28

### Changed
- Atualização do README

## [0.1.4] - 2026-05-28

### Changed
- Atualização do README

## [0.1.3] - 2026-05-28

### Changed
- Autores adicionados ao README

## [0.1.2] - 2026-05-28

### Added
- Licença MIT

## [0.1.1] - 2026-05-28

### Fixed
- E-mail de contato no README

## [0.1.0] - 2026-05-28

### Added
- Lançamento inicial: script de auditoria de relatórios de residentes (`pente_fino.py`)
