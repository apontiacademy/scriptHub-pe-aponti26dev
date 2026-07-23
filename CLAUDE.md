# CLAUDE.md

Guia para desenvolvimento deste projeto com Claude Code.

@CONTRIBUTING.md

Os padrões de estrutura de scripts, fluxo de contribuição (branch/commit/PR), sistema de configuração e testes estão documentados no arquivo acima — leia-o integralmente antes de criar ou alterar qualquer script. Ele é a fonte canônica desses padrões; não os duplique aqui.

Antes de abrir qualquer PR, releia as seções "Fluxo de contribuição" e "Versionamento e changelog" de CONTRIBUTING.md: confirme que o PR é contra `dev` (nunca `nightly`/`main` diretamente). A entrada em `SNAPSHOTS.md` e o bump de versão em `pyproject.toml` (`x.y.z.devN`) **não** entram na abertura da PR — são adicionados depois, como último commit da branch, só após a aprovação e imediatamente antes do squash (ver "Squash manual em dev/nightly/main" em CONTRIBUTING.md).

## Comandos úteis

```bash
uv run scripthub --help
uv run scripthub frequencias --help

# Testes, lint e formatação (ver checklist completo em CONTRIBUTING.md)
uv run pytest                              # suíte completa, cobertura mínima 80%
uv run pytest --no-cov                     # mais rápido para iteração
uv run pytest --no-cov tests/services/     # um módulo específico
uv run pytest --no-cov tests/services/test_log.py::test_ok   # um teste específico
uv run ruff check .
uv run ruff format --check .

# Logs de execução
tail -f logs/scripthub.log
```
