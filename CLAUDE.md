# CLAUDE.md

Guia para desenvolvimento deste projeto com Claude Code.

## Estrutura do projeto

```
src/scripthub/
├── cli.py                  # Ponto de entrada: comandos Typer
├── _i18n.py                # Traduções pt-BR para Typer/Click
├── scripts/                # Módulos de automação (um por pasta)
│   ├── auditar_frequencias/
│   ├── auditar_relatorios/
│   ├── auditar_softskills/
│   ├── compilacao_de_relatorios/
│   └── torpedo_de_forum/
└── services/
    ├── config/             # Configuração interativa (scripthub config)
    ├── log.py              # Helpers de output unificados
    └── menu/               # Menu interativo (scripthub menu)
```

Cada pacote de script contém:
- `__init__.py` — declara `MENU_CMD` e exporta `main` ou `ESCOPOS + get_config`
- `main.py` — orquestração do pipeline
- `config.py` — dataclass de configuração
- demais módulos de implementação

## Padrão de output dos scripts

Todos os scripts devem usar os helpers de `scripthub.services.log`:

```python
from scripthub.services import log
```

| Helper | Quando usar | Saída |
|---|---|---|
| `log.secao("TÍTULO")` | Início de uma etapa principal | `\n===...===\n▶ TÍTULO\n===...===` |
| `log.passo("msg")` | Passo em andamento | `  • msg` |
| `log.ok("msg")` | Conclusão bem-sucedida | `  ✔ msg` |
| `log.erro("msg")` | Erro (vai para stderr) | `  ❌ msg` |
| `log.aviso("msg")` | Aviso não-fatal | `  ⚠️  msg` |

**Nunca use `print()` diretamente nos scripts.**

Todo output é persistido automaticamente em `logs/scripthub.log` (ignorado pelo git).

## Contrato de erros

- **Funções de biblioteca**: levantar exceções (`ValueError`, `RuntimeError`, `FileNotFoundError`, etc.) — nunca chamar `sys.exit()`
- **CLI (`executar_script`)**: captura exceções das funções ESCOPOS e termina com `typer.Exit(1)`
- **Menu**: invoca o CLI via subprocess (`scripthub <cmd>`), o exit code do processo é exibido ao final

```python
# ✅ Correto — função de biblioteca
def main(config: Config):
    if not arquivo.exists():
        raise RuntimeError(f"Arquivo não encontrado: {arquivo}")

# ❌ Errado — sys.exit dentro de função de biblioteca
def main(config: Config):
    if not arquivo.exists():
        print("❌ Arquivo não encontrado", file=sys.stderr)
        sys.exit(1)
```

## Adicionando um novo script

1. Criar pasta em `src/scripthub/scripts/<nome>/`
2. Arquivos obrigatórios: `__init__.py`, `main.py`, `config.py`
3. Declarar `MENU_CMD = ("comando",)` no `__init__.py` (o menu usa isso para invocar o script via CLI)
4. Seguir o padrão de output (log helpers) e o contrato de erros acima
5. Registrar o comando em `src/scripthub/cli.py`
6. O menu detecta automaticamente novos scripts que tenham `MENU_CMD` no `__init__.py`

## Comandos úteis

```bash
uv run scripthub --help
uv run scripthub menu
uv run scripthub frequencias --help

# Logs de execução
tail -f logs/scripthub.log
```
