# Snapshots

Registro cumulativo do que já está em `dev`, mas ainda não foi promovido para `nightly` (branch de release candidate) nem virou uma entrada em [CHANGELOG.md](CHANGELOG.md).

`dev` usa squash manual — cada PR vira um único commit linear, sem commit de merge (mesmo mecanismo de `nightly`/`main`, ver "Squash manual em dev/nightly/main" em [CONTRIBUTING.md](CONTRIBUTING.md)). Cada commit em `dev` gera uma nova entrada `x.y.z.devN`, em que:

- `x.y.z` é a versão que está sendo construída — o próximo destino em `nightly`/`main`
- `N` é o número sequencial do snapshot dentro dessa versão (incrementa a cada commit em `dev`)

`pyproject.toml`, em `dev`, é atualizado junto com cada snapshot (`version = "x.y.z.devN"`) — formato PEP 440 (`.devN`), compatível com `uv lock`/`uv sync`.

Quando os snapshots de uma versão são promovidos para `nightly`, as entradas correspondentes saem daqui e viram a seção `[Unreleased]` de `CHANGELOG.md`. Quando `nightly` vira release em `main`, `[Unreleased]` vira `## [x.y.z] - data`.

Commits que só atualizam este arquivo, `CHANGELOG.md` ou a versão em `pyproject.toml` (`chore(changelog)`/`chore(release)`) não geram uma entrada própria — ver "Commits de changelog/release" em [CONTRIBUTING.md](CONTRIBUTING.md).

### 0.21.3.dev1 - 2026-08-02 - (PR#134)

- **Added**: `pytest-bdd` como dependência de dev; `tests/features/` e `tests/functional/` para cenários Gherkin (BDD) e suas step definitions
- **Changed**: suíte de testes pré-existente reorganizada em `tests/{unit,integration}/<domínio>/<script>/`, separando lógica pura/I-O mockado de I/O real de arquivo; marcadores `unit`/`integration` (`uv run pytest -m unit`/`-m integration`) passam a ser aplicados automaticamente por um hook em `conftest.py`; convenção documentada na seção "TDD e testes" de `CONTRIBUTING.md`
- **Changed**: teste de aceite da issue #78 (`test_aceite_perfis_diretorios_keyring.py`, pytest puro com Given/When/Then em docstring) convertido para um cenário `pytest-bdd` real (Gherkin + step definitions)

### 0.21.3.dev2 - 2026-08-02 - (PR#136)

- **Changed**: `pillow` (dependência transitiva via `fpdf2`) atualizado de 12.2.0 para 12.3.0; `pyasn1` (dependência transitiva via `pyasn1-modules`/`google-auth`) atualizado de 0.6.3 para 0.6.4 — vulnerabilidades apontadas pelo Dependabot

### 0.21.3.dev3 - 2026-08-03 - (PR#135)

- **Fixed**: status `AR` (aula realocada) do Moodle passa a ser reconhecido — antes caía em `AU` por padrão e gerava faltas falsas em massa; conta como presença (`PR`) no cálculo de faltas/percentual
- **Fixed**: sessão com pelo menos um registro `AR` é marcada como realocada (coluna com sufixo `**` no cabeçalho e fundo cinza), sem alterar o status individual dos demais alunos na mesma sessão
- **Fixed**: matrícula tardia ("não matriculado") ganha marcador visual próprio (Ø), em vez de reusar o círculo ciano de `JU`, e deixa de ser listada na seção de justificativas da página
- **Fixed**: `LIMITE_FALTAS_MES` corrigido de `> 3` para `>= 3` para o destaque vermelho de "risco"; novo destaque amarelo de "atenção" em exatamente 2 faltas, nunca simultâneo com "risco"
- **Fixed**: cor de alerta da linha (risco/atenção) passa a ter precedência sobre o cinza de sessão realocada, evitando que o cinza mascare um alerta de faltas ativo
- **Fixed**: notas de rodapé `*`/`**` passam a respeitar a ordem em que os símbolos aparecem na tabela e a ficar próximas entre si, sem espaçamento excessivo
