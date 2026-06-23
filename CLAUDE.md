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

Cada pacote de script segue um dos dois padrões:

**Padrão A — pipeline por escopos** (`auditar_frequencias`, `auditar_relatorios`):
- `__init__.py` — declara `MENU_CMD`, exporta `ESCOPOS` e `get_config`
- `ESCOPOS`: lista de tuplas `(nome_do_passo: str, funcao: Callable[[Config], None])`
- `get_config()`: retorna a dataclass de configuração (carrega `.env` + `settings.json`)
- O CLI usa `executar_script()` para iterar os escopos com log por passo e captura de exceção

**Padrão B — função main** (`auditar_softskills`, `compilacao_de_relatorios`, `torpedo_de_forum`) — **DEPRECIADO**:
- `__init__.py` — declara `MENU_CMD`, exporta apenas `main`
- `main()` carrega configuração internamente e executa o pipeline diretamente
- Não crie novos scripts com este padrão. Os existentes devem ser migrados para o Padrão A o quanto antes.

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
3. No `__init__.py`, declarar `MENU_CMD` e exportar `ESCOPOS` + `get_config` (Padrão A):

```python
MENU_CMD = ("meu_script",)
from .main import ESCOPOS
from .config import get_config
```

4. Em `main.py`, definir `ESCOPOS` como lista de tuplas `(nome, função)`:

```python
ESCOPOS = [
    ("Baixar dados", baixar_dados),
    ("Processar", processar),
]

def baixar_dados(config: Config): ...
def processar(config: Config): ...
```

5. Adicionar campos configuráveis em `services/config/esquemas.py` (ver seção "Sistema de configuração" abaixo)
6. Seguir o padrão de output (log helpers) e o contrato de erros acima
7. Registrar o comando em `src/scripthub/cli.py`
8. O menu detecta automaticamente novos scripts que tenham `MENU_CMD` no `__init__.py`

## Sistema de configuração

Os campos configuráveis de cada script são declarados em `services/config/esquemas.py` como entradas do dict `ESQUEMAS`, usando a dataclass `Campo` de `services/config/campo.py`.

```python
# services/config/esquemas.py
ESQUEMAS: dict[str, list[Campo]] = {
    "nome_do_modulo": [
        Campo(
            chave="moodle_usuario",
            rotulo="Usuário do Moodle",
            tipo="texto",
            origem="env",           # "env" → .env  |  "settings" → settings.json
            env_var="MOODLE_USUARIO",
        ),
        Campo(
            chave="moodle_url_login",
            rotulo="URL de login",
            tipo="url",
            origem="settings",
            json_chaves=["moodle", "urlLogin"],   # caminho de acesso no JSON
            obrigatorio=True,
        ),
    ],
}
```

Tipos de campo disponíveis:

| Tipo | Descrição |
|---|---|
| `texto` | String simples |
| `senha` | String mascarada na exibição |
| `url` | URL validada por regex |
| `caminho` | Caminho de arquivo ou diretório |
| `bool` | Booleano (sim/não interativo) |
| `int` | Inteiro |
| `lista_url` | Lista de URLs |
| `dict_str_url` | Dict `{str: url}` |
| `dict_str_lista_url` | Dict `{str: [url, ...]}` |

Use `depende_de="chave_outro_campo"` para tornar um campo condicional ao valor de outro campo booleano.

## Comandos úteis

```bash
uv run scripthub --help
uv run scripthub menu
uv run scripthub frequencias --help

# Logs de execução
tail -f logs/scripthub.log
```
