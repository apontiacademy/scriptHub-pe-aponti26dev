# ScriptHub — Aponti PE

Hub de automações para operações do bootcamp Aponti PE. Cada módulo resolve um problema específico do dia a dia com o Moodle e o Google Workspace.

## Instalação

Requer Python 3.12+ e [`uv`](https://docs.astral.sh/uv/). O projeto depende de um pacote privado da organização resolvido via `[tool.uv.sources]`, por isso `pip` não é suportado diretamente.

```bash
git clone git@github.com:apontiacademy/scriptHub-pe-aponti26dev.git
cd scriptHub-pe-aponti26dev
uv sync

# Configure as opções de cada script (veja a seção Configuração abaixo)
uv run scripthub config

# Para ver todos os comandos disponíveis:
uv run scripthub --help
```

Após o `uv sync`, também é possível ativar o ambiente virtual e invocar os comandos sem o prefixo `uv run`:

```bash
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
scripthub config
```

## Uso

```bash
# Invocar um script diretamente
uv run scripthub frequencias
uv run scripthub relatorios auditar
uv run scripthub relatorios compilar
uv run scripthub softskills
uv run scripthub torpedo

# Menu interativo (depreciado — prefira os comandos acima)
uv run scripthub menu
```

Para ver a ajuda e os aliases disponíveis:

```bash
uv run scripthub --help      # ou: scripthub -h
uv run scripthub --aliases   # ou: scripthub -a
```

## Comandos

| Comando | Alias | Descrição |
|---|---|---|
| `scripthub menu` | `m` | **Depreciado.** Menu interativo — prefira usar os comandos da CLI diretamente |
| `scripthub frequencias [-p passo]` | `f` | Exporta frequências de presença do Moodle para o Google Sheets |
| `scripthub relatorios auditar [-p passo]` | `r auditar` | Pipeline completo: download → análise → Google Sheets → backup |
| `scripthub relatorios compilar` | `r compilar` | Compila relatórios em PDF |
| `scripthub softskills` | `s` | Baixa notas de soft skills do Moodle e envia ao Google Drive |
| `scripthub torpedo` | `t` | Posta tópicos em fóruns do Moodle a partir de arquivos Markdown |
| `scripthub config` | `c` | Configura interativamente as opções de um script |

A opção `-p N` executa apenas o passo N do pipeline (começando em 1) em vez do pipeline completo. Disponível nos comandos `frequencias` e `relatorios auditar`.

## Configuração

Cada script tem suas próprias opções configuráveis (URLs do Moodle, credenciais, IDs de planilhas, etc.). Use o comando `config` para inspecionar e editar essas opções interativamente:

```bash
# Selecionar script interativamente e editar opções
uv run scripthub config

# Ir direto para as opções de um script específico
uv run scripthub config -s auditar_frequencias

# Apenas visualizar o estado atual das opções (sem editar)
uv run scripthub config --opcoes
uv run scripthub config -o -s torpedo_de_forum
```

O comando exibe cada opção com um ícone de status:

- ✅ Preenchida e válida — valor atual é exibido em resumo
- ❌ Ausente ou inválida — motivo do erro é exibido
- ⚪ Opcional e não preenchida

No modo de edição, selecione quais opções modificar (estilo `gh` CLI) e preencha os valores. Inputs são adaptados ao tipo do campo: texto, senha (oculta), URL, caminho, booleano, inteiro, listas de URLs e dicionários (com sub-menus de adicionar/editar/remover).

As configurações são persistidas em dois arquivos dentro de cada módulo:

- `.env` — credenciais (`MOODLE_USUARIO`, `MOODLE_SENHA`)
- `settings.json` — demais parâmetros

Se um script for executado sem as opções obrigatórias preenchidas, a CLI indica o comando exato para corrigi-las.

## Colaboradores

- **Leandro Carvalho** — [LinkedIn](https://www.linkedin.com/in/leandro-c-s/)
- **Caio Tenório** — [LinkedIn](https://www.linkedin.com/in/caiomatenorio/)
- **Ruan Rickelme Ramos** — [LinkedIn](https://www.linkedin.com/in/ruanrickelmeramos/?locale=pt)
