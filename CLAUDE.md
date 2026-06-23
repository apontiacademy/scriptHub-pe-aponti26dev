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
- `__init__.py` — exporta `main` ou `ESCOPOS + get_config`
- `__main__.py` — ponto de entrada para `python -m <script>` (usado pelo menu)
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
- **Bloco `if __name__ == "__main__"`**: capturar exceções, chamar `log.erro()` e `sys.exit(1)`
- **CLI (`executar_script`)**: captura exceções das funções ESCOPOS e termina com `typer.Exit(1)`

```python
# ✅ Correto — função de biblioteca
def main(config: Config):
    if not arquivo.exists():
        raise RuntimeError(f"Arquivo não encontrado: {arquivo}")

# ✅ Correto — bloco __main__
if __name__ == "__main__":
    try:
        main(Config.load())
    except Exception as e:
        log.erro(str(e))
        sys.exit(1)

# ❌ Errado — sys.exit dentro de função de biblioteca
def main(config: Config):
    if not arquivo.exists():
        print("❌ Arquivo não encontrado", file=sys.stderr)
        sys.exit(1)
```

## Adicionando um novo script

1. Criar pasta em `src/scripthub/scripts/<nome>/`
2. Arquivos obrigatórios: `__init__.py`, `__main__.py`, `main.py`, `config.py`
3. Seguir o padrão de output (log helpers) e o contrato de erros acima
4. Registrar o comando em `src/scripthub/cli.py`
5. O menu detecta automaticamente novos scripts (via `discover_modules`)

## Comandos úteis

```bash
uv run scripthub --help
uv run scripthub menu
uv run scripthub frequencias --help

# Logs de execução
tail -f logs/scripthub.log
```
