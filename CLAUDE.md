# CLAUDE.md

Guia para desenvolvimento deste projeto com Claude Code.

@CONTRIBUTING.md

Os padrões de estrutura de scripts, fluxo de contribuição (branch/commit/PR), sistema de configuração e testes estão documentados no arquivo acima — leia-o integralmente antes de criar ou alterar qualquer script. Ele é a fonte canônica desses padrões; não os duplique aqui.

Antes de abrir qualquer PR, releia as seções "Fluxo de contribuição" e "Versionamento e changelog" de CONTRIBUTING.md: confirme que o PR é contra `dev` (nunca `nightly`/`main` diretamente) e que a própria branch já inclui a entrada em `SNAPSHOTS.md` e o bump de versão em `pyproject.toml` (`x.y.z.devN`).

## Comandos úteis

```bash
uv run scripthub --help
uv run scripthub menu
uv run scripthub frequencias --help

# Logs de execução
tail -f logs/scripthub.log
```
